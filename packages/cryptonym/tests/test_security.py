"""Tests for the security boundary."""

from __future__ import annotations

import pytest

from cryptonym.security import SecurityValidationError, bounded_text, safe_error, validate_service_url


def test_public_endpoint_must_use_https() -> None:
    with pytest.raises(SecurityValidationError, match="HTTPS"):
        validate_service_url("http://example.com")


def test_credentials_in_url_are_rejected() -> None:
    with pytest.raises(SecurityValidationError, match="credentials"):
        validate_service_url("https://user:pass@example.com")


def test_loopback_allowed_only_when_requested() -> None:
    assert validate_service_url("http://127.0.0.1:8080", allow_loopback=True) == "http://127.0.0.1:8080"
    with pytest.raises(SecurityValidationError):
        validate_service_url("http://127.0.0.1:8080")


def test_relative_url_is_rejected() -> None:
    with pytest.raises(SecurityValidationError, match="absolute"):
        validate_service_url("/v1/endpoint")


def test_bounded_text_fails_closed_over_limit() -> None:
    assert bounded_text("ok", "field", 10) == "ok"
    with pytest.raises(SecurityValidationError, match="exceeds"):
        bounded_text("x" * 11, "field", 10)


def test_safe_error_does_not_leak_the_message() -> None:
    message = safe_error("publish failed", ValueError("token=SECRET"))
    assert "SECRET" not in message
    assert message == "publish failed: ValueError"
