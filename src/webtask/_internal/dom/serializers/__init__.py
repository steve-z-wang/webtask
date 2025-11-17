"""DOM serializers - convert DOM trees to different output formats.

Serializers transform DOM trees into various formats (JSON, markdown, etc.)
for output, debugging, or LLM consumption.
"""

from .json import serialize_to_json, serialize_tree_to_json_string

__all__ = [
    "serialize_to_json",
    "serialize_tree_to_json_string",
]
