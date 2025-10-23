"""Security primitives for authentication and encryption."""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Tuple

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import security


@dataclass
class PasswordHashResult:
    hash: str
    salt: bytes


class Authenticator:
    """Handle password hashing and verification."""

    def __init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=security.password_hash_time_cost,
            memory_cost=security.password_hash_memory_cost,
            parallelism=security.password_hash_parallelism,
            hash_len=security.password_hash_hash_len,
            salt_len=security.password_hash_salt_len,
        )

    def hash_password(self, password: str) -> PasswordHashResult:
        salt = os.urandom(security.password_hash_salt_len)
        password_hash = self._hasher.hash(password + base64.urlsafe_b64encode(salt).decode("utf-8"))
        return PasswordHashResult(hash=password_hash, salt=salt)

    def verify_password(self, stored_hash: str, salt: bytes, password: str) -> bool:
        try:
            self._hasher.verify(stored_hash, password + base64.urlsafe_b64encode(salt).decode("utf-8"))
            return True
        except VerifyMismatchError:
            return False


def derive_encryption_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet encryption key from the password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=security.encryption_key_length,
        salt=salt,
        iterations=security.encryption_key_iterations,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key


def generate_user_keys(password: str) -> Tuple[str, bytes, bytes]:
    """Generate a password hash and encryption key materials for a new user."""
    auth = Authenticator()
    password_hash = auth.hash_password(password)
    encryption_salt = os.urandom(16)
    encryption_key = derive_encryption_key(password, encryption_salt)
    fernet = Fernet(encryption_key)
    protected_key = fernet.encrypt(encryption_key)
    return password_hash.hash, password_hash.salt, encryption_salt + protected_key


def unlock_user_key(password: str, salt: bytes, encrypted_key_blob: bytes) -> bytes:
    """Unlock the stored encryption key using the provided password."""
    encryption_salt = encrypted_key_blob[:16]
    ciphertext = encrypted_key_blob[16:]
    derived_key = derive_encryption_key(password, encryption_salt)
    fernet = Fernet(derived_key)
    return fernet.decrypt(ciphertext)


__all__ = [
    "Authenticator",
    "PasswordHashResult",
    "derive_encryption_key",
    "generate_user_keys",
    "unlock_user_key",
]
