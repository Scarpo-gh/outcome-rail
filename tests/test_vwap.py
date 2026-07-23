from decimal import Decimal

from outcomerail_engine import (
    Verdict,
    analyze_execution,
    canonical_report_hash,
    estimate_vwap,
)


def test_estimate_vwap_consumes_multiple_price_levels_for_requested_size():
    estimate = estimate_vwap(
        levels=[("0.50", "40"), ("0.52", "60")],
        requested_size="75",
    )

    assert estimate.executable_size == Decimal("75")
    assert estimate.vwap == Decimal("0.5093333333333333333333333333")
    assert estimate.fully_fillable is True


def test_analyze_execution_blocks_when_less_than_half_of_requested_buy_is_visible():
    report = analyze_execution(
        action="BUY",
        bids=[("0.49", "100")],
        asks=[("0.50", "20"), ("0.52", "10")],
        requested_size="75",
    )

    assert report.verdict is Verdict.BLOCK
    assert report.executable_size == Decimal("30")
    assert report.rule_ids == ("INSUFFICIENT_VISIBLE_DEPTH",)


def test_analyze_execution_reduces_when_at_least_half_of_requested_size_is_visible():
    report = analyze_execution(
        action="BUY",
        bids=[("0.49", "100")],
        asks=[("0.50", "40")],
        requested_size="75",
    )

    assert report.verdict is Verdict.REDUCE
    assert report.executable_size == Decimal("40")
    assert report.rule_ids == ("PARTIAL_VISIBLE_DEPTH",)


def test_analyze_execution_returns_expected_price_and_top_of_book_spread():
    report = analyze_execution(
        action="BUY",
        bids=[("0.49", "100")],
        asks=[("0.50", "100")],
        requested_size="10",
    )

    assert report.verdict is Verdict.PROCEED
    assert report.expected_price == Decimal("0.50")
    assert report.spread == Decimal("0.01")


def test_analyze_execution_uses_price_priority_when_book_levels_are_unordered():
    buy = analyze_execution(
        action="BUY",
        bids=[("0.49", "100")],
        asks=[("0.60", "10"), ("0.50", "10")],
        requested_size="10",
    )
    sell = analyze_execution(
        action="SELL",
        bids=[("0.40", "10"), ("0.50", "10")],
        asks=[("0.51", "100")],
        requested_size="10",
    )

    assert buy.expected_price == Decimal("0.50")
    assert sell.expected_price == Decimal("0.50")


def test_canonical_report_hash_is_stable_for_same_report_and_snapshot():
    report = analyze_execution(
        action="SELL",
        bids=[("0.49", "100")],
        asks=[("0.50", "100")],
        requested_size="10",
    )

    first = canonical_report_hash(report, snapshot_timestamp="2026-07-18T12:00:00Z")
    second = canonical_report_hash(report, snapshot_timestamp="2026-07-18T12:00:00Z")

    assert first == second
    assert len(first) == 64
