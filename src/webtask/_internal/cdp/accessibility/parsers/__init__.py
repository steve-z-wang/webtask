"""Parsers for accessibility tree data.

Converts raw CDP accessibility tree data into AXNode intermediate representation.
"""

from .cdp import parse_cdp_accessibility

__all__ = ["parse_cdp_accessibility"]
