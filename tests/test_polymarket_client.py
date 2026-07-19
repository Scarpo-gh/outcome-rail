from polymarket_client import normalize_book


def test_normalize_book_keeps_decimal_strings_and_snapshot_metadata():
    snapshot = normalize_book(
        {
            "asset_id": "yes-token",
            "timestamp": "1721314200",
            "hash": "book-hash",
            "bids": [{"price": "0.49", "size": "100"}],
            "asks": [{"price": "0.50", "size": "75"}],
        }
    )

    assert snapshot.token_id == "yes-token"
    assert snapshot.source_timestamp == "1721314200"
    assert snapshot.book_hash == "book-hash"
    assert snapshot.bids == (("0.49", "100"),)
    assert snapshot.asks == (("0.50", "75"),)
