from polymarket_client import normalize_book
from analysis_job import run_analysis_job


def test_analysis_job_resolves_market_and_binds_manifest_to_receipt(tmp_path):
    snapshot = normalize_book({"asset_id": "yes-token", "timestamp": "2026-07-18T18:00:00Z", "hash": "book", "bids": [{"price":"0.49","size":"100"}], "asks":[{"price":"0.50","size":"100"}]})
    artifact = run_analysis_job(
        market_id="123", outcome="Yes", action="BUY", requested_size="10", observed_at="2026-07-18T18:00:01Z",
        token_resolver=lambda market_id, outcome: "yes-token", book_fetcher=lambda token_id: snapshot,
        evidence_log_path=tmp_path / "evidence.jsonl",
    )
    assert artifact.manifest.token_id == "yes-token"
    assert artifact.receipt.to_dict()["input"]["manifest_hash"] == artifact.manifest.content_hash
    assert artifact.verified is True
    assert artifact.evidence_entry["receipt_hash"] == artifact.receipt.receipt_hash
