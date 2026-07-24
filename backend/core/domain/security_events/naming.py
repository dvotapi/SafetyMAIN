from __future__ import annotations

import re

_PREFERRED_EVENT_TYPE_PATTERN = re.compile(r"^[a-z]+\.[a-z]+\.[a-z]+$")


def is_preferred_event_type_identifier(event_type: str) -> bool:
    """Return True when identifier follows `<category>.<subject>.<action>`."""
    return bool(_PREFERRED_EVENT_TYPE_PATTERN.fullmatch(event_type))


def validate_event_type_identifier_for_registration(
    event_type: str,
    *,
    legacy_identifier: bool,
) -> None:
    if not event_type:
        raise ValueError("Event type identifier must be non-empty.")
    if event_type != event_type.lower():
        raise ValueError(f"Event type identifier must be lowercase: {event_type!r}.")
    if " " in event_type:
        raise ValueError(f"Event type identifier must not contain spaces: {event_type!r}.")
    if is_preferred_event_type_identifier(event_type):
        return
    if legacy_identifier:
        return
    raise ValueError(
        f"Event type identifier {event_type!r} does not follow the preferred "
        "<category>.<subject>.<action> convention and is not marked legacy."
    )
