"""Verifier role - checks if subtask succeeded using conversation-based LLM."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from webtask.llm import (
    Content,
    Message,
    SystemMessage,
    UserMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
    ImageMimeType,
    ToolCall,
    ToolResultStatus,
)
from webtask._internal.llm import MessagePurger
from ..tool import ToolRegistry
from ...prompts.verifier_prompt import build_verifier_prompt
from webtask._internal.utils.wait import wait
from .verifier_session import VerifierSession, VerifierDecision
from .tools.complete_task import CompleteTaskTool
from .tools.abort_task import AbortTaskTool
from .tools.request_correction import RequestCorrectionTool
from .tools.observe import ObserveTool
from ..worker.tools.wait import WaitTool
from ..verifier_browser import VerifierBrowser

if TYPE_CHECKING:
    from ..agent_browser import AgentBrowser
    from webtask.llm.llm import LLM


class Verifier:
    """Verifier role - checks if subtask succeeded using conversation-based LLM."""

    # Small delay after each action
    ACTION_DELAY = 0.1

    def __init__(self, llm: "LLM", agent_browser: "AgentBrowser"):
        self._llm = llm
        self.verifier_browser = VerifierBrowser(agent_browser)
        self._tool_registry = ToolRegistry()

        # Register all tools
        self._tool_registry.register(ObserveTool(self.verifier_browser))
        self._tool_registry.register(WaitTool())
        self._tool_registry.register(CompleteTaskTool())
        self._tool_registry.register(RequestCorrectionTool())
        self._tool_registry.register(AbortTaskTool())

        # Create message purger to keep context bounded
        self._message_purger = MessagePurger(
            purge_tags=["observation"],
            message_types=[ToolResultMessage, UserMessage],
            keep_last_messages=1,  # Verifier only needs most recent observation
        )

    async def _execute_tool_calls(self, tool_calls: List[ToolCall]) -> dict:
        """Execute all tool calls and return results."""
        results = []

        for tool_call in tool_calls:
            # Execute using registry
            tool_result = await self._tool_registry.execute_tool_call(tool_call)
            results.append(tool_result)

            # Return immediately if decision tool called (only on success)
            if tool_result.status == ToolResultStatus.SUCCESS:
                tool = self._tool_registry.get(tool_call.name)
                if isinstance(tool, CompleteTaskTool):
                    return {
                        "results": results,
                        "decision": VerifierDecision.COMPLETE_TASK,
                        "feedback": tool_call.arguments.get("feedback", ""),
                    }
                elif isinstance(tool, RequestCorrectionTool):
                    return {
                        "results": results,
                        "decision": VerifierDecision.REQUEST_CORRECTION,
                        "feedback": tool_call.arguments.get("feedback", ""),
                    }
                elif isinstance(tool, AbortTaskTool):
                    return {
                        "results": results,
                        "decision": VerifierDecision.ABORT_TASK,
                        "feedback": tool_call.arguments.get("feedback", ""),
                    }

        # If we get here, no decision tool was called - this shouldn't happen
        raise ValueError("No decision tool was called by Verifier")

    async def run(
        self,
        task_description: str,
        max_steps: int,
        worker_summary: str,
        final_dom: Optional[str],
        final_screenshot: Optional[str],
        previous_session: Optional[VerifierSession] = None,
    ) -> VerifierSession:
        """Execute verification with optional continuation from previous session.

        Args:
            task_description: Task to verify
            max_steps: Maximum number of steps
            worker_summary: Summary of worker actions
            final_dom: Final DOM state after worker actions
            final_screenshot: Final screenshot after worker actions
            previous_session: Previous verifier session to continue from
        """
        if previous_session is not None:
            # Continue from previous conversation
            messages = previous_session.messages.copy()

            # Add new worker result as user message
            user_text = f"Worker has made corrections. Here is the updated result:\n\n{worker_summary}"

            user_content: List[Content] = [TextContent(text=user_text)]

            # Add worker's final observations
            if final_dom:
                user_content.append(TextContent(text=final_dom, tag="observation"))
            if final_screenshot:
                user_content.append(
                    ImageContent(
                        data=final_screenshot,
                        mime_type=ImageMimeType.PNG,
                        tag="observation",
                    )
                )

            messages.append(UserMessage(content=user_content))

            return await self._run(task_description, max_steps, messages)
        else:
            # Start fresh
            # Build user content with worker summary + final observations
            initial_text = f"Task: {task_description}\n\n{worker_summary}"

            # Explicit type annotation to allow both TextContent and ImageContent
            user_content: List[Content] = [TextContent(text=initial_text)]

            # Add worker's final observations
            if final_dom:
                user_content.append(TextContent(text=final_dom, tag="observation"))
            if final_screenshot:
                user_content.append(
                    ImageContent(
                        data=final_screenshot,
                        mime_type=ImageMimeType.PNG,
                        tag="observation",
                    )
                )

            # Initialize conversation
            messages: List[Message] = [
                SystemMessage(content=[TextContent(text=build_verifier_prompt())]),
                UserMessage(content=user_content),
            ]

            return await self._run(task_description, max_steps, messages)

    async def _run(
        self,
        task_description: str,
        max_steps: int,
        messages: List[Message],
    ) -> VerifierSession:
        """Shared implementation for verification."""
        start_time = datetime.now()
        decision = None

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

            # Execute all tool calls and collect results (will raise if no decision made)
            execution_result = await self._execute_tool_calls(assistant_msg.tool_calls)
            tool_results = execution_result["results"]
            decision = execution_result["decision"]
            feedback = execution_result["feedback"]

            # Wait after all actions complete
            await wait(self.ACTION_DELAY)

            # Check if observe tool was called - if so, capture fresh observations
            observe_called = any(
                tc.name == "observe" for tc in assistant_msg.tool_calls
            )
            content = []
            if observe_called:
                dom_snapshot = await self.verifier_browser.get_dom_snapshot()
                screenshot_b64 = await self.verifier_browser.get_screenshot()
                content = [
                    TextContent(text=dom_snapshot, tag="observation"),
                    ImageContent(
                        data=screenshot_b64,
                        mime_type=ImageMimeType.PNG,
                        tag="observation",
                    ),
                ]

            # Create tool result message
            result_message = ToolResultMessage(
                results=tool_results,
                content=content,
            )
            messages.append(result_message)

            # Decision was made, return immediately
            return VerifierSession(
                task_description=task_description,
                decision=decision,
                feedback=feedback,
                start_time=start_time,
                end_time=datetime.now(),
                max_steps=max_steps,
                steps_used=step + 1,
                messages=messages,
            )

        # This should never be reached - Verifier should always make a decision
        raise ValueError("Verifier reached max_steps without making a decision")
