"""Import flashcards from CSV or TSV."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .base import CardImporter


class DelimitedImporter(CardImporter):
    def __init__(self, delimiter: str = ",") -> None:
        self.delimiter = delimiter

    def load(self, path: Path) -> Iterable[dict]:
        with path.open("r", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle, delimiter=self.delimiter)
            for row in reader:
                yield {
                    "front": row.get("front") or row.get("prompt"),
                    "back": row.get("back") or row.get("answer"),
                    "card_type": row.get("type", "basic"),
                    "metadata": {key: value for key, value in row.items() if key not in {"front", "back", "type"}},
                }


CSVImporter = DelimitedImporter
TSVImporter = lambda: DelimitedImporter("\t")
