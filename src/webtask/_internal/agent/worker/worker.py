"""Worker role - executes one subtask with conversation-based LLM."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING, Any
from webtask.llm import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
    ImageMimeType,
)
from webtask._internal.llm import purge_messages_content
from ..tool import ToolRegistry
from ...prompts.worker_prompt import build_worker_prompt
from ...utils.logger import get_logger
from .worker_browser import WorkerBrowser
from .worker_session import WorkerSession, WorkerStatus
from .tools import (
    NavigateTool,
    ClickTool,
    FillTool,
    TypeTool,
    UploadTool,
    WaitTool,
    SetOutputTool,
    CompleteWorkTool,
    AbortWorkTool,
)

if TYPE_CHECKING:
    from webtask.browser import Context
    from webtask.llm.llm import LLM


class EndReason:
    """Wrapper to track if worker execution should end."""

    def __init__(self):
        self.value: Optional[WorkerStatus] = None


class OutputStorage:
    """Wrapper to store structured output data."""

    def __init__(self):
        self.value: Optional[Any] = None


@dataclass
class ToolCallPair:
    """Pair of assistant message and tool result message from one execution step.

    This is the single source of truth for a step's execution, containing:
    - The assistant's tool calls
    - The results of executing those tools
    - Human-readable descriptions of the actions taken
    - The assistant's reasoning/thoughts before taking actions
    """

    assistant_msg: AssistantMessage
    tool_result_msg: ToolResultMessage
    descriptions: List[str]  # Action descriptions for summary generation
    reasoning: Optional[str] = None  # LLM's thoughts/reasoning before actions


class Worker:
    """Worker role - executes one subtask with conversation-based LLM."""

    def __init__(
        self,
        llm: "LLM",
        context: "Context",
        wait_after_action: float,
        resources: Optional[Dict[str, str]] = None,
        mode: str = "accessibility",
    ):
        self._llm = llm
        self._mode = mode
        self.worker_browser = WorkerBrowser(
            context=context, wait_after_action=wait_after_action
        )
        self._tool_registry = ToolRegistry()
        self._logger = get_logger(__name__)

        # Register normal tools (non-terminal)
        self._tool_registry.register(WaitTool())
        self._tool_registry.register(ClickTool(self.worker_browser))
        self._tool_registry.register(FillTool(self.worker_browser))
        self._tool_registry.register(TypeTool(self.worker_browser))
        self._tool_registry.register(NavigateTool(self.worker_browser))
        self._tool_registry.register(UploadTool(self.worker_browser, resources))

        # Control tools registered per-run in _run() with fresh EndReason context

    def _build_summary(self, pairs: List[ToolCallPair]) -> str:
        """Build summary text from pairs, including reasoning and actions."""
        if not pairs:
            return ""

        lines = []
        for step_num, pair in enumerate(pairs, 1):
            lines.append(f"\nStep {step_num}:")

            # Add reasoning if present
            if pair.reasoning:
                # Indent reasoning for readability
                reasoning_lines = pair.reasoning.strip().split("\n")
                lines.append("  Reasoning:")
                for reasoning_line in reasoning_lines:
                    lines.append(f"    {reasoning_line}")

            # Add actions
            if pair.descriptions:
                lines.append("  Actions:")
                for description in pair.descriptions:
                    lines.append(f"    - {description}")

        return "\n".join(lines)

    def _pairs_to_messages(
        self,
        pairs: List[ToolCallPair],
        keep_last_n_pairs: int = 5,
    ) -> List[Message]:
        """Convert pairs to messages with optional compacting."""
        if len(pairs) <= keep_last_n_pairs:
            # Just return all messages
            messages = []
            for pair in pairs:
                messages.append(pair.assistant_msg)
                messages.append(pair.tool_result_msg)
            return messages

        # Build summary from old pairs
        old_pairs = pairs[:-keep_last_n_pairs]
        summary = self._build_summary(old_pairs)

        messages = []
        if summary:
            messages.append(
                UserMessage(
                    content=[
                        TextContent(
                            text=f"Previous actions in this session:\n{summary}"
                        )
                    ]
                )
            )

        # Add recent pairs
        for pair in pairs[-keep_last_n_pairs:]:
            messages.append(pair.assistant_msg)
            messages.append(pair.tool_result_msg)

        return messages

    async def _run_step(
        self,
        step: int,
        session_start_messages: List[Message],
        pairs: List[ToolCallPair],
    ) -> Tuple[ToolCallPair, str, str]:
        """Run one step and return new ToolCallPair."""
        self._logger.info(f"Step {step + 1} - Start")

        # Convert pairs to messages (with compacting if needed)
        tool_messages = self._pairs_to_messages(pairs)

        # Combine session start + tool messages
        all_messages = session_start_messages + tool_messages

        # Purge old content
        all_messages = purge_messages_content(
            all_messages,
            by_tags=["dom_snapshot"],
            message_types=[ToolResultMessage, UserMessage],
            keep_last_messages=1,
        )
        all_messages = purge_messages_content(
            all_messages,
            by_tags=["screenshot"],
            message_types=[ToolResultMessage, UserMessage],
            keep_last_messages=2,
        )

        # Call LLM
        self._logger.debug("Sending LLM request...")
        assistant_msg = await self._llm.call_tools(
            messages=all_messages,
            tools=self._tool_registry.get_all(),
        )

        if not assistant_msg.tool_calls:
            self._logger.warning(
                "LLM did not return any tool calls - creating empty result"
            )
            tool_results = []
            descriptions = []
        else:
            tool_names = [tc.name for tc in assistant_msg.tool_calls]
            self._logger.info(f"Received LLM response - Tools: {tool_names}")

            if assistant_msg.content:
                for content in assistant_msg.content:
                    if hasattr(content, "text") and content.text:
                        self._logger.info(f"Reasoning: {content.text}")

            # Execute tools using registry (control tools modify end_reason wrapper directly)
            tool_results, descriptions = await self._tool_registry.execute_tool_calls(
                assistant_msg.tool_calls
            )

        # Extract reasoning from assistant message
        reasoning = None
        if assistant_msg.content:
            for content in assistant_msg.content:
                if hasattr(content, "text") and content.text:
                    reasoning = content.text
                    break

        # Get current page state
        dom_snapshot = await self.worker_browser.get_dom_snapshot(mode=self._mode)
        screenshot_b64 = await self.worker_browser.get_screenshot()

        # Create tool result message
        tool_result_msg = ToolResultMessage(
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

        # Create ToolCallPair
        pair = ToolCallPair(
            assistant_msg=assistant_msg,
            tool_result_msg=tool_result_msg,
            descriptions=descriptions,
            reasoning=reasoning,
        )

        self._logger.info(f"Step {step + 1} - End")

        return pair, dom_snapshot, screenshot_b64

    async def _run(
        self,
        task_description: str,
        max_steps: int,
        session_start_messages: List[Message],
        previous_pairs: Optional[List[ToolCallPair]] = None,
    ) -> WorkerSession:
        """Execute worker session with ToolCallPair tracking."""
        self._logger.info(f"Worker session start - Task: {task_description}")

        pairs: List[ToolCallPair] = previous_pairs or []  # Continue from previous or start fresh

        # Create fresh EndReason and OutputStorage contexts and register control tools
        end_reason = EndReason()
        output_storage = OutputStorage()
        self._tool_registry.register(SetOutputTool(output_storage))
        self._tool_registry.register(CompleteWorkTool(end_reason))
        self._tool_registry.register(AbortWorkTool(end_reason))

        for step in range(max_steps):
            # Run step and get new pair
            pair, dom_snapshot, screenshot_b64 = await self._run_step(
                step, session_start_messages, pairs
            )

            # Accumulate pairs
            pairs.append(pair)

            # Check if control tool ended execution
            if end_reason.value:
                self._logger.info(
                    f"Worker session end - Reason: {end_reason.value.value}"
                )
                steps_used = step + 1
                break
        else:
            self._logger.info("Worker session end - Reason: max_steps_reached")
            end_reason.value = WorkerStatus.MAX_STEPS
            steps_used = max_steps

        # Build feedback summary from all pairs
        feedback = self._build_summary(pairs)

        return WorkerSession(
            status=end_reason.value,
            output=output_storage.value,
            feedback=feedback,
            pairs=pairs,
            task_description=task_description,
            steps_used=steps_used,
            max_steps=max_steps,
            final_dom=dom_snapshot,
            final_screenshot=screenshot_b64,
        )

    async def do(
        self,
        task: str,
        previous_pairs: Optional[List[ToolCallPair]] = None,
        max_steps: int = 20,
    ) -> WorkerSession:
        """
        Execute task, optionally continuing from previous conversation history.

        Args:
            task: Task description
            previous_pairs: Optional list of previous ToolCallPairs for conversation history
            max_steps: Maximum number of steps to execute

        Returns:
            WorkerSession with execution result and conversation history
        """
        user_content = []
        user_content.append(TextContent(text=f"Task: {task}"))

        # Get current page state
        dom_snapshot = await self.worker_browser.get_dom_snapshot(mode=self._mode)
        screenshot_b64 = await self.worker_browser.get_screenshot()
        user_content.append(TextContent(text=dom_snapshot, tag="dom_snapshot"))
        user_content.append(
            ImageContent(
                data=screenshot_b64,
                mime_type=ImageMimeType.PNG,
                tag="screenshot",
            )
        )

        # Build session start messages (never compacted)
        session_start_messages = [
            SystemMessage(content=[TextContent(text=build_worker_prompt())]),
            UserMessage(content=user_content),
        ]

        return await self._run(task, max_steps, session_start_messages, previous_pairs)
