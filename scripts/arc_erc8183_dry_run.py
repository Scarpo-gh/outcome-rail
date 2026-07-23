#!/usr/bin/env python3
"""OutcomeRail için Arc Testnet ERC-8183 non-broadcast preflight.

Varsayılan mod hiçbir Circle API çağrısı veya blockchain transaction'ı yapmaz.
Yalnız mevcut public wallet state'i ve deterministic request/receipt hash'lerini
kullanarak resmî AgenticCommerce reference contract çağrı planını üretir.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

REFERENCE_CONTRACT = "0x0747EEf0706327138c69792bF28Cd525089e4583"
USDC_CONTRACT = "0x3600000000000000000000000000000000000000"
CHAIN = "ARC-TESTNET"
BUDGET_USDC = "5"


def hash32(text: str) -> str:
    # OutcomeRail canonical evidence hashes are 32-byte SHA-256 values. The
    # ERC-8183 contract accepts them as opaque bytes32 commitments.
    return "0x" + hashlib.sha256(text.encode()).hexdigest()


def load_state(path: Path) -> dict:
    state = json.loads(path.read_text())
    for role in ("source", "destination"):
        if not state.get(role, {}).get("address"):
            raise ValueError(f"wallet state içinde {role}.address yok")
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True, help="Public Arc wallet state JSON")
    parser.add_argument("--deadline-minutes", type=int, default=15)
    args = parser.parse_args()
    if args.deadline_minutes < 10:
        raise SystemExit("Deadline en az 10 dakika olmalı; refund testi için güvenli buffer gerekir.")

    state = load_state(args.state)
    client = state["source"]["address"]
    provider = state["destination"]["address"]
    deadline = int(time.time()) + args.deadline_minutes * 60
    request_hash = hash32("outcomerail:public-data-analysis-job:v1")
    receipt_hash = hash32("outcomerail:canonical-receipt:fixture:v1")
    reason_hash = hash32("outcomerail:receipt-approved:v1")

    plan = {
        "mode": "DRY_RUN_NO_BROADCAST",
        "chain": CHAIN,
        "reference_contract": REFERENCE_CONTRACT,
        "usdc_contract": USDC_CONTRACT,
        "client": client,
        "provider": provider,
        "budget_usdc": BUDGET_USDC,
        "request_hash_preview": request_hash,
        "receipt_hash_preview": receipt_hash,
        "job_a_complete": [
            ["client", "createJob(address,address,uint256,string,address)", [provider, client, str(deadline), "OutcomeRail public-data analysis receipt", "0x0000000000000000000000000000000000000000"]],
            ["provider", "setBudget(uint256,uint256,bytes)", ["<jobId>", "5000000", "0x"]],
            ["client", "approve(address,uint256)", [REFERENCE_CONTRACT, "5000000"]],
            ["client", "fund(uint256,bytes)", ["<jobId>", "0x"]],
            ["provider", "submit(uint256,bytes32,bytes)", ["<jobId>", receipt_hash, "0x"]],
            ["client/evaluator", "complete(uint256,bytes32,bytes)", ["<jobId>", reason_hash, "0x"]],
        ],
        "job_b_refund": [
            "repeat create/setBudget/approve/fund with a separate job",
            f"wait until expiredAt >= {deadline}",
            ["any caller", "claimRefund(uint256)", ["<jobId>"]],
        ],
        "safety": "No transaction, API call, credential read, faucet request, or deploy was performed.",
    }
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
