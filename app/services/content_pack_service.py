"""Manage signed content packs for certifications."""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from cryptography.fernet import Fernet

from ..config import paths
from ..database import session_scope
from ..repositories.content_pack_repository import ContentPackRepository


@dataclass
class ContentPackInfo:
    id: int
    name: str
    version: str
    checksum: str
    metadata: dict


class ContentPackService:
    def __init__(self, encryption_key: bytes) -> None:
        self._fernet = Fernet(encryption_key)
        paths.packs_dir.mkdir(parents=True, exist_ok=True)

    def _checksum(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def install_pack(self, user_id: int, pack_path: Path) -> ContentPackInfo:
        with zipfile.ZipFile(pack_path, "r") as zf:
            manifest_data = json.loads(zf.read("manifest.json"))
            payload = zf.read("payload.bin") if "payload.bin" in zf.namelist() else b""
        checksum = self._checksum(payload)
        encrypted_manifest = self._fernet.encrypt(json.dumps(manifest_data).encode("utf-8"))
        with session_scope() as session:
            repo = ContentPackRepository(session)
            pack = repo.install_pack(
                user_id=user_id,
                name=manifest_data["name"],
                version=manifest_data.get("version", "1.0"),
                checksum=checksum,
                metadata=manifest_data,
                manifest=encrypted_manifest,
            )
            return ContentPackInfo(
                id=pack.id,
                name=pack.name,
                version=pack.version,
                checksum=pack.checksum,
                metadata=manifest_data,
            )

    def list_packs(self, user_id: int) -> List[ContentPackInfo]:
        with session_scope() as session:
            repo = ContentPackRepository(session)
            packs = repo.list_packs(user_id)
            return [
                ContentPackInfo(
                    id=pack.id,
                    name=pack.name,
                    version=pack.version,
                    checksum=pack.checksum,
                    metadata=json.loads(self._fernet.decrypt(pack.manifest).decode("utf-8")),
                )
                for pack in packs
            ]

    def export_pack(self, user_id: int, pack_id: int, destination: Path) -> Path:
        with session_scope() as session:
            repo = ContentPackRepository(session)
            pack = next(p for p in repo.list_packs(user_id) if p.id == pack_id)
            metadata = json.loads(self._fernet.decrypt(pack.manifest).decode("utf-8"))
        payload = json.dumps(metadata.get("items", [])).encode("utf-8")
        checksum = self._checksum(payload)
        with zipfile.ZipFile(destination, "w") as zf:
            zf.writestr("manifest.json", json.dumps(metadata))
            zf.writestr("payload.bin", payload)
            zf.writestr("checksum.txt", checksum)
        return destination
