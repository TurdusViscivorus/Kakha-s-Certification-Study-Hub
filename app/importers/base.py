"""Importer interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable


class CardImporter(ABC):
    """Base importer contract."""

    @abstractmethod
    def load(self, path: Path) -> Iterable[dict]:
        raise NotImplementedError
