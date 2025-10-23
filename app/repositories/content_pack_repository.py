"""Repository for managing content packs."""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from ..models.entities import ContentPack


class ContentPackRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def install_pack(
        self, *, user_id: int, name: str, version: str, checksum: str, metadata: dict, manifest: bytes
    ) -> ContentPack:
        pack = ContentPack(
            user_id=user_id,
            name=name,
            version=version,
            checksum=checksum,
            metadata=metadata,
            manifest=manifest,
        )
        self.session.add(pack)
        self.session.flush()
        return pack

    def list_packs(self, user_id: int) -> List[ContentPack]:
        return self.session.query(ContentPack).filter(ContentPack.user_id == user_id).all()
