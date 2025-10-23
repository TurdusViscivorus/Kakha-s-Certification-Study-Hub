"""Import flashcards from bulk pasted text."""
from __future__ import annotations

from typing import Iterable

from .base import CardImporter


class BulkPasteImporter(CardImporter):
    def __init__(self, text: str) -> None:
        self.text = text

    def load(self, _) -> Iterable[dict]:
        for line in self.text.strip().splitlines():
            if "::" in line:
                front, back = line.split("::", 1)
            else:
                front, back = line, ""
            yield {"front": front.strip(), "back": back.strip(), "card_type": "basic", "metadata": {}}
