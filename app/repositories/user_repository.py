"""Repository for user persistence."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..models.entities import User


class UserRepository:
    """Persist and retrieve user entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_username(self, username: str) -> Optional[User]:
        return self.session.query(User).filter(User.username == username).one_or_none()

    def create_user(
        self, *, username: str, password_hash: str, salt: bytes, encryption_blob: bytes
    ) -> User:
        user = User(
            username=username,
            password_hash=password_hash,
            password_salt=salt,
            encryption_blob=encryption_blob,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def set_hello_enabled(self, user: User, enabled: bool) -> None:
        user.hello_enabled = enabled
        self.session.add(user)
