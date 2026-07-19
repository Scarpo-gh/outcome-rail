"""Public Polymarket request'lerini read-only OutcomeRail artifact'ine dönüştürür."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Callable

from evidence_log import append_evidence
from analysis_manifest import AnalysisInputManifest, build_input_manifest
from outcomerail_engine import analyze_execution
from policy import ExecutionPolicy, evaluate_policy
from polymarket_client import BookSnapshot, fetch_book, resolve_token_id
from receipt import ExecutionReceipt, build_execution_receipt, snapshot_content_hash, verify_execution_receipt

DEFAULT_POLICY = ExecutionPolicy("visible-depth-guardrails", "1.1.0", 30, Decimal("0.03"), Decimal("0.02"))


@dataclass(frozen=True)
class AnalysisJobArtifact:
    manifest: AnalysisInputManifest
    receipt: ExecutionReceipt
    verified: bool
    evidence_entry: dict | None = None


def run_analysis_job(*, market_id: str, outcome: str, action: str, requested_size: str, observed_at: str,
                     token_resolver: Callable[[str, str], str] = resolve_token_id,
                     book_fetcher: Callable[[str], BookSnapshot] = fetch_book,
                     evidence_log_path: str | Path | None = None) -> AnalysisJobArtifact:
    token_id = token_resolver(market_id, outcome)
    snapshot = book_fetcher(token_id)
    report = analyze_execution(action=action, bids=snapshot.bids, asks=snapshot.asks, requested_size=requested_size)
    evaluation = evaluate_policy(report=report, snapshot=snapshot, observed_at=observed_at, action=action, policy=DEFAULT_POLICY)
    manifest = build_input_manifest(market_id=market_id, outcome=outcome, action=action, requested_size=requested_size,
        token_id=token_id, observed_at=observed_at, snapshot_content_hash=snapshot_content_hash(snapshot),
        policy_content_hash=DEFAULT_POLICY.content_hash)
    receipt = build_execution_receipt(snapshot=snapshot, report=evaluation.report, action=action, requested_size=requested_size,
        observed_at=observed_at, policy_id=DEFAULT_POLICY.policy_id, policy_version=DEFAULT_POLICY.version,
        policy=DEFAULT_POLICY, policy_metrics=evaluation.metrics, input_manifest=manifest, market_id=market_id, outcome=outcome)
    evidence_entry = append_evidence(evidence_log_path, manifest_hash=manifest.content_hash,
        receipt_hash=receipt.receipt_hash, observed_at=observed_at) if evidence_log_path else None
    return AnalysisJobArtifact(manifest, receipt, verify_execution_receipt(receipt), evidence_entry)
