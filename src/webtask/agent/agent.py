"""Agent - main interface for web automation."""

import logging
from typing import Dict, List, Optional, Any
from webtask.llm import LLM
from webtask.browser import Context
from webtask._internal.agent.worker.worker import Worker


class Agent:
    """
    Main agent interface for web automation.

    Requires a Context for browser management and page operations.

    Primary interface:
    - High-level autonomous: do(task) - Agent autonomously executes tasks with Worker
    - Supports persist_context for multi-turn conversations
    """

    def __init__(
        self,
        llm: LLM,
        context: Context,
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
        persist_context: bool = False,
    ):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning and task execution
            context: Context instance for browser management
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            mode: DOM context mode - "accessibility" (default) or "dom"
            persist_context: If True, maintain conversation history between do() calls (default: False)
        """
        self.llm = llm
        self.context = context
        self.wait_after_action = wait_after_action
        self.mode = mode
        self.persist_context = persist_context
        self.logger = logging.getLogger(__name__)

        # Store all conversation pairs if persist_context=True
        # Accumulates pairs from all do() calls for multi-turn conversations
        self._accumulated_pairs: List = []  # List[ToolCallPair]

    async def do(
        self,
        task: str,
        max_steps: int = 20,
        resources: Optional[Dict[str, str]] = None,
        wait_after_action: Optional[float] = None,
        mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task using Worker (new simplified interface).

        Args:
            task: Task description in natural language
            max_steps: Maximum number of steps to execute (default: 20)
            resources: Optional dict of file resources (name -> path)
            wait_after_action: Wait time in seconds after each action (overrides agent default if provided)
            mode: DOM context mode - "accessibility" or "dom" (overrides agent default if provided)

        Returns:
            Dict with status, output, and feedback:
            {
                "status": "completed" | "aborted" | "max_steps",
                "output": Any,  # Structured data from set_output tool
                "feedback": str  # Summary of what happened
            }
        """
        # Use task-level wait_after_action if provided, otherwise use agent default
        effective_wait = (
            wait_after_action
            if wait_after_action is not None
            else self.wait_after_action
        )

        # Use task-level mode if provided, otherwise use agent default
        effective_mode = mode if mode is not None else self.mode

        # Create worker
        worker = Worker(
            llm=self.llm,
            context=self.context,
            wait_after_action=effective_wait,
            resources=resources,
            mode=effective_mode,
        )

        # Execute with optional context persistence
        if self.persist_context:
            # Pass accumulated pairs from all previous do() calls
            # This maintains full conversation history across multiple tasks
            session = await worker.do(
                task,
                previous_pairs=self._accumulated_pairs if self._accumulated_pairs else None,
                max_steps=max_steps
            )
            # Accumulate new pairs from this session for next call
            self._accumulated_pairs.extend(session.pairs)
        else:
            # No context persistence - fresh session each time
            session = await worker.do(task, previous_pairs=None, max_steps=max_steps)

        # Convert WorkerSession to simple user-facing result
        return {
            "status": session.status.value,
            "output": session.output,
            "feedback": session.feedback,
        }

    async def close(self) -> None:
        """Close the agent and cleanup context."""
        if self.context:
            await self.context.close()
