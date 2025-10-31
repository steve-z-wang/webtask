"""Parsers for HTML and CDP snapshots."""

from .html import parse_html
from .cdp import parse_cdp

__all__ = ["parse_html", "parse_cdp"]
