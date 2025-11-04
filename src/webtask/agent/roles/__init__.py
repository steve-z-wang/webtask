"""Agent roles - different specialized behaviors for the agent."""

from .base_role import BaseRole, ActionResult
from .verifier import VerifierRole
from .proposer import ProposerRole

__all__ = [
    "BaseRole",
    "ActionResult",
    "VerifierRole",
    "ProposerRole",
]
