
from typing import List, Optional
import base64
from ....llm import LLM
from ....llm.message import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
    ToolResult,
)
from ..agent_browser import AgentBrowser
from ..tool import Tool, ToolRegistry
from .worker_session import WorkerSession


WORKER_SYSTEM_PROMPT = """You are a browser automation worker executing subtasks using pixel-based coordinates.

You can interact with the page using these tools:
- click_at(x, y): Click at normalized coordinates (0-1000)
- hover_at(x, y): Hover at coordinates
- type_text_at(x, y, text): Click and type text
- scroll_document(direction): Scroll the page
- scroll_at(x, y, direction, magnitude): Scroll at coordinates
- navigate(url): Navigate to URL
- key_combination(keys): Press keyboard keys

Coordinates are normalized 0-1000:
- (0, 0) = top-left corner
- (500, 500) = center
- (1000, 1000) = bottom-right corner

You will receive screenshots of the current page. Analyze the visual layout and use appropriate coordinates.

When the subtask is complete, respond without any tool calls to indicate completion."""


class Worker:

    # Configuration constants
    MAX_SCREENSHOTS_TO_KEEP = 2  # Keep only last 2 screenshots in message history

    def __init__(
        self,
        llm: LLM,
        agent_browser: AgentBrowser,
        tools: Optional[List[Tool]] = None,
    ):
        self.llm = llm
        self.agent_browser = agent_browser

        # Setup tool registry
        self.tool_registry = ToolRegistry()
        if tools:
            for tool in tools:
                self.tool_registry.register(tool)
        else:
            # Register default pixel-based tools
            self._register_default_tools()

    def _register_default_tools(self):
        from ..tools.pixel import (
            ClickAtTool,
            HoverAtTool,
            TypeTextAtTool,
            ScrollDocumentTool,
            ScrollAtTool,
            NavigateTool,
            KeyCombinationTool,
        )

        self.tool_registry.register(ClickAtTool())
        self.tool_registry.register(HoverAtTool())
        self.tool_registry.register(TypeTextAtTool())
        self.tool_registry.register(ScrollDocumentTool())
        self.tool_registry.register(ScrollAtTool())
        self.tool_registry.register(NavigateTool())
        self.tool_registry.register(KeyCombinationTool())

    async def run(
        self,
        subtask_description: str,
        max_iterations: int = 10,
    ) -> WorkerSession:
        # Initialize message history
        messages: List[Message] = []

        # Add system message
        messages.append(
            SystemMessage(content=[TextContent(text=WORKER_SYSTEM_PROMPT)])
        )

        # Add initial user message with subtask and screenshot
        initial_screenshot = await self._get_screenshot_base64()
        messages.append(
            UserMessage(
                content=[
                    TextContent(text=f"Subtask: {subtask_description}"),
                    ImageContent(data=initial_screenshot, mime_type="image/png"),
                ]
            )
        )

        # Execution loop
        iteration_count = 0
        for iteration in range(max_iterations):
            iteration_count = iteration + 1

            # Filter screenshots before calling LLM
            filtered_messages = self._filter_screenshots(
                messages, self.MAX_SCREENSHOTS_TO_KEEP
            )

            # Call LLM with tools
            try:
                assistant_msg = await self.llm.generate(
                    messages=filtered_messages, tools=self.tool_registry.get_all()
                )
            except Exception as e:
                return WorkerSession(
                    subtask_description=subtask_description,
                    status="failed",
                    message_history=messages,
                    iterations_count=iteration_count,
                    final_url=await self._get_current_url(),
                    error=f"LLM call failed: {str(e)}",
                )

            messages.append(assistant_msg)

            # Check if task is complete (no tool calls)
            if not assistant_msg.tool_calls:
                return WorkerSession(
                    subtask_description=subtask_description,
                    status="completed",
                    message_history=messages,
                    iterations_count=iteration_count,
                    final_url=await self._get_current_url(),
                )

            # Execute tool calls
            tool_results = []
            for tool_call in assistant_msg.tool_calls:
                try:
                    # Execute tool
                    result_text = await self._execute_tool_call(tool_call)

                    # Get new page state after tool execution
                    screenshot = await self._get_screenshot_base64()
                    current_url = await self._get_current_url()

                    # Create tool result with screenshot
                    tool_results.append(
                        ToolResult(
                            name=tool_call.name,
                            content=[
                                TextContent(text=f"Result: {result_text}\nURL: {current_url}"),
                                ImageContent(data=screenshot, mime_type="image/png"),
                            ],
                        )
                    )
                except Exception as e:
                    # Tool execution failed
                    tool_results.append(
                        ToolResult(
                            name=tool_call.name,
                            content=[TextContent(text=f"Error: {str(e)}")],
                        )
                    )

            # Add tool results to history
            messages.append(ToolResultMessage(results=tool_results))

        # Max iterations reached
        return WorkerSession(
            subtask_description=subtask_description,
            status="max_iterations",
            message_history=messages,
            iterations_count=iteration_count,
            final_url=await self._get_current_url(),
        )

    async def _execute_tool_call(self, tool_call) -> str:
        # Get current page
        page = self.agent_browser.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently active. Use navigate tool to open a page.")

        tool = self.tool_registry.get(tool_call.name)

        # Validate and create params
        params = tool.Params(**tool_call.arguments)

        # Execute tool with page
        result = await tool.execute(params, page=page)

        return str(result)

    async def _get_screenshot_base64(self) -> str:
        page = self.agent_browser.get_current_page()
        if page is None:
            return ""  # Return empty if no page

        screenshot_bytes = await page.screenshot(full_page=False)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def _get_current_url(self) -> str:
        page = self.agent_browser.get_current_page()
        if page is None:
            return "about:blank"  # Return default if no page

        return page.url

    def _filter_screenshots(
        self, messages: List[Message], keep_last_n: int
    ) -> List[Message]:
        if keep_last_n <= 0:
            # Remove all screenshots
            return self._remove_all_screenshots(messages)

        # Find indices of ToolResultMessages with screenshots
        screenshot_indices = []
        for i, msg in enumerate(messages):
            if isinstance(msg, ToolResultMessage):
                # Check if any result has ImageContent
                has_screenshot = any(
                    isinstance(content, ImageContent)
                    for result in msg.results
                    for content in result.content
                )
                if has_screenshot:
                    screenshot_indices.append(i)

        # Keep all if under limit
        if len(screenshot_indices) <= keep_last_n:
            return messages

        # Determine which to remove (keep last N)
        remove_indices = set(screenshot_indices[:-keep_last_n])

        # Create filtered message list
        filtered = []
        for i, msg in enumerate(messages):
            if i in remove_indices:
                # Remove screenshots from this ToolResultMessage
                filtered_results = []
                for result in msg.results:
                    filtered_content = [
                        c for c in result.content if not isinstance(c, ImageContent)
                    ]
                    if filtered_content:  # Only add if there's content left
                        filtered_results.append(
                            ToolResult(name=result.name, content=filtered_content)
                        )
                if filtered_results:  # Only add message if it has results
                    filtered.append(ToolResultMessage(results=filtered_results))
            else:
                filtered.append(msg)

        return filtered

    def _remove_all_screenshots(self, messages: List[Message]) -> List[Message]:
        filtered = []
        for msg in messages:
            if isinstance(msg, UserMessage) and msg.content:
                # Keep text, remove images
                filtered_content = [
                    c for c in msg.content if not isinstance(c, ImageContent)
                ]
                if filtered_content:
                    filtered.append(UserMessage(content=filtered_content))
            elif isinstance(msg, ToolResultMessage):
                # Remove screenshots from results
                filtered_results = []
                for result in msg.results:
                    filtered_content = [
                        c for c in result.content if not isinstance(c, ImageContent)
                    ]
                    if filtered_content:
                        filtered_results.append(
                            ToolResult(name=result.name, content=filtered_content)
                        )
                if filtered_results:
                    filtered.append(ToolResultMessage(results=filtered_results))
            else:
                # Keep other message types as-is
                filtered.append(msg)

        return filtered
