#!/usr/bin/env python3
"""Safe, receipt-bound ERC-8183 Arc Testnet preflight.

This module only creates deterministic call *plans*. It deliberately imports no
Circle SDK and has no HTTP/RPC/transaction-broadcast code. Future execution is
not implemented and is gated by an explicit confirmation token.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

# Permit ``python scripts/arc_erc8183_dry_run.py`` from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from receipt import verify_execution_receipt

REFERENCE_CONTRACT = "0x0747EEf0706327138c69792bF28Cd525089e4583"
USDC_CONTRACT = "0x3600000000000000000000000000000000000000"
CHAIN = "ARC-TESTNET"
BUDGET_USDC = "5"
BUDGET_BASE_UNITS = 5_000_000
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
EXECUTION_CONFIRMATION_TOKEN = "ERC8183_EXECUTION_CONFIRMED"


class ReceiptPreflightError(ValueError):
    """Receipt JSON is not a verified canonical OutcomeRail receipt."""


class ExecutionUnavailableError(RuntimeError):
    """Raised for all execution requests: this module never broadcasts."""


def hash32(text: str) -> str:
    """Return a bytes32-compatible SHA-256 commitment with a 0x prefix."""
    return "0x" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReceiptPreflightError(f"receipt JSON duplicate key contains: {key}")
        result[key] = value
    return result


def load_verified_receipt_json(receipt_json: str) -> dict[str, Any]:
    """Parse canonical JSON safely and verify receipt integrity before use."""
    try:
        receipt = json.loads(receipt_json, object_pairs_hook=_reject_duplicate_keys)
    except (json.JSONDecodeError, TypeError) as error:
        raise ReceiptPreflightError("receipt must be valid JSON") from error
    if not isinstance(receipt, dict) or not verify_execution_receipt(receipt):
        raise ReceiptPreflightError("receipt schema or integrity verification failed")
    return receipt


def derive_receipt_bytes32(receipt: dict[str, Any]) -> str:
    """Return receipt_hash as bytes32 only after receipt.py verifies it."""
    if not verify_execution_receipt(receipt):
        raise ReceiptPreflightError("receipt must verify before bytes32 derivation")
    receipt_hash = receipt.get("receipt_hash")
    if not isinstance(receipt_hash, str) or len(receipt_hash) != 64:
        raise ReceiptPreflightError("verified receipt_hash must be 32-byte hex")
    try:
        int(receipt_hash, 16)
    except ValueError as error:
        raise ReceiptPreflightError("verified receipt_hash must be hex") from error
    return "0x" + receipt_hash.lower()


def load_state(path: Path) -> dict[str, Any]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("wallet state JSON okunamadı") from error
    return validate_state(state)


def validate_state(state: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(state, dict):
        raise ValueError("wallet state JSON object olmalı")
    for role in ("source", "destination"):
        address = state.get(role, {}).get("address")
        if not isinstance(address, str) or not _is_evm_address(address):
            raise ValueError(f"wallet state içinde geçerli {role}.address yok")
    return state


def _is_evm_address(address: str) -> bool:
    if not address.startswith("0x") or len(address) != 42:
        return False
    try:
        int(address[2:], 16)
    except ValueError:
        return False
    return True


def _call(actor: str, contract: str, function: str, arguments: list[Any]) -> dict[str, Any]:
    return {
        "actor": actor,
        "contract": contract,
        "function": function,
        "arguments": arguments,
    }


def build_erc8183_preflight(*, receipt_json: str, state: dict[str, Any], deadline: int) -> dict[str, Any]:
    """Build Job A completion and separate Job B refund plans without execution."""
    if deadline <= int(time.time()):
        raise ValueError("deadline gelecekte olmalı")
    state = validate_state(state)
    receipt = load_verified_receipt_json(receipt_json)
    receipt_hash = derive_receipt_bytes32(receipt)
    client = state["source"]["address"]
    provider = state["destination"]["address"]
    evaluator = client
    reason_hash = hash32(f"outcomerail:receipt-approved:v1:{receipt_hash}")

    job_a = [
        _call("client", REFERENCE_CONTRACT, "createJob(address,address,uint256,string,address)", [provider, evaluator, str(deadline), "OutcomeRail receipt-backed analysis job A", ZERO_ADDRESS]),
        _call("provider", REFERENCE_CONTRACT, "setBudget(uint256,uint256,bytes)", ["<job_a_id>", str(BUDGET_BASE_UNITS), "0x"]),
        _call("client", USDC_CONTRACT, "approve(address,uint256)", [REFERENCE_CONTRACT, str(BUDGET_BASE_UNITS)]),
        _call("client", REFERENCE_CONTRACT, "fund(uint256,bytes)", ["<job_a_id>", "0x"]),
        _call("provider", REFERENCE_CONTRACT, "submit(uint256,bytes32,bytes)", ["<job_a_id>", receipt_hash, "0x"]),
        _call("evaluator", REFERENCE_CONTRACT, "complete(uint256,bytes32,bytes)", ["<job_a_id>", reason_hash, "0x"]),
    ]
    job_b = [
        _call("client", REFERENCE_CONTRACT, "createJob(address,address,uint256,string,address)", [provider, evaluator, str(deadline), "OutcomeRail refund-path analysis job B", ZERO_ADDRESS]),
        _call("provider", REFERENCE_CONTRACT, "setBudget(uint256,uint256,bytes)", ["<job_b_id>", str(BUDGET_BASE_UNITS), "0x"]),
        _call("client", USDC_CONTRACT, "approve(address,uint256)", [REFERENCE_CONTRACT, str(BUDGET_BASE_UNITS)]),
        _call("client", REFERENCE_CONTRACT, "fund(uint256,bytes)", ["<job_b_id>", "0x"]),
        _call("any caller after expiry", REFERENCE_CONTRACT, "claimRefund(uint256)", ["<job_b_id>"]),
    ]
    return {
        "mode": "DRY_RUN_NO_BROADCAST",
        "chain": CHAIN,
        "reference_contract": REFERENCE_CONTRACT,
        "usdc_contract": USDC_CONTRACT,
        "client": client,
        "provider": provider,
        "evaluator": evaluator,
        "budget_usdc": BUDGET_USDC,
        "budget_base_units": str(BUDGET_BASE_UNITS),
        "deadline": deadline,
        "receipt_hash_bytes32": receipt_hash,
        "reason_hash_bytes32": reason_hash,
        "job_a_complete": job_a,
        "job_b_refund": job_b,
        "safety": {
            "broadcast_performed": False,
            "network_calls_performed": False,
            "execution_implemented": False,
            "future_execution_requires_confirmation_token": EXECUTION_CONFIRMATION_TOKEN,
        },
    }


def request_execution(plan: dict[str, Any], *, confirmation_token: str | None) -> None:
    """Fail closed: even confirmed execution cannot broadcast from this module."""
    if confirmation_token != EXECUTION_CONFIRMATION_TOKEN:
        raise ExecutionUnavailableError("execution requires the deliberate confirmation token")
    raise ExecutionUnavailableError("execution is not implemented; no transaction was broadcast")


def main() -> None:
    parser = argparse.ArgumentParser(description="Receipt-verified ERC-8183 dry-run; never broadcasts.")
    parser.add_argument("--state", type=Path, required=True, help="Public Arc wallet state JSON")
    parser.add_argument("--receipt", type=Path, required=True, help="Canonical OutcomeRail receipt JSON")
    parser.add_argument("--deadline-minutes", type=int, default=15)
    parser.add_argument("--execute", action="store_true", help="Reserved; execution remains unavailable")
    parser.add_argument("--confirm", help="Required deliberate token for a future execution mode")
    args = parser.parse_args()
    if args.deadline_minutes < 10:
        raise SystemExit("Deadline en az 10 dakika olmalı; refund testi için güvenli buffer gerekir.")

    deadline = int(time.time()) + args.deadline_minutes * 60
    plan = build_erc8183_preflight(
        receipt_json=args.receipt.read_text(encoding="utf-8"),
        state=load_state(args.state),
        deadline=deadline,
    )
    print(json.dumps(plan, indent=2, sort_keys=True))
    if args.execute:
        request_execution(plan, confirmation_token=args.confirm)


if __name__ == "__main__":
    main()
