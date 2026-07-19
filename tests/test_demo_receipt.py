from pathlib import Path
import subprocess
import sys

from polymarket_client import normalize_book
from scripts.demo_receipt import build_demo_receipt, build_market_demo_receipt


def test_demo_receipt_builds_a_verified_read_only_artifact_from_injected_snapshot():
    snapshot = normalize_book(
        {
            "asset_id": "yes-token",
            "timestamp": "2026-07-18T18:30:00Z",
            "hash": "book-hash",
            "bids": [{"price": "0.49", "size": "100"}],
            "asks": [{"price": "0.50", "size": "100"}],
        }
    )

    artifact = build_demo_receipt(
        token_id="yes-token",
        action="BUY",
        size="10",
        observed_at="2026-07-18T18:30:01Z",
        fetcher=lambda _: snapshot,
    )

    assert artifact["verified"] is True
    assert artifact["receipt"]["input"]["snapshot"]["token_id"] == "yes-token"
    assert artifact["receipt"]["policy"]["id"] == "visible-depth-guardrails"


def test_market_demo_emits_manifest_and_verified_receipt():
    snapshot = normalize_book({"asset_id":"yes-token", "timestamp":"2026-07-18T18:30:00Z", "hash":"book", "bids":[{"price":"0.49","size":"100"}], "asks":[{"price":"0.50","size":"100"}]})
    artifact = build_market_demo_receipt(market_id="123", outcome="Yes", action="BUY", size="10", observed_at="2026-07-18T18:30:01Z", token_resolver=lambda *_: "yes-token", book_fetcher=lambda _: snapshot)
    assert artifact["verified"] is True
    assert artifact["manifest"]["market_id"] == "123"


def test_demo_script_runs_directly_from_repo_root():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/demo_receipt.py", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Read-only OutcomeRail receipt demosu" in result.stdout
