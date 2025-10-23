"""Optional Windows Hello integration."""
from __future__ import annotations

import logging

LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover - only available on Windows
    from winrt.windows.security.credentials.ui import UserConsentVerifier
except ImportError:  # pragma: no cover - gracefully degrade
    UserConsentVerifier = None  # type: ignore


def is_available() -> bool:
    if UserConsentVerifier is None:
        return False
    try:
        availability = UserConsentVerifier.check_availability_async().get()
        return availability == UserConsentVerifier.Availability.AVAILABLE
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("Windows Hello availability check failed: %s", exc)
        return False


def request_consent(reason: str) -> bool:
    if UserConsentVerifier is None:
        return False
    try:
        result = UserConsentVerifier.request_verification_async(reason).get()
        return result == UserConsentVerifier.VerificationResult.VERIFIED
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("Windows Hello verification failed: %s", exc)
        return False
