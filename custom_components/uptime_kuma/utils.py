"""Uptime Kuma utils."""
from __future__ import annotations

import re


def format_entity_name(string: str) -> str:
    """Format entity name."""
    string = re.sub(r"\s+", "_", string)
    string = re.sub(r"\W+", "", string).lower()
    return string
