"""Read-only OutcomeRail policy and receipt demo from a public CLOB snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis_job import run_analysis_job
from outcomerail_engine import analyze_execution
from policy import ExecutionPolicy, evaluate_policy
from polymarket_client import BookSnapshot, fetch_book
from receipt import build_execution_receipt, verify_execution_receipt

DEFAULT_POLICY = ExecutionPolicy(
    policy_id="visible-depth-guardrails",
    version="1.1.0",
    max_snapshot_age_seconds=30,
    max_spread=Decimal("0.03"),
    max_price_gap=Decimal("0.02"),
)


def build_demo_receipt(
    *,
    token_id: str,
    action: str,
    size: str,
    observed_at: str,
    fetcher: Callable[[str], BookSnapshot] = fetch_book,
) -> dict:
    """Fetches a snapshot and returns a policy result and verified receipt without sending a trade."""
    snapshot = fetcher(token_id)
    base_report = analyze_execution(
        action=action,
        bids=snapshot.bids,
        asks=snapshot.asks,
        requested_size=size,
    )
    evaluation = evaluate_policy(
        report=base_report,
        snapshot=snapshot,
        observed_at=observed_at,
        action=action,
        policy=DEFAULT_POLICY,
    )
    receipt = build_execution_receipt(
        snapshot=snapshot,
        report=evaluation.report,
        action=action,
        requested_size=size,
        observed_at=observed_at,
        policy_id=DEFAULT_POLICY.policy_id,
        policy_version=DEFAULT_POLICY.version,
        policy=DEFAULT_POLICY,
        policy_metrics=evaluation.metrics,
    )
    return {"receipt": receipt.to_dict(), "verified": verify_execution_receipt(receipt)}


def build_market_demo_receipt(**kwargs) -> dict:
    artifact = run_analysis_job(requested_size=kwargs.pop("size"), **kwargs)
    return {"manifest": {**artifact.manifest.to_dict(), "content_hash": artifact.manifest.content_hash},
            "receipt": artifact.receipt.to_dict(), "verified": artifact.verified,
            "evidence_entry": artifact.evidence_entry}


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only OutcomeRail receipt demosu")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--token-id", help="Public Polymarket CLOB token id")
    source.add_argument("--market-id", help="Public Polymarket Gamma market id")
    parser.add_argument("--outcome", help="Outcome for the market path (for example, Yes)")
    parser.add_argument("--action", choices=("BUY", "SELL"), required=True)
    parser.add_argument("--size", required=True, help="Requested contract quantity")
    parser.add_argument("--evidence-log", default="evidence/outcomerail.jsonl", help="Append-only local evidence-log path; used by the market path")
    args = parser.parse_args()
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if args.market_id:
        if not args.outcome:
            parser.error("--outcome is required with --market-id")
        artifact = build_market_demo_receipt(market_id=args.market_id, outcome=args.outcome,
            action=args.action, size=args.size, observed_at=observed_at, evidence_log_path=args.evidence_log)
    else:
        artifact = build_demo_receipt(token_id=args.token_id, action=args.action, size=args.size, observed_at=observed_at)
    print(json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
