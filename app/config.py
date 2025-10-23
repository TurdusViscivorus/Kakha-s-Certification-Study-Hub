"""Application configuration for Kakha's Certification Study Hub."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    """Path configuration for runtime artifacts."""

    root: Path = Path.home() / ".kakha_study_hub"

    @property
    def database(self) -> Path:
        return self.root / "study_hub.db"

    @property
    def log_file(self) -> Path:
        return self.root / "study_hub.log"

    @property
    def packs_dir(self) -> Path:
        return self.root / "content_packs"

    @property
    def attachments_dir(self) -> Path:
        return self.root / "attachments"


@dataclass(frozen=True)
class SecurityConfig:
    """Security-related configuration values."""

    password_hash_time_cost: int = 3
    password_hash_memory_cost: int = 2 ** 15
    password_hash_parallelism: int = 2
    password_hash_hash_len: int = 32
    password_hash_salt_len: int = 16
    encryption_key_iterations: int = 390_000
    encryption_key_length: int = 32


paths = Paths()
security = SecurityConfig()
