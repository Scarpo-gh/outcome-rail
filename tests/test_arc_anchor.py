from arc_anchor import build_anchor_request, encode_anchor_calldata


def test_anchor_calldata_contains_only_protocol_marker_and_entry_hash():
    entry_hash = "a" * 64
    assert encode_anchor_calldata(entry_hash) == "0x4f5231" + entry_hash


def test_anchor_request_uses_self_call_without_value_transfer():
    request = build_anchor_request(
        wallet_address="0x7a0a0bd6e35cf5656c6fbc6c6b769b53c374d4b8",
        evidence_entry_hash="b" * 64,
        idempotency_key="123e4567-e89b-42d3-a456-426614174000",
    )
    assert request["blockchain"] == "ARC-TESTNET"
    assert request["contractAddress"] == request["walletAddress"]
    assert request["callData"] == "0x4f5231" + "b" * 64
    assert "amount" not in request
