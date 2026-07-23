"""Dependency-free, read-only WSGI Analysis API for OutcomeRail."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from analysis_job import AnalysisJobArtifact, run_analysis_job

MAX_BODY_BYTES = 8192


class InvalidRequest(ValueError):
    """Client-input error returned as HTTP 4xx."""

    def __init__(self, message: str, status: str = "400 Bad Request", code: str = "invalid_request"):
        super().__init__(message)
        self.status = status
        self.code = code


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_response(start_response: Callable, status: str, payload: dict[str, Any], headers: list[tuple[str, str]] | None = None):
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    response_headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        *(headers or []),
    ]
    start_response(status, response_headers)
    return [body]


def _serialize(artifact: AnalysisJobArtifact) -> dict[str, Any]:
    return {
        "manifest": {**artifact.manifest.to_dict(), "content_hash": artifact.manifest.content_hash},
        "receipt": artifact.receipt.to_dict(),
        "verified": artifact.verified,
    }


def _parse_payload(environ: dict[str, Any]) -> dict[str, Any]:
    try:
        content_length = int(environ.get("CONTENT_LENGTH", "0"))
    except ValueError as exc:
        raise InvalidRequest("body must be a valid JSON object") from exc
    if content_length < 0:
        raise InvalidRequest("Content-Length cannot be negative")
    if content_length > MAX_BODY_BYTES:
        raise InvalidRequest(
            f"body may be at most {MAX_BODY_BYTES} bytes",
            "413 Payload Too Large",
            "payload_too_large",
        )
    try:
        raw = environ["wsgi.input"].read(content_length)
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidRequest("body must be a valid JSON object") from exc
    if not isinstance(payload, dict):
        raise InvalidRequest("body must be a valid JSON object")
    return payload


def _required_string(payload: Any, field: str) -> str:
    value = payload.get(field) if isinstance(payload, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise InvalidRequest(f"{field} is a required string field")
    return value.strip()


def _validate_action(value: str) -> str:
    if value not in {"BUY", "SELL"}:
        raise InvalidRequest("action must be BUY or SELL", "422 Unprocessable Content")
    return value


def _validate_size(value: Any) -> str:
    if not isinstance(value, str):
        raise InvalidRequest("size must be a positive, finite decimal", "422 Unprocessable Content")
    try:
        size = Decimal(value)
    except InvalidOperation as exc:
        raise InvalidRequest("size must be a positive, finite decimal", "422 Unprocessable Content") from exc
    if not size.is_finite() or size <= 0:
        raise InvalidRequest("size must be a positive, finite decimal", "422 Unprocessable Content")
    return value


def create_app(*, runner: Callable[..., AnalysisJobArtifact] = run_analysis_job, now: Callable[[], str] = _utc_now):
    """Builds the ``POST /v1/analyze`` WSGI application that reads only public data."""

    def app(environ: dict[str, Any], start_response: Callable):
        if environ.get("PATH_INFO") != "/v1/analyze":
            return _json_response(
                start_response,
                "404 Not Found",
                {"error": {"code": "not_found", "message": "path not found"}},
            )
        if environ.get("REQUEST_METHOD") != "POST":
            return _json_response(
                start_response,
                "405 Method Not Allowed",
                {"error": {"code": "method_not_allowed", "message": "only POST is supported"}},
                [("Allow", "POST")],
            )
        try:
            payload = _parse_payload(environ)
            market_id = _required_string(payload, "market_id")
            outcome = _required_string(payload, "outcome")
            action = _validate_action(_required_string(payload, "action"))
            requested_size = _validate_size(payload.get("size"))
        except InvalidRequest as exc:
            return _json_response(
                start_response,
                exc.status,
                {"error": {"code": exc.code, "message": str(exc)}},
            )
        try:
            artifact = runner(
                market_id=market_id,
                outcome=outcome,
                action=action,
                requested_size=requested_size,
                observed_at=now(),
            )
        except LookupError:
            return _json_response(
                start_response,
                "404 Not Found",
                {"error": {"code": "market_or_outcome_not_found", "message": "market or outcome not found"}},
            )
        except OSError:
            return _json_response(
                start_response,
                "502 Bad Gateway",
                {"error": {"code": "public_source_unavailable", "message": "public market data is temporarily unavailable"}},
            )
        except Exception:
            return _json_response(
                start_response,
                "500 Internal Server Error",
                {"error": {"code": "analysis_failed", "message": "analysis could not be completed"}},
            )
        return _json_response(start_response, "200 OK", _serialize(artifact))

    return app
