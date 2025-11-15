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
from webtask._internal.llm import purge_messages_content
from webtask.llm.message import ToolCall
from ..tool import ToolRegistry
from ...prompts.worker_prompt import build_worker_prompt
from ...utils.logger import get_logger
from .worker_browser import WorkerBrowser
from .worker_session import WorkerSession, WorkerEndReason
from .action_tracker import ActionTracker
from .tools import (
    NavigateTool,
    ClickTool,
    FillTool,
    TypeTool,
    UploadTool,
    WaitTool,
    CompleteWorkTool,
    AbortWorkTool,
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
        wait_after_action: float,
        resources: Optional[Dict[str, str]] = None,
    ):
        self._llm = llm
        self.worker_browser = WorkerBrowser(
            session_browser, wait_after_action=wait_after_action
        )
        self._tool_registry = ToolRegistry()
        self._logger = get_logger(__name__)

        self._tool_registry.register(WaitTool())
        self._tool_registry.register(ClickTool(self.worker_browser))
        self._tool_registry.register(FillTool(self.worker_browser))
        self._tool_registry.register(TypeTool(self.worker_browser))
        self._tool_registry.register(NavigateTool(self.worker_browser))
        self._tool_registry.register(UploadTool(self.worker_browser, resources))

        self._tool_registry.register(CompleteWorkTool())
        self._tool_registry.register(AbortWorkTool())

    async def _execute_tool_calls(
        self, tool_calls: List[ToolCall], action_tracker: ActionTracker
    ) -> Tuple[List[ToolResult], Optional[WorkerEndReason]]:
        results = []

        for tool_call in tool_calls:
            tool = self._tool_registry.get(tool_call.name)
            params = tool.Params(**tool_call.arguments)
            description = tool.describe(params)

            self._logger.info(f"Executing: {description}")

            tool_result = await self._tool_registry.execute_tool_call(tool_call)
            results.append(tool_result)

            if tool_result.status == ToolResultStatus.ERROR:
                self._logger.error(f"Tool error: {tool_result.error}")

            action_tracker.add_action(
                description=description,
                status=tool_result.status.value,
                error=(
                    tool_result.error
                    if tool_result.status == ToolResultStatus.ERROR
                    else None
                ),
            )

            if tool_result.status == ToolResultStatus.SUCCESS:
                tool = self._tool_registry.get(tool_call.name)
                if isinstance(tool, CompleteWorkTool):
                    return results, WorkerEndReason.COMPLETE_WORK
                elif isinstance(tool, AbortWorkTool):
                    return results, WorkerEndReason.ABORT_WORK

        return results, None
    
   
    def compact_messages(
        self,
        messages: List[Message]
    ) -> List[Message]:
        
    

    async def _run_step(
        self,
        step: int,
        messages: List[Message],
        action_tracker: ActionTracker,
    ) -> Tuple[List[Message], Optional[WorkerEndReason], str, str]:
        self._logger.info(f"Step {step + 1} - Start")

        messages = purge_messages_content(
            messages,
            by_tags=["dom_snapshot"],
            message_types=[ToolResultMessage, UserMessage],
            keep_last_messages=1,
        )
        messages = purge_messages_content(
            messages,
            by_tags=["screenshot"],
            message_types=[ToolResultMessage, UserMessage],
            keep_last_messages=2,
        )

        self._logger.debug("Sending LLM request...")
        assistant_msg = await self._llm.call_tools(
            messages=messages,
            tools=self._tool_registry.get_all(),
        )
        messages.append(assistant_msg)

        if not assistant_msg.tool_calls:
            raise ValueError("LLM did not return any tool calls")

        tool_names = [tc.name for tc in assistant_msg.tool_calls]
        self._logger.info(f"Received LLM response - Tools: {tool_names}")

        if assistant_msg.content:
            for content in assistant_msg.content:
                if hasattr(content, "text") and content.text:
                    self._logger.info(f"Reasoning: {content.text}")

        tool_results, end_reason = await self._execute_tool_calls(
            assistant_msg.tool_calls, action_tracker
        )

        dom_snapshot = await self.worker_browser.get_dom_snapshot()
        screenshot_b64 = await self.worker_browser.get_screenshot()
        messages.append(
            ToolResultMessage(
                results=tool_results,
                content=[
                    TextContent(text=dom_snapshot, tag="dom_snapshot"),
                    ImageContent(
                        data=screenshot_b64,
                        mime_type=ImageMimeType.PNG,
                        tag="screenshot",
                    ),
                ],
            )
        )

        self._logger.info(f"Step {step + 1} - End")

        return messages, end_reason, dom_snapshot, screenshot_b64

    async def _run(
        self,
        task_description: str,
        max_steps: int,
        messages: List[Message],
    ) -> WorkerSession:
        self._logger.info(f"Worker session start - Task: {task_description}")

        action_tracker = ActionTracker()
        start_time = datetime.now()

        for step in range(max_steps):
            messages, end_reason, dom_snapshot, screenshot_b64 = await self._run_step(
                step, messages, action_tracker
            )

            if end_reason:
                self._logger.info(f"Worker session end - Reason: {end_reason.value}")
                steps_used = step + 1
                break
        else:
            self._logger.info("Worker session end - Reason: max_steps_reached")
            end_reason = WorkerEndReason.MAX_STEPS
            steps_used = max_steps

        return WorkerSession(
            task_description=task_description,
            start_time=start_time,
            end_time=datetime.now(),
            max_steps=max_steps,
            steps_used=steps_used,
            end_reason=end_reason,
            messages=messages,
            action_summary=action_tracker.get_summary_text(),
            final_dom=dom_snapshot,
            final_screenshot=screenshot_b64,
        )

    async def run(
        self,
        task_description: str,
        max_steps: int,
        previous_session: Optional[WorkerSession] = None,
        verifier_feedback: Optional[str] = None,
    ) -> WorkerSession:
        if previous_session is not None:
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
                previous_session.task_description, max_steps, messages=messages
            )
        else:
            dom_snapshot = await self.worker_browser.get_dom_snapshot()
            screenshot_b64 = await self.worker_browser.get_screenshot()

            messages = [
                SystemMessage(content=[TextContent(text=build_worker_prompt())]),
                UserMessage(
                    content=[
                        TextContent(text=f"Task: {task_description}"),
                        TextContent(text=dom_snapshot, tag="dom_snapshot"),
                        ImageContent(
                            data=screenshot_b64,
                            mime_type=ImageMimeType.PNG,
                            tag="screenshot",
                        ),
                    ]
                ),
            ]
            return await self._run(task_description, max_steps, messages)
