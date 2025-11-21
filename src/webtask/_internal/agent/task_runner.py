"""TaskRunner - executes one task with conversation-based LLM."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING, Type
from pydantic import BaseModel
from webtask.llm import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    Content,
    TextContent,
    ImageContent,
    ImageMimeType,
)
from webtask._internal.llm import purge_messages_content
from .tool_registry import ToolRegistry
from ..prompts.worker_prompt import build_worker_prompt
from ..utils.logger import get_logger
from .agent_browser import AgentBrowser
from .run import Run, TaskResult, TaskStatus
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
    from webtask.llm.llm import LLM


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


class TaskRunner:
    """Task executor - executes one task with conversation-based LLM.

    Stateless executor that can be reused across multiple runs.
    """

    def __init__(
        self,
        llm: "LLM",
        browser: AgentBrowser,
    ):
        self._llm = llm
        self.browser = browser
        self._logger = get_logger(__name__)

    async def run(
        self,
        task: str,
        max_steps: int,
        previous_runs: Optional[List[Run]] = None,
        output_schema: Optional[Type[BaseModel]] = None,
        resources: Optional[Dict[str, str]] = None,
    ) -> Run:
        # Create result object for this run
        result = TaskResult()

        # Setup tool registry for this run
        tool_registry = self._setup_tools(result, resources, output_schema)

        session_start_messages = await self._build_session_start_messages(
            task, previous_runs
        )

        self._logger.info(f"Task start - Task: {task}")

        pairs: List[ToolCallPair] = []
        for step in range(max_steps):
            self._logger.info(f"Step {step + 1} - Start")

            all_messages = self._prepare_messages(session_start_messages, pairs)

            self._logger.debug("Sending LLM request...")
            assistant_msg = await self._llm.call_tools(
                messages=all_messages,
                tools=tool_registry.get_all(),
            )

            reasoning = self._extract_reasoning(assistant_msg)
            tool_names = (
                [tc.name for tc in assistant_msg.tool_calls]
                if assistant_msg.tool_calls
                else []
            )

            self._logger.info(f"Received LLM response - Tools: {tool_names}")
            if reasoning:
                self._logger.info(f"Reasoning: {reasoning}")

            tool_results, descriptions = await tool_registry.execute_tool_calls(
                assistant_msg.tool_calls or []
            )

            content, dom_snapshot, screenshot_b64 = await self._get_page_state_content()

            tool_result_msg = ToolResultMessage(
                results=tool_results,
                content=content,
            )
            pair = ToolCallPair(
                assistant_msg=assistant_msg,
                tool_result_msg=tool_result_msg,
                descriptions=descriptions,
                reasoning=reasoning,
            )
            pairs.append(pair)

            self._logger.info(f"Step {step + 1} - End")

            # Check if control tool ended execution
            if result.status:
                steps_used = step + 1
                break
        else:
            self._logger.info("Task end - Reason: max_steps_reached")
            result.status = TaskStatus.ABORTED
            result.feedback = "Reached maximum steps"
            steps_used = max_steps

        self._logger.info(f"Task end - Status: {result.status.value}")

        # Build automatic summary from all pairs
        summary = self._build_summary(pairs)

        # Convert pairs to full message list
        messages = []
        for pair in pairs:
            messages.append(pair.assistant_msg)
            messages.append(pair.tool_result_msg)

        # Build and return Run with embedded Result
        return Run(
            result=result,
            summary=summary,
            messages=messages,
            task_description=task,
            steps_used=steps_used,
            max_steps=max_steps,
            final_dom=dom_snapshot,
            final_screenshot=screenshot_b64,
        )

    ### Helper methods ###

    def _setup_tools(
        self,
        result: TaskResult,
        resources: Optional[Dict[str, str]],
        output_schema: Optional[Type[BaseModel]],
    ) -> ToolRegistry:
        """Create and configure tool registry for this run."""
        tool_registry = ToolRegistry()

        # Register browser action tools
        tool_registry.register(WaitTool())
        tool_registry.register(ClickTool(self.browser))
        tool_registry.register(FillTool(self.browser))
        tool_registry.register(TypeTool(self.browser))
        tool_registry.register(NavigateTool(self.browser))
        tool_registry.register(UploadTool(self.browser, resources))

        # Register control tools
        tool_registry.register(CompleteWorkTool(result, output_schema))
        tool_registry.register(AbortWorkTool(result))

        return tool_registry

    async def _build_session_start_messages(
        self,
        task: str,
        previous_runs: Optional[List[Run]] = None,
    ) -> List[Message]:
        user_content: List[Content] = []

        # Add previous sessions if provided
        if previous_runs:
            formatted_sessions = self._format_previous_runs(previous_runs)
            user_content.append(TextContent(text=formatted_sessions))

        user_content.append(TextContent(text=f"## Current task:\n{task}"))

        # Add current page state (DOM + screenshot)
        page_state_content, _, _ = await self._get_page_state_content()
        user_content.extend(page_state_content)

        # Build session start messages (never compacted)
        return [
            SystemMessage(content=[TextContent(text=build_worker_prompt())]),
            UserMessage(content=user_content),
        ]

    async def _get_page_state_content(
        self,
    ) -> Tuple[List[Content], str, Optional[str]]:
        dom_snapshot = await self.browser.get_dom_snapshot()
        screenshot_b64 = await self.browser.get_screenshot()

        content: List[Content] = []
        content.append(TextContent(text=dom_snapshot, tag="dom_snapshot"))

        # Only add screenshot if we have one (page is open)
        if screenshot_b64 is not None:
            content.append(
                ImageContent(
                    data=screenshot_b64,
                    mime_type=ImageMimeType.PNG,
                    tag="screenshot",
                )
            )

        return content, dom_snapshot, screenshot_b64

    def _format_previous_runs(self, runs: List[Run]) -> str:
        lines = ["## Previous tasks:", ""]
        for i, run in enumerate(runs, 1):
            lines.append(f"### Task {i}")
            lines.append(f"Task: {run.task_description}")
            lines.append(f"Status: {run.result.status.value.capitalize()}")
            if run.result.feedback:
                lines.append(f"Feedback: {run.result.feedback}")
            lines.append("")  # Blank line between tasks
        return "\n".join(lines)

    def _build_summary(self, pairs: List[ToolCallPair]) -> str:
        if not pairs:
            return ""

        lines = []
        for pair in pairs:
            # Add reasoning as main bullet point if present
            if pair.reasoning:
                reasoning = pair.reasoning.strip()
                # Single line reasoning
                if "\n" not in reasoning:
                    lines.append(f"- {reasoning}")
                else:
                    # Multi-line reasoning
                    reasoning_lines = reasoning.split("\n")
                    lines.append(f"- {reasoning_lines[0]}")
                    for reasoning_line in reasoning_lines[1:]:
                        lines.append(f"  {reasoning_line}")

            # Add actions as nested list (indented)
            if pair.descriptions or pair.tool_result_msg.results:
                # Match descriptions with tool results
                for i, description in enumerate(pair.descriptions):
                    # Get corresponding tool result if available
                    if i < len(pair.tool_result_msg.results):
                        result = pair.tool_result_msg.results[i]
                        if result.status.value == "error":
                            lines.append(f"  - {description} [FAILED: {result.error}]")
                        else:
                            lines.append(f"  - {description}")
                    else:
                        lines.append(f"  - {description}")

        return "\n".join(lines)

    def _prepare_messages(
        self, session_start_messages: List[Message], pairs: List[ToolCallPair]
    ) -> List[Message]:
        keep_last_n_pairs = 5

        # Convert pairs to messages (with optional compacting)
        tool_messages = []

        # If we have more pairs than keep_last_n_pairs, build summary from old ones
        if len(pairs) > keep_last_n_pairs:
            old_pairs = pairs[:-keep_last_n_pairs]
            summary = self._build_summary(old_pairs)
            if summary:
                tool_messages.append(
                    UserMessage(
                        content=[
                            TextContent(
                                text=f"Previous actions in this session:\n{summary}"
                            )
                        ]
                    )
                )

        # Add recent pairs (or all pairs if <= keep_last_n_pairs)
        recent_pairs = (
            pairs[-keep_last_n_pairs:] if len(pairs) > keep_last_n_pairs else pairs
        )
        for pair in recent_pairs:
            tool_messages.append(pair.assistant_msg)
            tool_messages.append(pair.tool_result_msg)

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

        return all_messages

    def _extract_reasoning(self, assistant_msg: AssistantMessage) -> Optional[str]:
        if assistant_msg.content:
            for content in assistant_msg.content:
                if hasattr(content, "text") and content.text:
                    return content.text
        return None
