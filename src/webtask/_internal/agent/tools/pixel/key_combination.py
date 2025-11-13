
from typing import TYPE_CHECKING, List
from pydantic import BaseModel, Field
from ...tool import Tool

if TYPE_CHECKING:
    from webtask._internal.browser import Page


class KeyCombinationTool(Tool):

    name = "key_combination"
    description = 'Press keyboard keys and combinations, such as "Control+C", "Enter", "Escape", etc.'

    class Params(BaseModel):
        keys: str = Field(
            description='Key combination separated by + (e.g., "Control+C", "Meta+V", "Enter")'
        )

    async def execute(self, params: Params, page: "Page") -> str:
        # Split keys by +
        keys = [k.strip() for k in params.keys.split("+")]

        if len(keys) == 1:
            # Single key press
            await page.keyboard_press(keys[0])
        else:
            # Key combination - hold modifiers and press last key
            modifiers = keys[:-1]
            key = keys[-1]

            # Press and hold modifiers
            for mod in modifiers:
                await page.keyboard_down(mod)

            # Press the key
            await page.keyboard_press(key)

            # Release modifiers
            for mod in reversed(modifiers):
                await page.keyboard_up(mod)

        return f"Pressed key combination: {params.keys}"
