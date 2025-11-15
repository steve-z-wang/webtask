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
from ...utils.logger import get_logger
from .worker_browser import WorkerBrowser
from .worker_session import WorkerSession, WorkerEndReason
from .tools import (
    NavigateTool,
    ClickTool,
    FillTool,
    TypeTool,
    UploadTool,
    WaitTool,
    CompleteWorkTool,
    AbortWorkTool,
    NoteThoughtTool,
)

if TYPE_CHECKING:
    from ..session_browser import SessionBrowser
    from webtask.llm.llm import LLM


class Worker:
    """Worker role - executes one subtask with conversation-based LLM."""

    def __init__(
        self,
        llm: "LLM",
        session_browser: "SessionBrowser",
        action_delay: float = 0.1,
    ):
        self._llm = llm
        self.worker_browser = WorkerBrowser(session_browser, action_delay=action_delay)
        self._tool_registry = ToolRegistry()
        self._logger = get_logger(__name__)

        # Register all tools with dependencies (except upload which needs resources)
        self._tool_registry.register(WaitTool())
        self._tool_registry.register(NoteThoughtTool())
        self._tool_registry.register(ClickTool(self.worker_browser))
        self._tool_registry.register(FillTool(self.worker_browser))
        self._tool_registry.register(TypeTool(self.worker_browser))
        self._tool_registry.register(NavigateTool(self.worker_browser))

        # Create message purger to keep context bounded
        self._message_purger = MessagePurger(
            purge_tags=["observation"],
            message_types=[ToolResultMessage, UserMessage],
            keep_last_messages=2,
        )
        self._tool_registry.register(CompleteWorkTool())
        self._tool_registry.register(AbortWorkTool())

    async def _execute_tool_calls(
        self, tool_calls: List[ToolCall]
    ) -> Tuple[List[ToolResult], Optional[WorkerEndReason], List[Dict]]:
        """Execute all tool calls and return results.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            Tuple of (tool_results, end_reason, actions)
            - tool_results: List of tool execution results
            - end_reason: WorkerEndReason enum or None if not finished
            - actions: List of action records (description + status)
        """
        results = []
        actions = []

        for tool_call in tool_calls:
            # Get tool and generate description
            tool = self._tool_registry.get(tool_call.name)
            params = tool.Params(**tool_call.arguments)
            description = tool.describe(params)

            # Log tool execution
            self._logger.info(f"Executing: {description}")

            # Execute using registry
            tool_result = await self._tool_registry.execute_tool_call(tool_call)
            results.append(tool_result)

            # Log errors if any
            if tool_result.status == ToolResultStatus.ERROR:
                self._logger.error(f"Tool error: {tool_result.error}")

            # Record action (skip meta tools like note_thought, complete_work, abort_work)
            if tool_call.name not in ["note_thought", "complete_work", "abort_work"]:
                action_record = {
                    "description": description,
                    "status": tool_result.status.value,
                }
                if tool_result.status == ToolResultStatus.ERROR:
                    action_record["error"] = tool_result.error
                actions.append(action_record)

            # Return immediately if complete_work or abort_work (only on success)
            if tool_result.status == ToolResultStatus.SUCCESS:
                tool = self._tool_registry.get(tool_call.name)
                if isinstance(tool, CompleteWorkTool):
                    return results, WorkerEndReason.COMPLETE_WORK, actions
                elif isinstance(tool, AbortWorkTool):
                    return results, WorkerEndReason.ABORT_WORK, actions

        return results, None, actions

    async def _run_step(
        self,
        step: int,
        messages: List[Message],
    ) -> Tuple[List[Message], Optional[WorkerEndReason], List[Dict], str, str]:
        """Execute one step and return updated state.

        Args:
            step: Current step number (0-indexed)
            messages: Current message history

        Returns:
            Tuple of (messages, end_reason, step_actions, dom_snapshot, screenshot_b64)
        """
        self._logger.info(f"Step {step + 1} - Start")

        # Purge old observations from message history
        messages = self._message_purger.purge(messages)

        # Call LLM with conversation history and tools
        self._logger.debug("Sending LLM request...")
        assistant_msg = await self._llm.call_tools(
            messages=messages,
            tools=self._tool_registry.get_all(),
        )
        messages.append(assistant_msg)

        # LLM must return tool calls
        if not assistant_msg.tool_calls:
            raise ValueError("LLM did not return any tool calls")

        # Log response
        tool_names = [tc.name for tc in assistant_msg.tool_calls]
        self._logger.info(f"Received LLM response - Tools: {tool_names}")

        # Execute all tool calls and collect results
        tool_results, end_reason, step_actions = await self._execute_tool_calls(
            assistant_msg.tool_calls
        )

        # Append tool result message with page state
        dom_snapshot = await self.worker_browser.get_dom_snapshot()
        screenshot_b64 = await self.worker_browser.get_screenshot()
        messages.append(
            ToolResultMessage(
                results=tool_results,
                content=[
                    TextContent(text=dom_snapshot, tag="observation"),
                    ImageContent(
                        data=screenshot_b64,
                        mime_type=ImageMimeType.PNG,
                        tag="observation",
                    ),
                ],
            )
        )

        self._logger.info(f"Step {step + 1} - End")

        return messages, end_reason, step_actions, dom_snapshot, screenshot_b64

    async def _run(
        self,
        task_description: str,
        max_steps: int,
        resources: Optional[Dict[str, str]],
        messages: List[Message],
    ) -> WorkerSession:
        """Shared implementation for both run methods."""

        self._logger.info(f"Worker session start - Task: {task_description}")

        # Register upload tool with resources for this task
        if resources:
            self._tool_registry.register(UploadTool(self.worker_browser, resources))

        start_time = datetime.now()
        action_log = []  # Track all actions across steps

        # Main execution loop
        for step in range(max_steps):
            # Execute one step
            messages, end_reason, step_actions, dom_snapshot, screenshot_b64 = (
                await self._run_step(step, messages)
            )

            # Append actions from this step to overall action log
            action_log.extend(step_actions)

            # Check if finished and break
            if end_reason:
                self._logger.info(f"Worker session end - Reason: {end_reason.value}")
                steps_used = step + 1
                break
        else:
            # Max steps reached - capture final state
            self._logger.info("Worker session end - Reason: max_steps_reached")
            end_reason = WorkerEndReason.MAX_STEPS
            steps_used = max_steps

        # Create and return WorkerSession
        return WorkerSession(
            task_description=task_description,
            start_time=start_time,
            end_time=datetime.now(),
            max_steps=max_steps,
            steps_used=steps_used,
            end_reason=end_reason,
            messages=messages,
            actions=action_log,
            final_dom=dom_snapshot,
            final_screenshot=screenshot_b64,
        )

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
