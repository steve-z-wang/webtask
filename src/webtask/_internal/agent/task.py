"""Task definition - simple container for task description and resources."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Task:
    """Basic task definition with description and optional file resources."""

    description: str
    resources: Dict[str, str] = field(default_factory=dict)
