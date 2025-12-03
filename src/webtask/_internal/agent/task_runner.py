"""TaskRunner - executes one task with conversation-based LLM."""

from typing import Awaitable, Callable, List, Optional, Tuple, TYPE_CHECKING, Type
from pydantic import BaseModel
from webtask.llm import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    Content,
    TextContent,
)
from webtask.llm.tool import Tool
from webtask._internal.llm import purge_messages_content
from .tool_registry import ToolRegistry
from ..prompts.worker_prompt import build_worker_prompt
from ..utils.logger import get_logger
from .run import Run, TaskResult, TaskStatus
from .tools import CompleteWorkTool, AbortWorkTool

if TYPE_CHECKING:
    from webtask.llm.llm import LLM

# Type alias for message pairs
MessagePair = Tuple[AssistantMessage, ToolResultMessage]


class TaskRunner:
    """Task executor - executes one task with conversation-based LLM.

    Accepts browser tools and a context callback from outside.
    Creates control tools (complete_work, abort_work) internally.
    """

    def __init__(
        self,
        llm: "LLM",
        tools: List[Tool],
        get_context: Callable[[], Awaitable[List[Content]]],
    ):
        """Initialize TaskRunner.

        Args:
            llm: LLM instance for making tool calls
            tools: List of browser tools (click, fill, goto, etc.)
            get_context: Async callback that returns page context as Content list
        """
        self._llm = llm
        self._tools = tools
        self._get_context = get_context
        self._logger = get_logger(__name__)

    async def run(
        self,
        task: str,
        max_steps: int,
        previous_runs: Optional[List[Run]] = None,
        output_schema: Optional[Type[BaseModel]] = None,
    ) -> Run:
        # Create result object for this run
        result = TaskResult()

        # Setup tool registry for this run (browser tools + control tools)
        tool_registry = self._setup_tools(result, output_schema)

        session_start_messages = await self._build_session_start_messages(
            task, previous_runs
        )

        self._logger.info(f"Task start - Task: {task}")

        pairs: List[MessagePair] = []
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

            tool_results = await tool_registry.execute_tool_calls(
                assistant_msg.tool_calls or []
            )

            # Get page context after tool execution
            page_context = await self._get_context()

            tool_result_msg = ToolResultMessage(
                results=tool_results,
                content=page_context,
            )
            pairs.append((assistant_msg, tool_result_msg))

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
        messages: List[Message] = []
        for assistant_msg, tool_result_msg in pairs:
            messages.append(assistant_msg)
            messages.append(tool_result_msg)

        # Extract final state from last pair
        final_dom = ""
        final_screenshot = None
        if pairs:
            _, last_tool_result = pairs[-1]
            if last_tool_result.content:
                for content in last_tool_result.content:
                    if hasattr(content, "tag"):
                        if content.tag == "dom_snapshot" and hasattr(content, "text"):
                            final_dom = content.text
                        elif content.tag == "screenshot" and hasattr(content, "data"):
                            final_screenshot = content.data

        # Build and return Run with embedded Result
        return Run(
            result=result,
            summary=summary,
            messages=messages,
            task_description=task,
            steps_used=steps_used,
            max_steps=max_steps,
            final_dom=final_dom,
            final_screenshot=final_screenshot,
        )

    ### Helper methods ###

    def _setup_tools(
        self,
        result: TaskResult,
        output_schema: Optional[Type[BaseModel]],
    ) -> ToolRegistry:
        """Create and configure tool registry for this run.

        Registers browser tools (passed via constructor) and control tools.
        """
        tool_registry = ToolRegistry()

        # Register browser tools (injected from outside)
        for tool in self._tools:
            tool_registry.register(tool)

        # Register control tools (created internally)
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

        # Add context (page state + files) via get_context callback
        context = await self._get_context()
        user_content.extend(context)

        # Build session start messages (never compacted)
        return [
            SystemMessage(content=[TextContent(text=build_worker_prompt())]),
            UserMessage(content=user_content),
        ]

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

    def _build_summary(self, pairs: List[MessagePair]) -> str:
        if not pairs:
            return ""

        lines = []
        for assistant_msg, tool_result_msg in pairs:
            # Extract reasoning from assistant message
            reasoning = self._extract_reasoning(assistant_msg)

            # Add reasoning as main bullet point if present
            if reasoning:
                reasoning = reasoning.strip()
                # Single line reasoning
                if "\n" not in reasoning:
                    lines.append(f"- {reasoning}")
                else:
                    # Multi-line reasoning
                    reasoning_lines = reasoning.split("\n")
                    lines.append(f"- {reasoning_lines[0]}")
                    for reasoning_line in reasoning_lines[1:]:
                        lines.append(f"  {reasoning_line}")

            # Add actions as nested list (indented) - descriptions are in ToolResult
            for result in tool_result_msg.results:
                if result.status.value == "error":
                    lines.append(f"  - {result.description} [FAILED: {result.error}]")
                else:
                    lines.append(f"  - {result.description}")

        return "\n".join(lines)

    def _prepare_messages(
        self, session_start_messages: List[Message], pairs: List[MessagePair]
    ) -> List[Message]:
        # Convert pairs to messages
        tool_messages: List[Message] = []
        for assistant_msg, tool_result_msg in pairs:
            tool_messages.append(assistant_msg)
            tool_messages.append(tool_result_msg)

        # Combine session start + tool messages
        all_messages = session_start_messages + tool_messages

        # Purge old content (keep context size manageable)
        all_messages = purge_messages_content(
            all_messages,
            by_tags=["tabs_context", "dom_snapshot"],
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
