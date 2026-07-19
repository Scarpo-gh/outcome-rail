from decimal import Decimal

from analysis_manifest import build_input_manifest
from outcomerail_engine import analyze_execution
from policy import ExecutionPolicy
from polymarket_client import normalize_book
from receipt import build_execution_receipt, snapshot_content_hash, verify_execution_receipt


def _snapshot():
    return normalize_book(
        {
            "asset_id": "yes-token",
            "timestamp": "2026-07-18T12:00:00Z",
            "hash": "clob-book-hash",
            "bids": [{"price": "0.49", "size": "100"}],
            "asks": [{"price": "0.50", "size": "75"}],
        }
    )


def _receipt(input_manifest=None):
    snapshot = _snapshot()
    report = analyze_execution(
        action="BUY",
        bids=snapshot.bids,
        asks=snapshot.asks,
        requested_size="50",
    )
    return build_execution_receipt(
        snapshot=snapshot,
        report=report,
        action="BUY",
        requested_size="50",
        observed_at="2026-07-18T12:00:01Z",
        policy_id="visible-depth",
        policy_version="1.0.0",
        policy=ExecutionPolicy(
            policy_id="visible-depth",
            version="1.0.0",
            max_snapshot_age_seconds=30,
            max_spread=Decimal("0.03"),
            max_price_gap=Decimal("0.02"),
        ),
        policy_metrics=None,
        input_manifest=input_manifest,
        market_id="123",
        outcome="Yes",
    )


def test_receipt_binds_snapshot_policy_and_execution_report():
    receipt = _receipt()
    payload = receipt.to_dict()

    assert verify_execution_receipt(receipt)
    assert payload["schema"] == "outcomerail.execution-receipt.v1"
    assert payload["input"]["snapshot"]["token_id"] == "yes-token"
    assert payload["input"]["snapshot"]["content_hash"] == snapshot_content_hash(_snapshot())
    assert payload["analysis"]["verdict"] == "PROCEED"
    assert payload["policy"]["content_hash"] == ExecutionPolicy(
        policy_id="visible-depth",
        version="1.0.0",
        max_snapshot_age_seconds=30,
        max_spread=Decimal("0.03"),
        max_price_gap=Decimal("0.02"),
    ).content_hash
    assert len(payload["analysis"]["report_hash"]) == 64
    assert len(payload["receipt_hash"]) == 64


def test_receipt_is_deterministic_for_identical_inputs():
    assert _receipt().to_json() == _receipt().to_json()


def test_receipt_verification_rejects_tampered_analysis_or_snapshot():
    tampered_analysis = _receipt().to_dict()
    tampered_analysis["analysis"]["verdict"] = "BLOCK"
    assert verify_execution_receipt(tampered_analysis) is False

    tampered_snapshot = _receipt().to_dict()
    tampered_snapshot["input"]["snapshot"]["content_hash"] = "0" * 64
    assert verify_execution_receipt(tampered_snapshot) is False


def test_receipt_binds_input_manifest_hash():
    manifest = build_input_manifest(
        market_id="123", outcome="Yes", action="BUY", requested_size="50",
        token_id="yes-token", observed_at="2026-07-18T12:00:01Z",
        snapshot_content_hash="a" * 64, policy_content_hash="b" * 64,
    )
    receipt = _receipt(manifest)
    payload = receipt.to_dict()

    assert payload["input"]["manifest_hash"] == manifest.content_hash
    assert verify_execution_receipt(receipt)
