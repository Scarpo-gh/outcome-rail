import json
from pathlib import Path

from receipt import verify_execution_receipt


EVIDENCE_DIR = Path("docs/evidence/arc-testnet-2026-07-23")


def test_tracked_arc_evidence_bundle_binds_verified_receipt_to_job_a_submit():
    receipt = json.loads((EVIDENCE_DIR / "receipt.json").read_text())
    lifecycle = json.loads((EVIDENCE_DIR / "arc-lifecycle.json").read_text())

    assert verify_execution_receipt(receipt) is True
    assert lifecycle["receipt_binding"]["receipt_hash"] == "0x" + receipt["receipt_hash"]
    job_a = next(job for job in lifecycle["jobs"] if job["id"] == 159281)
    submit = next(step for step in job_a["steps"] if step["method"] == "submit")
    assert submit["deliverable_hash"] == lifecycle["receipt_binding"]["receipt_hash"]


def test_tracked_arc_evidence_bundle_contains_two_distinct_terminal_paths():
    lifecycle = json.loads((EVIDENCE_DIR / "arc-lifecycle.json").read_text())
    by_id = {job["id"]: job for job in lifecycle["jobs"]}

    assert any(step["method"] == "complete" for step in by_id[159281]["steps"])
    assert any(step["method"] == "claimRefund" for step in by_id[159283]["steps"])
