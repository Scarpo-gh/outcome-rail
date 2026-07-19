import json

from evidence_log import append_evidence, verify_evidence_log


def test_append_only_log_chains_verified_receipts(tmp_path):
    path = tmp_path / "evidence.jsonl"
    first = append_evidence(path, manifest_hash="a" * 64, receipt_hash="b" * 64, observed_at="2026-07-18T18:00:00Z")
    second = append_evidence(path, manifest_hash="c" * 64, receipt_hash="d" * 64, observed_at="2026-07-18T18:00:01Z")

    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert first["previous_entry_hash"] is None
    assert second["previous_entry_hash"] == first["entry_hash"]
    assert rows[1]["entry_hash"] == second["entry_hash"]
    assert verify_evidence_log(path) is True
