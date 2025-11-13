

class XPath:

    def __init__(self, path: str):
        self.path = path

    def for_playwright(self) -> str:
        return f"xpath={self.path}"

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"XPath({self.path!r})"
