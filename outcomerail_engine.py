"""OutcomeRail'in deterministik orderbook execution-quality hesapları."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable


@dataclass(frozen=True)
class VwapEstimate:
    executable_size: Decimal
    vwap: Decimal | None
    fully_fillable: bool


class Verdict(str, Enum):
    PROCEED = "PROCEED"
    REDUCE = "REDUCE"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class ExecutionReport:
    verdict: Verdict
    executable_size: Decimal
    expected_price: Decimal | None
    spread: Decimal | None
    rule_ids: tuple[str, ...]


def analyze_execution(
    *,
    action: str,
    bids: Iterable[tuple[str, str]],
    asks: Iterable[tuple[str, str]],
    requested_size: str,
) -> ExecutionReport:
    """Görünür defter derinliğine göre BUY/SELL uygulanabilirliğini değerlendirir."""
    normalized_action = action.upper()
    if normalized_action not in {"BUY", "SELL"}:
        raise ValueError("action BUY veya SELL olmalı")

    bid_levels = tuple(bids)
    ask_levels = tuple(asks)
    estimate = estimate_vwap(
        ask_levels if normalized_action == "BUY" else bid_levels, requested_size
    )
    valid_bids = [Decimal(price) for price, size in bid_levels if Decimal(size) > 0]
    valid_asks = [Decimal(price) for price, size in ask_levels if Decimal(size) > 0]
    spread = min(valid_asks) - max(valid_bids) if valid_bids and valid_asks else None
    requested = Decimal(requested_size)
    if not estimate.fully_fillable:
        if estimate.executable_size * 2 >= requested:
            return ExecutionReport(
                verdict=Verdict.REDUCE,
                executable_size=estimate.executable_size,
                expected_price=estimate.vwap,
                spread=spread,
                rule_ids=("PARTIAL_VISIBLE_DEPTH",),
            )
        return ExecutionReport(
            verdict=Verdict.BLOCK,
            executable_size=estimate.executable_size,
            expected_price=estimate.vwap,
            spread=spread,
            rule_ids=("INSUFFICIENT_VISIBLE_DEPTH",),
        )
    return ExecutionReport(
        verdict=Verdict.PROCEED,
        executable_size=estimate.executable_size,
        expected_price=estimate.vwap,
        spread=spread,
        rule_ids=(),
    )


def estimate_vwap(
    levels: Iterable[tuple[str, str]], requested_size: str
) -> VwapEstimate:
    """İstenen kontrat büyüklüğünü sıralı fiyat seviyelerinde simüle eder."""
    requested = Decimal(requested_size)
    if requested <= 0:
        raise ValueError("requested_size pozitif olmalı")

    remaining = requested
    notional = Decimal("0")
    executable = Decimal("0")
    for raw_price, raw_size in levels:
        if remaining <= 0:
            break
        price = Decimal(raw_price)
        available = Decimal(raw_size)
        if price <= 0 or available <= 0:
            continue
        fill = min(available, remaining)
        executable += fill
        notional += fill * price
        remaining -= fill

    return VwapEstimate(
        executable_size=executable,
        vwap=(notional / executable) if executable else None,
        fully_fillable=remaining == 0,
    )


def canonical_report_hash(report: ExecutionReport, *, snapshot_timestamp: str) -> str:
    """Rapor kanıtını hash'lemek için sürümlenebilir, deterministik payload üretir."""
    payload = {
        "expected_price": str(report.expected_price) if report.expected_price is not None else None,
        "executable_size": str(report.executable_size),
        "rule_ids": list(report.rule_ids),
        "snapshot_timestamp": snapshot_timestamp,
        "spread": str(report.spread) if report.spread is not None else None,
        "verdict": report.verdict.value,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
