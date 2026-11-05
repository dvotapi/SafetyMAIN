from __future__ import annotations

import pytest

from backend.core.domain.value_objects.compliance_enums import SafetyDomain


def test_safety_domain_values() -> None:
    assert [member.value for member in SafetyDomain] == [
        "occupational",
        "industrial",
        "transport_security",
        "fire",
        "environmental",
        "road",
        "dangerous_goods",
    ]


def test_transport_security_replaces_labour() -> None:
    """«ТрБез» is transport security (16-ФЗ); `labour` was a mistranslation."""
    assert SafetyDomain("transport_security") is SafetyDomain.TRANSPORT_SECURITY
    with pytest.raises(ValueError):
        SafetyDomain("labour")
