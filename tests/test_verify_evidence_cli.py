import subprocess
import sys
from pathlib import Path

from evidence_log import append_evidence


ROOT = Path(__file__).resolve().parents[1]


def test_verify_cli_returns_zero_and_json_for_valid_log(tmp_path):
    path = tmp_path / "evidence.jsonl"
    append_evidence(path, manifest_hash="a" * 64, receipt_hash="b" * 64, observed_at="2026-07-18T18:00:00Z")
    result = subprocess.run([sys.executable, "scripts/verify_evidence.py", "--log", str(path)], cwd=ROOT, text=True, capture_output=True)

    assert result.returncode == 0
    assert '"valid":true' in result.stdout


def test_verify_cli_returns_nonzero_for_tampered_log(tmp_path):
    path = tmp_path / "evidence.jsonl"
    append_evidence(path, manifest_hash="a" * 64, receipt_hash="b" * 64, observed_at="2026-07-18T18:00:00Z")
    path.write_text(path.read_text().replace('"receipt_hash":"', '"receipt_hash":"tampered'))
    result = subprocess.run([sys.executable, "scripts/verify_evidence.py", "--log", str(path)], cwd=ROOT, text=True, capture_output=True)

    assert result.returncode == 1
    assert '"valid":false' in result.stdout
