from analysis_manifest import build_input_manifest


def test_manifest_is_canonical_and_binds_request_snapshot_and_policy():
    manifest = build_input_manifest(
        market_id="123", outcome="Yes", action="BUY", requested_size="10",
        token_id="yes-token", observed_at="2026-07-18T18:00:01Z",
        snapshot_content_hash="a" * 64, policy_content_hash="b" * 64,
    )

    assert manifest.to_dict()["schema"] == "outcomerail.input-manifest.v1"
    assert manifest.to_dict()["sources"]["gamma_market_url"].endswith("id=123")
    assert len(manifest.content_hash) == 64
    assert manifest.to_json() == build_input_manifest(
        market_id="123", outcome="Yes", action="BUY", requested_size="10",
        token_id="yes-token", observed_at="2026-07-18T18:00:01Z",
        snapshot_content_hash="a" * 64, policy_content_hash="b" * 64,
    ).to_json()
