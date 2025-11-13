
from typing import Dict
from webtask._internal.dom.domnode import DomNode
from webtask._internal.llm import Block
from ..agent_browser import AgentBrowser
from ...page_context import PageContextBuilder


class WorkerBrowser:

    def __init__(self, agent_browser: AgentBrowser):
        self._agent_browser = agent_browser
        self._element_map: Dict[str, DomNode] = {}

    async def get_context(
        self,
        include_element_ids: bool = True,
        with_bounding_boxes: bool = True,
        full_page: bool = False,
        debug_filename: str = None,
    ) -> Block:
        page = self._agent_browser.get_current_page()
        if page is None:
            self._element_map = {}
            return Block(
                heading="Current Page",
                content="ERROR: No page opened yet.\nPlease use the navigate tool to navigate to a URL.",
            )

        block, element_map = await PageContextBuilder.build(
            page=page,
            include_element_ids=include_element_ids,
            with_bounding_boxes=with_bounding_boxes,
            full_page_screenshot=full_page,
            debug_filename=debug_filename,
        )

        self._element_map = element_map if element_map else {}
        return block

    def _get_xpath(self, element_id: str):
        if element_id not in self._element_map:
            raise KeyError(f"Element ID '{element_id}' not found")

        node = self._element_map[element_id]
        return node.get_x_path()

    async def select(self, element_id: str):
        page = self._agent_browser.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")

        xpath = self._get_xpath(element_id)
        return await page.select_one(xpath)

    async def click(self, element_id: str) -> None:
        element = await self.select(element_id)
        await element.click()

    async def fill(self, element_id: str, value: str) -> None:
        element = await self.select(element_id)
        await element.fill(value)

    async def type(self, element_id: str, text: str) -> None:
        element = await self.select(element_id)
        await element.type(text)

    async def upload(self, element_id: str, file_path: str) -> None:
        element = await self.select(element_id)
        await element.upload_file(file_path)

    async def navigate(self, url: str) -> None:
        await self._agent_browser.navigate(url)
        self._element_map.clear()

    async def wait_for_idle(self, timeout: int = 30000) -> None:
        await self._agent_browser.wait_for_idle(timeout=timeout)
