"""Selector - natural language element selection using LLM."""

from typing import List, Optional
from pydantic import BaseModel, Field
from webtask.llm import LLM
from webtask.llm.tool import Tool
from webtask.llm.message import Content
from webtask.browser import Element
from webtask.exceptions import TaskAbortedError
from .task_runner import TaskRunner
from .run import TaskStatus
from .agent_browser import AgentBrowser
from ..prompts.worker_prompt import build_worker_prompt


class ElementSelection(BaseModel):
    """Structured output for element selection."""

    element_id: str = Field(
        description="The element ID (e.g., 'button-0', 'input-3') that best matches the description"
    )


class Selector:
    """
    Natural language element selector.

    Uses the LLM to identify elements matching a description
    from the current page's DOM context.

    Example:
        selector = Selector(llm, browser)
        element = await selector.select("the login button")
        await element.click()
    """

    def __init__(self, llm: LLM, browser: AgentBrowser):
        """
        Initialize selector.

        Args:
            llm: LLM instance for element identification
            browser: AgentBrowser for DOM context and element resolution
        """
        self.llm = llm
        self.browser = browser

    async def select(self, description: str, max_steps: int = 5) -> Element:
        """
        Select an element using natural language description.

        Args:
            description: Natural language description of the element
                        (e.g., "the login button", "email input field")
            max_steps: Maximum steps to execute (default: 5)

        Returns:
            Element instance for direct interaction (click, fill, etc.)

        Raises:
            TaskAbortedError: If element cannot be found
            KeyError: If the identified element ID doesn't exist
        """
        # Ensure DOM mode for element selection
        self.browser.set_mode("dom")

        # Create context callback
        async def get_context() -> List[Content]:
            return await self.browser.get_page_context(
                include_dom=True, include_screenshot=True
            )

        # Create TaskRunner with no tools (just identification)
        task_runner = TaskRunner(
            llm=self.llm,
            tools=[],  # No tools needed - just identify
            get_context=get_context,
            system_prompt=build_worker_prompt(),
        )

        task = f"Identify the element that matches: {description}"
        run = await task_runner.run(
            task=task,
            max_steps=max_steps,
            previous_runs=[],
            output_schema=ElementSelection,
        )

        if run.result.status == TaskStatus.ABORTED:
            raise TaskAbortedError(
                run.result.feedback or f"Could not identify element: {description}"
            )

        if not run.result.output:
            raise TaskAbortedError(f"Could not identify element: {description}")

        element_id = run.result.output.element_id
        return await self.browser.select(element_id)
