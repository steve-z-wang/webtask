"""ObserveTool - capture fresh page observation for verification."""

from pydantic import BaseModel
from webtask.agent.tool import Tool


class ObserveParams(BaseModel):
    """Parameters for observe tool."""

    pass


class ObserveTool(Tool):
    """Capture fresh DOM and screenshot for verification."""

    def __init__(self, verifier_browser):
        self.verifier_browser = verifier_browser

    @property
    def name(self) -> str:
        return "observe"

    @property
    def description(self) -> str:
        return "Capture fresh page observation (DOM + screenshot). Use this after waiting or if you need to see the current page state."

    @property
    def Params(self):
        return ObserveParams

    async def execute(self, params: ObserveParams) -> str:
        # Observations will be captured automatically after this tool executes
        # Just return a confirmation
        return "Page observation captured"
