from __future__ import annotations

import logging

from backend.bootstrap.settings import AppSettings

logger = logging.getLogger("safetymain.bootstrap")
_LOGGED_SECURITY_CONFIGURATION = False


def log_security_configuration(settings: AppSettings) -> None:
    """Log non-sensitive security configuration once at startup."""

    global _LOGGED_SECURITY_CONFIGURATION
    if _LOGGED_SECURITY_CONFIGURATION:
        return

    logger.info(
        "Security configuration validated: app_env=%s jwt_algorithm=%s "
        "jwt_issuer_configured=%s auth_enforcement=%s",
        settings.app_env,
        settings.jwt_algorithm,
        settings.jwt_issuer is not None,
        settings.auth_enforcement,
    )
    _LOGGED_SECURITY_CONFIGURATION = True
