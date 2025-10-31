"""Verifier role - verifies task completion."""

from typing import List
from ...llm import LLM, Context, Block
from ...prompts import get_prompt
from ...utils import parse_json
from ..step import Action, ExecutionResult, VerificationResult
from ..step_history import StepHistory
from ...llm_browser import LLMBrowser


class Verifier:
    """Verifies whether the task has been completed."""

    def __init__(
        self,
        llm: LLM,
        task: str,
        step_history: StepHistory,
        llm_browser: LLMBrowser,
        use_screenshot: bool = False,
    ):
        self.llm = llm
        self.task = task
        self.step_history = step_history
        self.llm_browser = llm_browser
        self.use_screenshot = use_screenshot

    async def _build_context(
        self, actions: List[Action], execution_results: List[ExecutionResult]
    ) -> Context:
        system = get_prompt("verifier_system")
        context = Context(system=system)
        context.append(Block(f"Task:\n{self.task}"))

        lines = ["Current Actions:"]
        for i, (action, execution_result) in enumerate(
            zip(actions, execution_results), 1
        ):
            lines.append(f"  Action {i}:")
            lines.append(f"    Tool: {action.tool_name}")
            lines.append(f"    Reason: {action.reason}")
            lines.append(f"    Parameters: {action.parameters}")
            lines.append(
                f"    Execution: {'Success' if execution_result.success else 'Failed'}"
            )
            if execution_result.error:
                lines.append(f"    Error: {execution_result.error}")
        context.append(Block("\n".join(lines)))

        context.append(self.step_history.to_context_block())
        context.append(await self.llm_browser.to_context_block(use_screenshot=self.use_screenshot))
        return context

    async def verify(
        self, actions: List[Action], execution_results: List[ExecutionResult]
    ) -> VerificationResult:
        """Verify if the task is complete."""
        context = await self._build_context(actions, execution_results)
        response = await self.llm.generate(context)
        verification_data = parse_json(response)

        complete = verification_data.get("complete")
        message = verification_data.get("message")

        if complete is None or not message:
            raise ValueError("LLM response missing 'complete' or 'message' field")

        return VerificationResult(complete=bool(complete), message=message)
