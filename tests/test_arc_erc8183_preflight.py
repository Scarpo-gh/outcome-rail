import json
from decimal import Decimal
from pathlib import Path
import subprocess
import sys

import pytest

from outcomerail_engine import analyze_execution
from policy import ExecutionPolicy
from polymarket_client import normalize_book
from receipt import build_execution_receipt
from scripts.arc_erc8183_dry_run import (
    EXECUTION_CONFIRMATION_TOKEN,
    ExecutionUnavailableError,
    ReceiptPreflightError,
    build_erc8183_preflight,
    derive_receipt_bytes32,
    request_execution,
)


def _canonical_receipt_json() -> str:
    snapshot = normalize_book(
        {
            "asset_id": "yes-token",
            "timestamp": "2026-07-18T12:00:00Z",
            "hash": "clob-book-hash",
            "bids": [{"price": "0.49", "size": "100"}],
            "asks": [{"price": "0.50", "size": "75"}],
        }
    )
    report = analyze_execution(
        action="BUY", bids=snapshot.bids, asks=snapshot.asks, requested_size="50"
    )
    receipt = build_execution_receipt(
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
        market_id="123",
        outcome="Yes",
    )
    return receipt.to_json()


def _state() -> dict[str, dict[str, str]]:
    return {
        "source": {"address": "0x1111111111111111111111111111111111111111"},
        "destination": {"address": "0x2222222222222222222222222222222222222222"},
    }


def test_preflight_verifies_canonical_receipt_before_binding_bytes32():
    receipt_json = _canonical_receipt_json()
    receipt = json.loads(receipt_json)

    plan = build_erc8183_preflight(
        receipt_json=receipt_json, state=_state(), deadline=1_800_000_000
    )

    expected_bytes32 = "0x" + receipt["receipt_hash"]
    assert derive_receipt_bytes32(receipt) == expected_bytes32
    assert plan["mode"] == "DRY_RUN_NO_BROADCAST"
    assert plan["receipt_hash_bytes32"] == expected_bytes32
    assert plan["job_a_complete"][4]["arguments"][1] == expected_bytes32
    assert [call["function"] for call in plan["job_a_complete"]] == [
        "createJob(address,address,uint256,string,address)",
        "setBudget(uint256,uint256,bytes)",
        "approve(address,uint256)",
        "fund(uint256,bytes)",
        "submit(uint256,bytes32,bytes)",
        "complete(uint256,bytes32,bytes)",
    ]
    assert [call["function"] for call in plan["job_b_refund"]] == [
        "createJob(address,address,uint256,string,address)",
        "setBudget(uint256,uint256,bytes)",
        "approve(address,uint256)",
        "fund(uint256,bytes)",
        "claimRefund(uint256)",
    ]


def test_preflight_rejects_tampered_or_duplicate_key_receipt_before_hash_binding():
    tampered = json.loads(_canonical_receipt_json())
    tampered["analysis"]["verdict"] = "BLOCK"

    with pytest.raises(ReceiptPreflightError):
        derive_receipt_bytes32(tampered)

    duplicate_hash_json = _canonical_receipt_json().replace(
        '"receipt_hash":', '"receipt_hash":"not-a-valid-hash","receipt_hash":', 1
    )
    with pytest.raises(ReceiptPreflightError):
        build_erc8183_preflight(
            receipt_json=duplicate_hash_json, state=_state(), deadline=1_800_000_000
        )


def test_execution_request_is_never_broadcast_by_default_and_requires_confirmation_token():
    plan = build_erc8183_preflight(
        receipt_json=_canonical_receipt_json(), state=_state(), deadline=1_800_000_000
    )

    assert plan["safety"]["broadcast_performed"] is False
    with pytest.raises(ExecutionUnavailableError, match="confirmation token"):
        request_execution(plan, confirmation_token=None)
    with pytest.raises(ExecutionUnavailableError, match="not implemented"):
        request_execution(plan, confirmation_token=EXECUTION_CONFIRMATION_TOKEN)


def test_preflight_script_runs_directly_from_repo_root():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/arc_erc8183_dry_run.py", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Receipt-verified ERC-8183 dry-run" in result.stdout
