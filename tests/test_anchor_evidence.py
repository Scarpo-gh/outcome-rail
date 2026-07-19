import json

from scripts.anchor_evidence import latest_verified_entry_hash
from evidence_log import append_evidence


def test_anchor_uses_latest_verified_evidence_entry(tmp_path):
    path = tmp_path / "evidence.jsonl"
    append_evidence(path, manifest_hash="a" * 64, receipt_hash="b" * 64, observed_at="2026-07-18T18:00:00Z")
    second = append_evidence(path, manifest_hash="c" * 64, receipt_hash="d" * 64, observed_at="2026-07-18T18:00:01Z")

    assert latest_verified_entry_hash(path) == second["entry_hash"]
