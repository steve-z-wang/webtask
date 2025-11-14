"""Worker role - executes one subtask with conversation-based LLM."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from webtask.llm import (
    Message,
    SystemMessage,
    UserMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
    ImageMimeType,
    ToolResult,
    ToolResultStatus,
)
from webtask._internal.llm import MessagePurger
from webtask.llm.message import ToolCall
from ..tool import ToolRegistry
from ...prompts.worker_prompt import build_worker_prompt
from webtask._internal.utils.wait import wait
from .worker_browser import WorkerBrowser
from .worker_session import WorkerSession, WorkerEndReason
from .tools.navigate import NavigateTool
from .tools.click import ClickTool
from .tools.fill import FillTool
from .tools.type import TypeTool
from .tools.upload import UploadTool
from .tools.wait import WaitTool
from .tools.complete_work import CompleteWorkTool
from .tools.abort_work import AbortWorkTool
from .tools.observe import ObserveTool
from .tools.think import ThinkTool

if TYPE_CHECKING:
    from ..agent_browser import AgentBrowser
    from webtask.llm.llm import LLM


class Worker:
    """Worker role - executes one subtask with conversation-based LLM."""

    # Small delay after each action to prevent race conditions
    ACTION_DELAY = 0.1

    def __init__(
        self,
        llm: "LLM",
        agent_browser: "AgentBrowser",
    ):
        self._llm = llm
        self.worker_browser = WorkerBrowser(agent_browser)
        self._tool_registry = ToolRegistry()

        # Register all tools with dependencies (except upload which needs resources)
        self._tool_registry.register(NavigateTool(self.worker_browser))
        self._tool_registry.register(ClickTool(self.worker_browser))
        self._tool_registry.register(FillTool(self.worker_browser))
        self._tool_registry.register(TypeTool(self.worker_browser))
        self._tool_registry.register(WaitTool())
        self._tool_registry.register(ObserveTool())

        # Create message purger to keep context bounded
        self._message_purger = MessagePurger(
            purge_tags=["observation"],
            message_types=[ToolResultMessage, UserMessage],
            keep_last_messages=2,
        )
        self._tool_registry.register(ThinkTool())
        self._tool_registry.register(CompleteWorkTool())
        self._tool_registry.register(AbortWorkTool())

    async def _execute_tool_calls(
        self, tool_calls: List[ToolCall]
    ) -> Tuple[List[ToolResult], Optional[WorkerEndReason]]:
        """Execute all tool calls and return results.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            Tuple of (tool_results, end_reason)
            - end_reason is WorkerEndReason enum or None if not finished
        """
        results = []

        for tool_call in tool_calls:
            # Execute using registry
            tool_result = await self._tool_registry.execute_tool_call(tool_call)
            results.append(tool_result)

            # Return immediately if complete_work or abort_work (only on success)
            if tool_result.status == ToolResultStatus.SUCCESS:
                tool = self._tool_registry.get(tool_call.name)
                if isinstance(tool, CompleteWorkTool):
                    return results, WorkerEndReason.COMPLETE_WORK
                elif isinstance(tool, AbortWorkTool):
                    return results, WorkerEndReason.ABORT_WORK

        return results, None

    async def run(
        self,
        task_description: str,
        max_steps: int,
        resources: Optional[Dict[str, str]] = None,
        previous_session: Optional[WorkerSession] = None,
        verifier_feedback: Optional[str] = None,
    ) -> WorkerSession:
        """Execute task with optional continuation from previous session.

        Args:
            task_description: Task to execute
            max_steps: Maximum number of steps
            resources: Optional file resources for upload
            previous_session: Previous worker session to continue from
            verifier_feedback: Feedback from verifier (requires previous_session)
        """
        if previous_session is not None:
            # Continue from previous session with verifier feedback
            messages = previous_session.messages.copy()
            if verifier_feedback:
                messages.append(
                    UserMessage(
                        content=[
                            TextContent(text=f"Verifier feedback: {verifier_feedback}")
                        ]
                    )
                )
            return await self._run(
                previous_session.task_description,
                max_steps,
                resources=None,  # Resources already registered in first run()
                messages=messages,
            )
        else:
            # Start fresh
            # Capture initial page state
            dom_snapshot = await self.worker_browser.get_dom_snapshot()
            screenshot_b64 = await self.worker_browser.get_screenshot()

            messages = [
                SystemMessage(content=[TextContent(text=build_worker_prompt())]),
                UserMessage(
                    content=[
                        TextContent(text=f"Task: {task_description}"),
                        TextContent(text=dom_snapshot, tag="observation"),
                        ImageContent(
                            data=screenshot_b64,
                            mime_type=ImageMimeType.PNG,
                            tag="observation",
                        ),
                    ]
                ),
            ]
            return await self._run(task_description, max_steps, resources, messages)

    async def _run(
        self,
        task_description: str,
        max_steps: int,
        resources: Optional[Dict[str, str]],
        messages: List[Message],
    ) -> WorkerSession:
        """Shared implementation for both run methods."""
        start_time = datetime.now()

        # Register upload tool with resources for this task
        if resources:
            self._tool_registry.register(UploadTool(self.worker_browser, resources))

        # Main execution loop
        for step in range(max_steps):
            # Purge old observations from message history
            messages = self._message_purger.purge(messages)

            # Call LLM with conversation history and tools
            assistant_msg = await self._llm.call_tools(
                messages=messages,
                tools=self._tool_registry.get_all(),
            )
            messages.append(assistant_msg)

            # LLM must return tool calls
            if not assistant_msg.tool_calls:
                raise ValueError("LLM did not return any tool calls")

            # Execute all tool calls and collect results
            tool_results, end_reason = await self._execute_tool_calls(
                assistant_msg.tool_calls
            )

            # Wait after all actions complete
            await wait(self.ACTION_DELAY)

            # Capture page state once after all tool executions
            dom_snapshot = await self.worker_browser.get_dom_snapshot()
            screenshot_b64 = await self.worker_browser.get_screenshot()

            # Create tool result message with acknowledgments + observation content
            content = [
                TextContent(text=dom_snapshot, tag="observation"),
                ImageContent(
                    data=screenshot_b64, mime_type=ImageMimeType.PNG, tag="observation"
                ),
            ]

            result_message = ToolResultMessage(
                results=tool_results,
                content=content,
            )
            messages.append(result_message)

            # Check if finished and return immediately
            if end_reason:
                return WorkerSession(
                    task_description=task_description,
                    start_time=start_time,
                    end_time=datetime.now(),
                    max_steps=max_steps,
                    steps_used=step + 1,
                    end_reason=end_reason,
                    messages=messages,
                    final_dom=dom_snapshot,
                    final_screenshot=screenshot_b64,
                )

        # Max steps reached - capture final state
        final_dom = await self.worker_browser.get_dom_snapshot()
        final_screenshot = await self.worker_browser.get_screenshot()

        return WorkerSession(
            task_description=task_description,
            start_time=start_time,
            end_time=datetime.now(),
            max_steps=max_steps,
            steps_used=max_steps,
            end_reason=WorkerEndReason.MAX_STEPS,
            messages=messages,
            final_dom=final_dom,
            final_screenshot=final_screenshot,
        )
