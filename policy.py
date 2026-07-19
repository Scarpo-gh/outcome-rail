"""OutcomeRail için sürümlü, deterministik execution politikaları."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from outcomerail_engine import ExecutionReport, Verdict
from polymarket_client import BookSnapshot


def _canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class ExecutionPolicy:
    policy_id: str
    version: str
    max_snapshot_age_seconds: int
    max_spread: Decimal
    max_price_gap: Decimal

    def __post_init__(self) -> None:
        if not self.policy_id or not self.version:
            raise ValueError("policy_id ve version zorunlu")
        if self.max_snapshot_age_seconds <= 0:
            raise ValueError("max_snapshot_age_seconds pozitif olmalı")
        if self.max_spread <= 0 or self.max_price_gap <= 0:
            raise ValueError("price eşikleri pozitif olmalı")

    def to_dict(self) -> dict:
        return {
            "id": self.policy_id,
            "max_price_gap": str(self.max_price_gap),
            "max_snapshot_age_seconds": self.max_snapshot_age_seconds,
            "max_spread": str(self.max_spread),
            "version": self.version,
        }

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PolicyEvaluation:
    report: ExecutionReport
    metrics: dict[str, str | None]


def _parse_timestamp(raw_timestamp: str) -> datetime:
    if not raw_timestamp:
        raise ValueError("snapshot source_timestamp zorunlu")
    try:
        epoch = Decimal(raw_timestamp)
    except Exception:
        epoch = None
    if epoch is not None:
        if epoch >= Decimal("100000000000"):
            epoch /= Decimal("1000")
        return datetime.fromtimestamp(float(epoch), tz=timezone.utc)
    normalized = raw_timestamp.replace("Z", "+00:00")
    timestamp = datetime.fromisoformat(normalized)
    if timestamp.tzinfo is None:
        raise ValueError("timestamp UTC timezone içermeli")
    return timestamp.astimezone(timezone.utc)


def _max_price_gap(levels: tuple[tuple[str, str], ...]) -> Decimal:
    prices = sorted(Decimal(price) for price, size in levels if Decimal(size) > 0)
    return max((right - left for left, right in zip(prices, prices[1:])), default=Decimal("0"))


def evaluate_policy(
    *,
    report: ExecutionReport,
    snapshot: BookSnapshot,
    observed_at: str,
    policy: ExecutionPolicy,
    action: str = "BUY",
) -> PolicyEvaluation:
    """Base raporu yalnız daha temkinli hale getiren deterministik policy katmanı."""
    try:
        observed = _parse_timestamp(observed_at)
        source = _parse_timestamp(snapshot.source_timestamp or "")
        age_seconds = (observed - source).total_seconds()
    except ValueError:
        age_seconds = None

    normalized_action = action.upper()
    if normalized_action not in {"BUY", "SELL"}:
        raise ValueError("action BUY veya SELL olmalı")
    price_gap = _max_price_gap(snapshot.asks if normalized_action == "BUY" else snapshot.bids)
    metrics: dict[str, str | None] = {
        "max_price_gap": str(price_gap),
        "snapshot_age_seconds": str(int(age_seconds)) if age_seconds is not None else None,
        "spread": str(report.spread) if report.spread is not None else None,
    }
    additional_rules: tuple[str, ...] = ()
    verdict = report.verdict
    if age_seconds is None or age_seconds < 0 or age_seconds > policy.max_snapshot_age_seconds:
        verdict = Verdict.BLOCK
        additional_rules = ("STALE_SNAPSHOT",)
    elif report.spread is not None and report.spread > policy.max_spread and verdict is Verdict.PROCEED:
        verdict = Verdict.REDUCE
        additional_rules = ("WIDE_SPREAD",)
    elif price_gap > policy.max_price_gap and verdict is Verdict.PROCEED:
        verdict = Verdict.REDUCE
        additional_rules = ("LARGE_PRICE_GAP",)

    return PolicyEvaluation(
        report=ExecutionReport(
            verdict=verdict,
            executable_size=report.executable_size,
            expected_price=report.expected_price,
            spread=report.spread,
            rule_ids=tuple(dict.fromkeys((*report.rule_ids, *additional_rules))),
        ),
        metrics=metrics,
    )
