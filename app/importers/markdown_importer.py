"""Import flashcards from Markdown format."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .base import CardImporter

CARD_PATTERN = re.compile(r"^#\s*(?P<title>.+)$", re.MULTILINE)
SEPARATOR = "---"


class MarkdownImporter(CardImporter):
    def load(self, path: Path) -> Iterable[dict]:
        text = path.read_text(encoding="utf-8")
        cards = text.split(SEPARATOR)
        for block in cards:
            lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
            if not lines:
                continue
            front = lines[0]
            back = "\n".join(lines[1:]) if len(lines) > 1 else ""
            yield {"front": front, "back": back, "card_type": "basic", "metadata": {"format": "markdown"}}
