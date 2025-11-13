
from pydantic import BaseModel, Field
from ...tool import Tool


class TypeTool(Tool):

    name = "type"
    description = "Type text into an element character by character with realistic delays (appends to existing text - use fill to replace)"

    class Params(BaseModel):

        element_id: str = Field(description="ID of the element to type into")
        text: str = Field(description="Text to type into the element")

    async def execute(self, params: Params, **kwargs) -> None:
        worker_browser = kwargs.get("worker_browser")
        element = await worker_browser.select(params.element_id)

        # Type text character by character (appends to existing content)
        await element.type(params.text)
