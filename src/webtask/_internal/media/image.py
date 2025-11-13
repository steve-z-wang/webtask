
import base64


class Image:

    def __init__(self, data: bytes, format: str = "png"):
        self._data = data
        self._format = format

    def to_base64(self) -> str:
        return base64.b64encode(self._data).decode("utf-8")

    def to_data_url(self) -> str:
        b64 = self.to_base64()
        return f"data:image/{self._format};base64,{b64}"

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            f.write(self._data)

    def to_bytes(self) -> bytes:
        return self._data

    @property
    def format(self) -> str:
        return self._format

    @property
    def size(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"Image(format={self._format}, size={self.size} bytes)"
