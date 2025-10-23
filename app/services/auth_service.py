"""Authentication service for the Study Hub."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from ..bootstrap_db import ensure_database
from ..database import session_scope
from ..repositories.user_repository import UserRepository
from ..security import Authenticator, generate_user_keys, unlock_user_key

LOGGER = logging.getLogger(__name__)


@dataclass
class AuthenticatedUser:
    id: int
    username: str
    encryption_key: bytes
    hello_enabled: bool


class AuthService:
    def __init__(self) -> None:
        ensure_database()
        self._authenticator = Authenticator()

    def register(self, username: str, password: str) -> AuthenticatedUser:
        with session_scope() as session:
            repository = UserRepository(session)
            if repository.get_by_username(username):
                raise ValueError("Username already exists")
            password_hash, salt, encryption_blob = generate_user_keys(password)
            user = repository.create_user(
                username=username,
                password_hash=password_hash,
                salt=salt,
                encryption_blob=encryption_blob,
            )
            encryption_key = unlock_user_key(password, user.password_salt, user.encryption_blob)
            LOGGER.info("Created new user %s", username)
            return AuthenticatedUser(
                id=user.id,
                username=user.username,
                encryption_key=encryption_key,
                hello_enabled=user.hello_enabled,
            )

    def authenticate(self, username: str, password: str) -> Optional[AuthenticatedUser]:
        with session_scope() as session:
            repository = UserRepository(session)
            user = repository.get_by_username(username)
            if user is None:
                return None
            if not self._authenticator.verify_password(user.password_hash, user.password_salt, password):
                LOGGER.warning("Failed login attempt for %s", username)
                return None
            encryption_key = unlock_user_key(password, user.password_salt, user.encryption_blob)
            return AuthenticatedUser(
                id=user.id,
                username=user.username,
                encryption_key=encryption_key,
                hello_enabled=user.hello_enabled,
            )

    def update_windows_hello(self, username: str, enabled: bool) -> None:
        with session_scope() as session:
            repository = UserRepository(session)
            user = repository.get_by_username(username)
            if user:
                repository.set_hello_enabled(user, enabled)
                LOGGER.info("Set Windows Hello for %s to %s", username, enabled)
