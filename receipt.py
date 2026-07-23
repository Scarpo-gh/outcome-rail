"""Off-chain, verifiable receipt generation for OutcomeRail analysis results.

This module performs no financial settlement, custody, or on-chain transaction. It binds a CLOB
snapshot, the applied policy, and an execution-quality verdict into one canonical
payload, so the same analysis can be independently verified later.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from analysis_manifest import AnalysisInputManifest
from outcomerail_engine import ExecutionReport, canonical_report_hash
from policy import ExecutionPolicy
from polymarket_client import BookSnapshot

SCHEMA_VERSION = "outcomerail.execution-receipt.v1"


class ReceiptIntegrityError(ValueError):
    """Raised when the receipt schema or integrity is invalid."""


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def snapshot_content_hash(snapshot: BookSnapshot) -> str:
    """Local evidence hash of all fetched levels, independent of the CLOB-provided hash."""
    return _sha256(
        {
            "asks": [list(level) for level in snapshot.asks],
            "bids": [list(level) for level in snapshot.bids],
            "source_book_hash": snapshot.book_hash,
            "source_timestamp": snapshot.source_timestamp,
            "token_id": snapshot.token_id,
        }
    )


@dataclass(frozen=True)
class ExecutionReceipt:
    """Self-verifiable immutable receipt containing only analysis evidence."""

    payload: dict[str, Any]
    receipt_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload, "receipt_hash": self.receipt_hash}

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())


def build_execution_receipt(
    *,
    snapshot: BookSnapshot,
    report: ExecutionReport,
    action: str,
    requested_size: str,
    observed_at: str,
    policy_id: str,
    policy_version: str,
    policy: ExecutionPolicy | None = None,
    policy_metrics: dict[str, str | None] | None = None,
    input_manifest: AnalysisInputManifest | None = None,
    market_id: str | None = None,
    outcome: str | None = None,
) -> ExecutionReceipt:
    """Binds an execution-quality report to its source snapshot and policy.

    ``observed_at`` must be the caller’s UTC ISO-8601 time. The CLOB source time
    is retained separately when available; it is not replaced when absent.
    """
    normalized_action = action.upper()
    if normalized_action not in {"BUY", "SELL"}:
        raise ReceiptIntegrityError("action must be BUY or SELL")
    if Decimal(requested_size) <= 0:
        raise ReceiptIntegrityError("requested_size must be positive")
    if not observed_at or not policy_id or not policy_version:
        raise ReceiptIntegrityError("observed_at, policy_id, and policy_version are required")
    if not snapshot.token_id:
        raise ReceiptIntegrityError("snapshot token_id is required")

    if policy and (policy_id != policy.policy_id or policy_version != policy.version):
        raise ReceiptIntegrityError("policy_id/version must match the supplied policy")

    report_timestamp = snapshot.source_timestamp or observed_at
    policy_payload = {"id": policy_id, "version": policy_version}
    if policy:
        policy_payload["content_hash"] = policy.content_hash
        policy_payload["thresholds"] = policy.to_dict()
    if policy_metrics is not None:
        policy_payload["metrics"] = policy_metrics
    payload = {
        "analysis": {
            "executable_size": str(report.executable_size),
            "expected_price": str(report.expected_price) if report.expected_price is not None else None,
            "report_hash": canonical_report_hash(report, snapshot_timestamp=report_timestamp),
            "rule_ids": list(report.rule_ids),
            "spread": str(report.spread) if report.spread is not None else None,
            "verdict": report.verdict.value,
        },
        "input": {
            "action": normalized_action,
            "market_id": market_id,
            "manifest_hash": input_manifest.content_hash if input_manifest else None,
            "outcome": outcome,
            "requested_size": requested_size,
            "snapshot": {
                "content_hash": snapshot_content_hash(snapshot),
                "source_book_hash": snapshot.book_hash,
                "source_timestamp": snapshot.source_timestamp,
                "token_id": snapshot.token_id,
            },
        },
        "observed_at": observed_at,
        "policy": policy_payload,
        "scope": "execution-quality-only; no trade, custody, settlement, or profitability claim",
        "schema": SCHEMA_VERSION,
    }
    return ExecutionReceipt(payload=payload, receipt_hash=_sha256(payload))


def verify_execution_receipt(receipt: dict[str, Any] | ExecutionReceipt) -> bool:
    """Verifies the receipt schema version and integrity of the full payload."""
    serialized = receipt.to_dict() if isinstance(receipt, ExecutionReceipt) else receipt
    if not isinstance(serialized, dict):
        return False
    supplied_hash = serialized.get("receipt_hash")
    payload = {key: value for key, value in serialized.items() if key != "receipt_hash"}
    return (
        payload.get("schema") == SCHEMA_VERSION
        and isinstance(supplied_hash, str)
        and supplied_hash == _sha256(payload)
    )
