from __future__ import annotations

import logging


_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    """Configure basic application logging once.

    Secrets and full database URLs must never be logged by call sites.
    """

    global _CONFIGURED
    if _CONFIGURED:
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    _CONFIGURED = True


def get_logger(name: str = "safetymain.api") -> logging.Logger:
    return logging.getLogger(name)
