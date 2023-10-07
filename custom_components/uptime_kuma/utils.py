"""Uptime Kuma utils."""
from __future__ import annotations

import re
from urllib.parse import urlparse


def format_entity_name(string: str) -> str:
    """Format entity name."""
    string = re.sub(r"\s+", "_", string)
    string = re.sub(r"\W+", "", string).lower()
    return string

def sensor_name_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    clean_url = parsed_url.netloc.replace(":"+str(parsed_url.port), "")
    return re.sub(r"\W+", "_", clean_url)