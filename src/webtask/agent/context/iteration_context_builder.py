"""Context builder for Iteration lists."""

from typing import List, TYPE_CHECKING
from ...llm import Block

if TYPE_CHECKING:
    from ..tool_call import Iteration


class IterationContextBuilder:
    """Builds LLM context blocks from Iteration lists."""

    def __init__(self, iterations: List["Iteration"]):
        self._iterations = iterations

    def build_iterations_context(self) -> Block:
        """Get formatted iterations for LLM context."""
        if not self._iterations:
            return Block(heading="Current Session Iterations", content="No iterations yet in this session.")

        content = ""
        for i, iteration in enumerate(self._iterations, 1):
            content += f"\n**Iteration {i}**\n"
            content += f"Thinking: {iteration.message}\n"
            content += f"Tool calls: {len(iteration.tool_calls)}\n"
            for tc in iteration.tool_calls:
                status = "✓" if tc.success else "✗"
                content += f"  {status} {tc.tool}({tc.parameters}) - {tc.result}\n"

        return Block(heading="Current Session Iterations", content=content.strip())
