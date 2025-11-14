"""Verifier role - checks if subtask succeeded using conversation-based LLM."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, TYPE_CHECKING
from webtask.llm import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
    ImageMimeType,
    ToolCall,
    ToolResult,
    ToolResultStatus,
)
from webtask.agent.tool import Tool
from webtask._internal.llm import MessagePurger
from ..tool import ToolRegistry
from webtask._internal.config import Config
from ...prompts.verifier_prompt import build_verifier_prompt
from webtask._internal.utils.wait import wait
from ..worker.worker_session import WorkerSession
from .verifier_session import VerifierSession, VerifierDecision
from .tools.complete_task import CompleteTaskTool
from .tools.abort_task import AbortTaskTool
from .tools.request_correction import RequestCorrectionTool
from .tools.observe import ObserveTool
from ..worker.tools.wait import WaitTool
from ..verifier_browser import VerifierBrowser

if TYPE_CHECKING:
    from ..agent_browser import AgentBrowser
    from webtask.llm.llm_v2 import LLM


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
            keep_last_messages=1  # Verifier only needs most recent observation
        )

    def _format_worker_actions(self, worker_session: WorkerSession) -> str:
        """Format worker actions as text for verifier context."""
        if not worker_session.messages:
            return "No worker actions yet."

        lines = ["Worker Actions Summary:"]
        lines.append(f"Steps used: {worker_session.steps_used}/{worker_session.max_steps}")
        lines.append(f"End reason: {worker_session.end_reason}")
        lines.append("")

        # Extract actions from assistant messages with their results
        step_num = 1
        for i, msg in enumerate(worker_session.messages):
            if isinstance(msg, AssistantMessage) and msg.tool_calls:
                actions = []

                # Get the next message (should be ToolResultMessage)
                tool_results = {}
                if i + 1 < len(worker_session.messages):
                    next_msg = worker_session.messages[i + 1]
                    if isinstance(next_msg, ToolResultMessage):
                        for result in next_msg.results:
                            tool_results[result.tool_call_id] = result

                # Parse tool calls - only keep actions (skip observe, think, complete_work, abort_work)
                for tc in msg.tool_calls:
                    if tc.name not in ["observe", "think", "complete_work", "abort_work"]:
                        # Action tool - get description
                        description = tc.arguments.get("description", tc.name)

                        # Check if action succeeded or failed
                        result = tool_results.get(tc.id)
                        if result and result.status.value == "error":
                            actions.append(f"{description} (ERROR: {result.error})")
                        else:
                            actions.append(description)

                # Only add step if there are actions
                if actions:
                    lines.append(f"Step {step_num}:")
                    for action in actions:
                        lines.append(f"  - {action}")
                    step_num += 1

        return "\n".join(lines)

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
        worker_session: WorkerSession,
    ) -> VerifierSession:
        """Execute verification using conversation-based LLM."""
        start_time = datetime.now()

        # Build initial user message with context
        worker_summary = self._format_worker_actions(worker_session)
        initial_text = f"""Task: {task_description}

{worker_summary}"""

        # Build user content with worker summary + final observations
        user_content = [TextContent(text=initial_text)]

        # Add worker's final observations
        if worker_session.final_dom:
            user_content.append(TextContent(text=worker_session.final_dom, tag="observation"))
        if worker_session.final_screenshot:
            user_content.append(ImageContent(data=worker_session.final_screenshot, mime_type=ImageMimeType.PNG, tag="observation"))

        # Initialize conversation
        messages: List[Message] = [
            SystemMessage(content=[TextContent(text=build_verifier_prompt())]),
            UserMessage(content=user_content),
        ]

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
            observe_called = any(tc.name == "observe" for tc in assistant_msg.tool_calls)
            content = []
            if observe_called:
                dom_snapshot = await self.verifier_browser.get_dom_snapshot()
                screenshot_b64 = await self.verifier_browser.get_screenshot()
                content = [
                    TextContent(text=dom_snapshot, tag="observation"),
                    ImageContent(data=screenshot_b64, mime_type=ImageMimeType.PNG, tag="observation"),
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
                worker_session=worker_session,
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
