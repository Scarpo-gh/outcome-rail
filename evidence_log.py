"""Local append-only, hash-chained OutcomeRail evidence log."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

SCHEMA = "outcomerail.evidence-log.v1"


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(payload: dict) -> str:
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()


def _read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line] if path.exists() else []


def append_evidence(path: str | Path, *, manifest_hash: str, receipt_hash: str, observed_at: str) -> dict:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = _read(path)
    payload = {"schema": SCHEMA, "manifest_hash": manifest_hash, "receipt_hash": receipt_hash,
               "observed_at": observed_at, "previous_entry_hash": rows[-1]["entry_hash"] if rows else None}
    entry = {**payload, "entry_hash": _hash(payload)}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_canonical(entry) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return entry


def verify_evidence_log(path: str | Path) -> bool:
    previous = None
    try:
        for entry in _read(Path(path)):
            payload = {key: value for key, value in entry.items() if key != "entry_hash"}
            if payload.get("schema") != SCHEMA or payload.get("previous_entry_hash") != previous or entry.get("entry_hash") != _hash(payload):
                return False
            previous = entry["entry_hash"]
    except (OSError, json.JSONDecodeError, KeyError):
        return False
    return True
