"""Agent - main interface for web automation."""

from ..llm import LLM
from ..browser import Page
from ..llm_browser import LLMBrowser
from .tool import ToolRegistry
from .step_history import StepHistory
from .step import Step, TaskResult
from .role import Proposer, Executer, Verifier


class Agent:
    """
    Main agent interface for web automation.

    Provides high-level execute() for autonomous task completion
    and low-level methods for imperative control.
    """

    def __init__(self, llm: LLM, page: Page):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning
            page: Page instance to automate
        """
        self.llm = llm
        self.page = page

        # Create infrastructure
        self.llm_browser = LLMBrowser(page, llm)
        self.tool_registry = ToolRegistry()
        self.step_history = StepHistory()

        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register available tools in the registry."""
        from .tools.browser import NavigateTool, ClickTool, FillTool

        self.tool_registry.register(NavigateTool(self.llm_browser))
        self.tool_registry.register(ClickTool(self.llm_browser))
        self.tool_registry.register(FillTool(self.llm_browser))

    async def execute(
        self, task: str, max_steps: int = 10, clear_history: bool = True
    ) -> TaskResult:
        """
        Execute a task autonomously.

        Args:
            task: Task description in natural language
            max_steps: Maximum number of steps before giving up
            clear_history: Clear step history before starting (default: True)

        Returns:
            TaskResult with completion status, steps, and final message
        """
        # Clear history if requested
        if clear_history:
            self.step_history.clear()

        # Create roles
        proposer = Proposer(
            self.llm, task, self.step_history, self.tool_registry, self.llm_browser
        )
        executer = Executer(self.tool_registry)
        verifier = Verifier(self.llm, task, self.step_history, self.llm_browser)

        # Agent loop
        for i in range(max_steps):
            # 1. Propose next action
            action = await proposer.propose()

            # 2. Execute action
            exec_result = await executer.execute(action)

            # 3. Verify if task complete
            verify_result = await verifier.verify(action, exec_result)

            # 4. Create step and add to history
            step = Step(
                proposal=action, execution=exec_result, verification=verify_result
            )
            self.step_history.add_step(step)

            # 5. Check if done
            if verify_result.complete:
                return TaskResult(
                    completed=True,
                    steps=self.step_history.get_all(),
                    message=verify_result.message,
                )

        # Max steps reached without completion
        return TaskResult(
            completed=False,
            steps=self.step_history.get_all(),
            message=f"Task not completed after {max_steps} steps",
        )

    async def navigate(self, url: str):
        """
        Navigate to URL (low-level imperative mode).

        Args:
            url: URL to navigate to
        """
        await self.llm_browser.navigate(url)

    async def select(self, description: str):
        """
        Select element by natural language description (low-level imperative mode).

        Args:
            description: Natural language description of element

        Returns:
            Browser Element with .click(), .fill() methods
        """
        return await self.llm_browser.select(description)
