"""Import basic cards from Anki .apkg collections."""
from __future__ import annotations

import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable

from .base import CardImporter


class AnkiImporter(CardImporter):
    def load(self, path: Path) -> Iterable[dict]:
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(path, "r") as archive:
                archive.extractall(temp_dir)
            collection_path = Path(temp_dir) / "collection.anki2"
            if not collection_path.exists():
                return []
            connection = sqlite3.connect(collection_path)
            cursor = connection.cursor()
            model_map = self._load_models_from_db(cursor)
            cursor.execute("SELECT flds, mid FROM notes")
            for fields_raw, model_id in cursor.fetchall():
                fields = fields_raw.split("\x1f")
                front = fields[0]
                back = fields[1] if len(fields) > 1 else ""
                model = model_map.get(str(model_id), {})
                yield {
                    "front": front,
                    "back": back,
                    "card_type": model.get("type", "basic"),
                    "metadata": {"model": model.get("name", "Unknown")},
                }
            connection.close()

    def _load_models_from_db(self, cursor) -> dict:
        cursor.execute("SELECT models FROM col")
        row = cursor.fetchone()
        if not row:
            return {}
        models = json.loads(row[0])
        return models
