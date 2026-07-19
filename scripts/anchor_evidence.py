"""Son doğrulanmış OutcomeRail evidence hash'ini Arc Testnet'e self-call olarak anchorlar."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_anchor import build_anchor_request
from evidence_log import verify_evidence_log


def latest_verified_entry_hash(log_path: str | Path) -> str:
    path = Path(log_path)
    if not verify_evidence_log(path):
        raise ValueError("evidence log bütünlüğü geçersiz")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    if not rows:
        raise ValueError("evidence log boş")
    return rows[-1]["entry_hash"]


def main() -> int:
    parser = argparse.ArgumentParser(description="OutcomeRail evidence hash Arc Testnet anchor")
    parser.add_argument("--log", default="evidence/outcomerail.jsonl")
    parser.add_argument("--state", default="/home/hermes/arc-forecast-agent/arc_state.json")
    args = parser.parse_args()
    entry_hash = latest_verified_entry_hash(args.log)
    wallet_address = json.loads(Path(args.state).read_text())["source"]["address"]

    from circle.web3 import developer_controlled_wallets as dcw, utils
    api_key, entity_secret = os.environ["CIRCLE_API_KEY"], os.environ["CIRCLE_ENTITY_SECRET"]
    client = utils.init_developer_controlled_wallets_client(api_key=api_key, entity_secret=entity_secret)
    transactions = dcw.TransactionsApi(client)
    request = dcw.CreateContractExecutionTransactionForDeveloperRequest.from_dict(build_anchor_request(
        wallet_address=wallet_address, evidence_entry_hash=entry_hash, idempotency_key=str(uuid.uuid4())))
    response = transactions.create_developer_transaction_contract_execution(request)
    for _ in range(30):
        tx = transactions.get_transaction(id=response.data.id).data.transaction
        if tx.state == "COMPLETE":
            print(json.dumps({"entry_hash": entry_hash, "tx_hash": tx.tx_hash, "arcscan": f"https://testnet.arcscan.app/tx/{tx.tx_hash}"}, separators=(",", ":")))
            return 0
        if tx.state == "FAILED":
            raise RuntimeError("Circle anchor transaction başarısız")
        time.sleep(2)
    raise TimeoutError("Anchor transaction 60 saniye içinde tamamlanmadı")


if __name__ == "__main__":
    raise SystemExit(main())
