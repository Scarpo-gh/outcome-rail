"""OutcomeRail evidence entry hash'ini Arc Testnet'e değer transferi olmadan anchorlar."""
from __future__ import annotations

ARC_TESTNET = "ARC-TESTNET"
ANCHOR_MARKER_HEX = "4f5231"  # ASCII: OR1


def encode_anchor_calldata(evidence_entry_hash: str) -> str:
    if len(evidence_entry_hash) != 64 or any(char not in "0123456789abcdef" for char in evidence_entry_hash.lower()):
        raise ValueError("evidence_entry_hash 64 karakter hex olmalı")
    return "0x" + ANCHOR_MARKER_HEX + evidence_entry_hash.lower()


def build_anchor_request(*, wallet_address: str, evidence_entry_hash: str, idempotency_key: str) -> dict[str, str]:
    if not wallet_address.startswith("0x") or len(wallet_address) != 42:
        raise ValueError("wallet_address EVM adresi olmalı")
    return {
        "blockchain": ARC_TESTNET,
        "walletAddress": wallet_address,
        "contractAddress": wallet_address,
        "callData": encode_anchor_calldata(evidence_entry_hash),
        "feeLevel": "MEDIUM",
        "idempotencyKey": idempotency_key,
        "refId": f"outcomerail:{evidence_entry_hash}",
    }
