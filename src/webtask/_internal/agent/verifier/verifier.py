"""Verifier role - checks if subtask succeeded using conversation-based LLM."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from webtask.llm import (
    Message,
    SystemMessage,
    UserMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
    ImageMimeType,
)
from webtask._internal.llm import purge_messages_content
from ..tool import ToolRegistry
from ...prompts.verifier_prompt import build_verifier_prompt
from ...utils.logger import get_logger
from webtask._internal.utils.wait import wait
from .verifier_session import VerifierSession, VerifierDecision
from .tools.complete_task import CompleteTaskTool
from .tools.abort_task import AbortTaskTool
from .tools.request_correction import RequestCorrectionTool
from ..worker.tools import WaitTool
from .verifier_browser import VerifierBrowser

if TYPE_CHECKING:
    from ..session_browser import SessionBrowser
    from webtask.llm.llm import LLM


class VerifierResult:
    """Wrapper to track verifier decision and feedback."""

    def __init__(self):
        self.decision: Optional[VerifierDecision] = None
        self.feedback: Optional[str] = None


class Verifier:
    """Verifier role - checks if subtask succeeded using conversation-based LLM."""

    # Small delay after each action
    ACTION_DELAY = 0.1

    def __init__(self, llm: "LLM", session_browser: "SessionBrowser"):
        self._llm = llm
        self.verifier_browser = VerifierBrowser(session_browser)
        self._tool_registry = ToolRegistry()
        self._logger = get_logger(__name__)

        # Register normal tools (non-terminal)
        self._tool_registry.register(WaitTool())

        # Control tools registered per-run in _run() with fresh VerifierResult context

    async def run(
        self,
        task_description: str,
        max_steps: int,
        worker_actions: str,
        final_dom: str,
        final_screenshot: str,
        previous_history: Optional[str] = None,
    ) -> VerifierSession:
        user_content = []

        user_content.append(TextContent(text=f"Task: {task_description}"))

        if previous_history:
            user_content.append(
                TextContent(text=f"\nPrevious history:\n{previous_history}")
            )

        # Add current worker summary (what just happened)
        user_content.append(TextContent(text=f"\nWorker actions:\n{worker_actions}"))

        # Add worker's final observations
        user_content.append(TextContent(text=final_dom, tag="dom_snapshot"))
        user_content.append(
            ImageContent(
                data=final_screenshot,
                mime_type=ImageMimeType.PNG,
                tag="screenshot",
            )
        )

        # Build session start messages (never compacted)
        session_start_messages: List[Message] = [
            SystemMessage(content=[TextContent(text=build_verifier_prompt())]),
            UserMessage(content=user_content),
        ]

        return await self._run(task_description, max_steps, session_start_messages)

    async def _run(
        self,
        task_description: str,
        max_steps: int,
        messages: List[Message],
    ) -> VerifierSession:
        """Shared implementation for verification."""
        start_time = datetime.now()
        all_descriptions: List[str] = []

        # Create fresh VerifierResult wrapper and register control tools
        verifier_result = VerifierResult()
        self._tool_registry.register(CompleteTaskTool(verifier_result))
        self._tool_registry.register(RequestCorrectionTool(verifier_result))
        self._tool_registry.register(AbortTaskTool(verifier_result))

        self._logger.info(f"Verifier session start - Task: {task_description}")

        # Main execution loop
        for step in range(max_steps):
            self._logger.info(f"Step {step + 1} - Start")

            # Purge old content from message history
            # Keep only last 1 DOM snapshot (they're large and less critical)
            messages = purge_messages_content(
                messages,
                by_tags=["dom_snapshot"],
                message_types=[ToolResultMessage, UserMessage],
                keep_last_messages=1,
            )
            # Keep last 2 screenshots (more valuable for visual context)
            messages = purge_messages_content(
                messages,
                by_tags=["screenshot"],
                message_types=[ToolResultMessage, UserMessage],
                keep_last_messages=1,
            )

            # Call LLM with conversation history and tools
            self._logger.debug("Sending LLM request...")
            assistant_msg = await self._llm.call_tools(
                messages=messages,
                tools=self._tool_registry.get_all(),
            )
            messages.append(assistant_msg)

            # Handle case when LLM doesn't return tool calls
            if not assistant_msg.tool_calls:
                self._logger.warning(
                    "LLM did not return any tool calls - creating empty result"
                )
                tool_results = []
                descriptions = []
            else:
                # Log response
                tool_names = [tc.name for tc in assistant_msg.tool_calls]
                self._logger.info(f"Received LLM response - Tools: {tool_names}")

                # Log reasoning if present
                if assistant_msg.content:
                    for content in assistant_msg.content:
                        if hasattr(content, "text") and content.text:
                            self._logger.info(f"Reasoning: {content.text}")

                # Execute tools using registry (control tools modify verifier_result directly)
                tool_results, descriptions = (
                    await self._tool_registry.execute_tool_calls(
                        assistant_msg.tool_calls
                    )
                )

            # Accumulate descriptions
            all_descriptions.extend(descriptions)

            # Wait after all actions complete
            await wait(self.ACTION_DELAY)

            # Always capture fresh observations (like worker does)
            dom_snapshot = await self.verifier_browser.get_dom_snapshot()
            screenshot_b64 = await self.verifier_browser.get_screenshot()
            content = [
                TextContent(text=dom_snapshot, tag="dom_snapshot"),
                ImageContent(
                    data=screenshot_b64,
                    mime_type=ImageMimeType.PNG,
                    tag="screenshot",
                ),
            ]

            # Create tool result message
            result_message = ToolResultMessage(
                results=tool_results,
                content=content,
            )
            messages.append(result_message)

            # Check if control tool made a decision
            if verifier_result.decision:
                # Log decision
                self._logger.info(f"Decision: {verifier_result.decision.value}")
                if verifier_result.feedback:
                    self._logger.info(f"Feedback: {verifier_result.feedback}")

                self._logger.info(f"Step {step + 1} - End")
                self._logger.info(
                    f"Verifier session end - Decision: {verifier_result.decision.value}"
                )

                # Build summary from all descriptions
                summary = "\n".join(
                    f"{i+1}. {desc}" for i, desc in enumerate(all_descriptions)
                )

                # Decision was made, return immediately
                return VerifierSession(
                    task_description=task_description,
                    decision=verifier_result.decision,
                    feedback=verifier_result.feedback,
                    start_time=start_time,
                    end_time=datetime.now(),
                    max_steps=max_steps,
                    steps_used=step + 1,
                    summary=summary,
                )

        # This should never be reached - Verifier should always make a decision
        raise ValueError("Verifier reached max_steps without making a decision")
