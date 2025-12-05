"""TaskRunner - executes one task with conversation-based LLM."""

from collections import defaultdict
from typing import Awaitable, Callable, List, Optional, Tuple, TYPE_CHECKING, Type
from pydantic import BaseModel
from webtask.llm import (
    Message,
    SystemMessage,
    AssistantMessage,
    Content,
    TextContent,
)
from webtask.llm.tool import Tool
from .message import (
    AgentContent,
    AgentTextContent,
    AgentUserMessage,
    AgentToolResultMessage,
)
from .tool_registry import ToolRegistry
from ..utils.logger import get_logger
from .run import Run, TaskResult, TaskStatus
from .tools import CompleteWorkTool, AbortWorkTool

if TYPE_CHECKING:
    from webtask.llm.llm import LLM

# Type alias for message pairs
MessagePair = Tuple[AssistantMessage, AgentToolResultMessage]


class TaskRunner:
    """Task executor - executes one task with conversation-based LLM.

    Accepts browser tools and a context callback from outside.
    Creates control tools (complete_work, abort_work) internally.
    """

    def __init__(
        self,
        llm: "LLM",
        tools: List[Tool],
        get_context: Callable[[], Awaitable[List[AgentContent]]],
        system_prompt: str,
    ):
        """Initialize TaskRunner.

        Args:
            llm: LLM instance for making tool calls
            tools: List of browser tools (click, fill, goto, etc.)
            get_context: Async callback that returns page context as AgentContent list
            system_prompt: System prompt to use for the LLM
        """
        self._llm = llm
        self._tools = tools
        self._get_context = get_context
        self._system_prompt = system_prompt
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

            tool_result_msg = AgentToolResultMessage(
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

        # Convert pairs to full message list
        messages: List[Message] = []
        for assistant_msg, tool_result_msg in pairs:
            messages.append(assistant_msg)
            messages.append(tool_result_msg)

        # Build and return Run with embedded Result
        return Run(
            result=result,
            messages=messages,
            task_description=task,
            steps_used=steps_used,
            max_steps=max_steps,
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
        user_content: List[AgentContent] = []

        # Add previous sessions if provided
        if previous_runs:
            formatted_sessions = self._format_previous_runs(previous_runs)
            user_content.append(AgentTextContent(text=formatted_sessions))

        user_content.append(AgentTextContent(text=f"## Current task:\n{task}"))

        # Add context (page state + files) via get_context callback
        context = await self._get_context()
        user_content.extend(context)

        # Build session start messages (never compacted)
        return [
            SystemMessage(content=[TextContent(text=self._system_prompt)]),
            AgentUserMessage(content=user_content),
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

        # Purge old content based on lifespan values
        return self._purge_by_lifespan(all_messages)

    def _purge_by_lifespan(self, messages: List[Message]) -> List[Message]:
        """Purge old content from message history based on lifespan values.

        Content with lifespan=N is kept only in the last N messages that contain
        content with that lifespan value. Content with lifespan=None is kept forever.
        """
        if not messages:
            return messages

        # Group message indices by lifespan value
        lifespan_to_indices: dict[int, List[int]] = defaultdict(list)

        for i, msg in enumerate(messages):
            if not msg.content:
                continue
            for content_item in msg.content:
                if isinstance(content_item, AgentContent) and content_item.lifespan is not None:
                    if i not in lifespan_to_indices[content_item.lifespan]:
                        lifespan_to_indices[content_item.lifespan].append(i)

        # For each lifespan, determine which message indices should have content purged
        indices_to_purge: dict[int, set[int]] = defaultdict(set)

        for lifespan, indices in lifespan_to_indices.items():
            if len(indices) > lifespan:
                # Purge from older messages (keep last 'lifespan' messages)
                cutoff = len(indices) - lifespan
                for idx in indices[:cutoff]:
                    indices_to_purge[idx].add(lifespan)

        # Build purged message list
        purged: List[Message] = []
        for i, msg in enumerate(messages):
            if i in indices_to_purge and msg.content:
                lifespans_to_purge = indices_to_purge[i]
                filtered_content = [
                    content_item
                    for content_item in msg.content
                    if not isinstance(content_item, AgentContent)
                    or content_item.lifespan not in lifespans_to_purge
                ]
                purged.append(
                    msg.model_copy(
                        update={"content": filtered_content if filtered_content else None}
                    )
                )
            else:
                purged.append(msg)

        return purged

    def _extract_reasoning(self, assistant_msg: AssistantMessage) -> Optional[str]:
        if assistant_msg.content:
            for content in assistant_msg.content:
                if hasattr(content, "text") and content.text:
                    return content.text
        return None
