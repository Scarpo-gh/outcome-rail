from __future__ import annotations

import io
import json

import pytest

from analysis_job import run_analysis_job
from polymarket_client import normalize_book


def _request(
    app,
    *,
    method: str = "POST",
    path: str = "/v1/analyze",
    payload: bytes = b"{}",
    content_type: str = "application/json",
    content_length: str | None = None,
):
    captured: dict[str, object] = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    response = app(
        {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "CONTENT_LENGTH": str(len(payload)) if content_length is None else content_length,
            "CONTENT_TYPE": content_type,
            "wsgi.input": io.BytesIO(payload),
        },
        start_response,
    )
    return captured["status"], dict(captured["headers"]), json.loads(b"".join(response))


def test_analyze_endpoint_returns_verified_read_only_artifact_without_evidence_log():
    from api import create_app

    snapshot = normalize_book(
        {
            "asset_id": "yes-token",
            "timestamp": "2026-07-19T17:10:00Z",
            "hash": "book-hash",
            "bids": [{"price": "0.49", "size": "100"}],
            "asks": [{"price": "0.50", "size": "100"}],
        }
    )
    calls: list[dict] = []

    def runner(**kwargs):
        calls.append(kwargs)
        return run_analysis_job(
            **kwargs,
            token_resolver=lambda market_id, outcome: "yes-token",
            book_fetcher=lambda token_id: snapshot,
        )

    app = create_app(runner=runner, now=lambda: "2026-07-19T17:10:01Z")
    status, headers, body = _request(
        app,
        payload=json.dumps({"market_id": "123", "outcome": "Yes", "action": "BUY", "size": "10"}).encode(),
    )

    assert status == "200 OK"
    assert headers["Content-Type"].startswith("application/json")
    assert body["verified"] is True
    assert body["manifest"]["content_hash"] == body["receipt"]["input"]["manifest_hash"]
    assert "evidence_entry" not in body
    assert "evidence_log_path" not in calls[0]


def test_analyze_endpoint_rejects_non_positive_size_before_runner():
    from api import create_app

    called = False

    def runner(**kwargs):
        nonlocal called
        called = True
        raise AssertionError("runner should not be called")

    app = create_app(runner=runner)
    status, _, body = _request(
        app,
        payload=json.dumps({"market_id": "123", "outcome": "Yes", "action": "BUY", "size": "0"}).encode(),
    )

    assert status == "422 Unprocessable Content"
    assert body == {"error": {"code": "invalid_request", "message": "size must be a positive, finite decimal"}}
    assert called is False


def test_analyze_endpoint_rejects_missing_required_field():
    from api import create_app

    app = create_app(runner=lambda **kwargs: (_ for _ in ()).throw(AssertionError("runner should not be called")))
    status, _, body = _request(app, payload=json.dumps({"outcome": "Yes", "action": "BUY", "size": "10"}).encode())

    assert status == "400 Bad Request"
    assert body == {"error": {"code": "invalid_request", "message": "market_id is a required string field"}}


def test_analyze_endpoint_rejects_unsupported_action_before_runner():
    from api import create_app

    app = create_app(runner=lambda **kwargs: (_ for _ in ()).throw(AssertionError("runner should not be called")))
    status, _, body = _request(
        app,
        payload=json.dumps({"market_id": "123", "outcome": "Yes", "action": "HOLD", "size": "10"}).encode(),
    )

    assert status == "422 Unprocessable Content"
    assert body == {"error": {"code": "invalid_request", "message": "action must be BUY or SELL"}}


def test_analyze_endpoint_rejects_malformed_json_before_runner():
    from api import create_app

    app = create_app(runner=lambda **kwargs: (_ for _ in ()).throw(AssertionError("runner should not be called")))
    status, _, body = _request(app, payload=b"{")

    assert status == "400 Bad Request"
    assert body == {"error": {"code": "invalid_request", "message": "body must be a valid JSON object"}}


def test_analyze_endpoint_allows_only_post_to_versioned_path():
    from api import create_app

    app = create_app(runner=lambda **kwargs: (_ for _ in ()).throw(AssertionError("runner should not be called")))
    status, headers, body = _request(app, method="GET")

    assert status == "405 Method Not Allowed"
    assert headers["Allow"] == "POST"
    assert body == {"error": {"code": "method_not_allowed", "message": "only POST is supported"}}


def test_analyze_endpoint_rejects_body_larger_than_8_kib_before_parsing():
    from api import create_app

    app = create_app(runner=lambda **kwargs: (_ for _ in ()).throw(AssertionError("runner should not be called")))
    status, _, body = _request(app, payload=b"x" * 8193)

    assert status == "413 Payload Too Large"
    assert body == {"error": {"code": "payload_too_large", "message": "body en fazla 8192 byte olabilir"}}


def test_api_returns_404_for_other_paths_before_parsing():
    from api import create_app

    app = create_app(runner=lambda **kwargs: (_ for _ in ()).throw(AssertionError("runner should not be called")))
    status, _, body = _request(app, path="/v1/other", payload=b"{")

    assert status == "404 Not Found"
    assert body == {"error": {"code": "not_found", "message": "path not found"}}


def test_local_server_cli_defaults_to_loopback_and_port_8080():
    from scripts.serve_api import parse_args

    args = parse_args([])

    assert args.host == "127.0.0.1"
    assert args.port == 8080


@pytest.mark.parametrize("host", ["0.0.0.0", "::1"])
def test_local_server_cli_rejects_non_loopback_host(host):
    from scripts.serve_api import parse_args

    with pytest.raises(SystemExit):
        parse_args(["--host", host])


def test_analyze_endpoint_maps_market_lookup_error_without_leaking_details():
    from api import create_app

    def runner(**kwargs):
        raise LookupError("internal upstream detail")

    app = create_app(runner=runner)
    status, _, body = _request(
        app,
        payload=json.dumps({"market_id": "missing", "outcome": "Yes", "action": "BUY", "size": "10"}).encode(),
    )

    assert status == "404 Not Found"
    assert body == {"error": {"code": "market_or_outcome_not_found", "message": "market or outcome not found"}}


def test_analyze_endpoint_maps_public_source_error_without_leaking_details():
    from api import create_app

    app = create_app(runner=lambda **kwargs: (_ for _ in ()).throw(OSError("upstream hostname detail")))
    status, _, body = _request(
        app,
        payload=json.dumps({"market_id": "123", "outcome": "Yes", "action": "BUY", "size": "10"}).encode(),
    )

    assert status == "502 Bad Gateway"
    assert body == {"error": {"code": "public_source_unavailable", "message": "public market data is temporarily unavailable"}}


def test_analyze_endpoint_rejects_negative_content_length_before_reading_body():
    from api import create_app

    app = create_app(runner=lambda **kwargs: (_ for _ in ()).throw(AssertionError("runner should not be called")))
    status, _, body = _request(
        app,
        payload=json.dumps({"market_id": "123", "outcome": "Yes", "action": "BUY", "size": "10"}).encode(),
        content_length="-1",
    )

    assert status == "400 Bad Request"
    assert body == {"error": {"code": "invalid_request", "message": "Content-Length negatif olamaz"}}


def test_analyze_endpoint_hides_unexpected_runner_error():
    from api import create_app

    app = create_app(runner=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("internal implementation detail")))
    status, _, body = _request(
        app,
        payload=json.dumps({"market_id": "123", "outcome": "Yes", "action": "BUY", "size": "10"}).encode(),
    )

    assert status == "500 Internal Server Error"
    assert body == {"error": {"code": "analysis_failed", "message": "analysis could not be completed"}}
