from decimal import Decimal

import pytest

from outcomerail_engine import Verdict, analyze_execution
from policy import ExecutionPolicy, evaluate_policy
from polymarket_client import normalize_book


def test_policy_hash_is_stable_for_identical_thresholds():
    policy = ExecutionPolicy(
        policy_id="visible-depth-guardrails",
        version="1.1.0",
        max_snapshot_age_seconds=30,
        max_spread=Decimal("0.03"),
        max_price_gap=Decimal("0.02"),
    )

    assert policy.content_hash == ExecutionPolicy(
        policy_id="visible-depth-guardrails",
        version="1.1.0",
        max_snapshot_age_seconds=30,
        max_spread=Decimal("0.03"),
        max_price_gap=Decimal("0.02"),
    ).content_hash
    assert len(policy.content_hash) == 64


def test_policy_rejects_negative_or_zero_thresholds():
    with pytest.raises(ValueError):
        ExecutionPolicy(
            policy_id="visible-depth-guardrails",
            version="1.1.0",
            max_snapshot_age_seconds=0,
            max_spread=Decimal("0.03"),
            max_price_gap=Decimal("0.02"),
        )


def test_policy_blocks_stale_snapshot():
    snapshot = normalize_book(
        {
            "asset_id": "yes-token",
            "timestamp": "2026-07-18T12:00:00Z",
            "hash": "book-hash",
            "bids": [{"price": "0.49", "size": "100"}],
            "asks": [{"price": "0.50", "size": "100"}],
        }
    )
    report = analyze_execution(
        action="BUY", bids=snapshot.bids, asks=snapshot.asks, requested_size="10"
    )
    policy = ExecutionPolicy(
        policy_id="visible-depth-guardrails",
        version="1.1.0",
        max_snapshot_age_seconds=30,
        max_spread=Decimal("0.03"),
        max_price_gap=Decimal("0.02"),
    )

    result = evaluate_policy(
        report=report,
        snapshot=snapshot,
        observed_at="2026-07-18T12:01:00Z",
        policy=policy,
    )

    assert result.report.verdict is Verdict.BLOCK
    assert result.report.rule_ids == ("STALE_SNAPSHOT",)
    assert result.metrics["snapshot_age_seconds"] == "60"


def test_policy_reduces_a_fully_fillable_order_with_wide_spread():
    snapshot = normalize_book(
        {
            "asset_id": "yes-token",
            "timestamp": "2026-07-18T12:00:00Z",
            "hash": "book-hash",
            "bids": [{"price": "0.40", "size": "100"}],
            "asks": [{"price": "0.50", "size": "100"}],
        }
    )
    report = analyze_execution(
        action="BUY", bids=snapshot.bids, asks=snapshot.asks, requested_size="10"
    )
    result = evaluate_policy(
        report=report,
        snapshot=snapshot,
        observed_at="2026-07-18T12:00:01Z",
        policy=ExecutionPolicy(
            policy_id="visible-depth-guardrails",
            version="1.1.0",
            max_snapshot_age_seconds=30,
            max_spread=Decimal("0.03"),
            max_price_gap=Decimal("0.02"),
        ),
    )

    assert result.report.verdict is Verdict.REDUCE
    assert result.report.rule_ids == ("WIDE_SPREAD",)
    assert result.metrics["spread"] == "0.10"


def test_policy_reduces_when_requested_side_has_a_large_price_gap():
    snapshot = normalize_book(
        {
            "asset_id": "yes-token",
            "timestamp": "2026-07-18T12:00:00Z",
            "hash": "book-hash",
            "bids": [{"price": "0.49", "size": "100"}],
            "asks": [
                {"price": "0.50", "size": "5"},
                {"price": "0.55", "size": "100"},
            ],
        }
    )
    report = analyze_execution(
        action="BUY", bids=snapshot.bids, asks=snapshot.asks, requested_size="10"
    )
    result = evaluate_policy(
        report=report,
        snapshot=snapshot,
        observed_at="2026-07-18T12:00:01Z",
        action="BUY",
        policy=ExecutionPolicy(
            policy_id="visible-depth-guardrails",
            version="1.1.0",
            max_snapshot_age_seconds=30,
            max_spread=Decimal("0.03"),
            max_price_gap=Decimal("0.02"),
        ),
    )

    assert result.report.verdict is Verdict.REDUCE
    assert result.report.rule_ids == ("LARGE_PRICE_GAP",)
    assert result.metrics["max_price_gap"] == "0.05"


def test_policy_accepts_unix_epoch_source_timestamp_from_clob():
    snapshot = normalize_book(
        {
            "asset_id": "yes-token",
            "timestamp": "1721314200",
            "hash": "book-hash",
            "bids": [{"price": "0.49", "size": "100"}],
            "asks": [{"price": "0.50", "size": "100"}],
        }
    )
    report = analyze_execution(
        action="BUY", bids=snapshot.bids, asks=snapshot.asks, requested_size="10"
    )
    result = evaluate_policy(
        report=report,
        snapshot=snapshot,
        observed_at="2024-07-18T14:50:01Z",
        policy=ExecutionPolicy(
            policy_id="visible-depth-guardrails",
            version="1.1.0",
            max_snapshot_age_seconds=30,
            max_spread=Decimal("0.03"),
            max_price_gap=Decimal("0.02"),
        ),
    )

    assert result.report.verdict is Verdict.PROCEED
    assert result.metrics["snapshot_age_seconds"] == "1"
