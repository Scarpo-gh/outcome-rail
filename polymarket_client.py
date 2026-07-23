"""Read-only Polymarket public Gamma/CLOB adapter; contains no authentication or trading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CLOB_BOOK_URL = "https://clob.polymarket.com/book"
GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"
USER_AGENT = "OutcomeRail/0.1 read-only execution-quality research"


@dataclass(frozen=True)
class BookSnapshot:
    token_id: str
    source_timestamp: str | None
    book_hash: str | None
    bids: tuple[tuple[str, str], ...]
    asks: tuple[tuple[str, str], ...]


def normalize_book(payload: dict[str, Any]) -> BookSnapshot:
    def levels(side: str) -> tuple[tuple[str, str], ...]:
        return tuple((str(level["price"]), str(level["size"])) for level in payload.get(side, []))

    return BookSnapshot(
        token_id=str(payload["asset_id"]),
        source_timestamp=str(payload["timestamp"]) if payload.get("timestamp") is not None else None,
        book_hash=str(payload["hash"]) if payload.get("hash") is not None else None,
        bids=levels("bids"),
        asks=levels("asks"),
    )


def fetch_book(token_id: str, *, timeout_seconds: int = 15) -> BookSnapshot:
    """Fetches one CLOB snapshot; raises non-2xx responses and invalid JSON to the caller."""
    url = f"{CLOB_BOOK_URL}?{urlencode({'token_id': token_id})}"
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout_seconds) as response:
        return normalize_book(json.load(response))


def resolve_token_id(market_id: str, outcome: str, *, timeout_seconds: int = 15) -> str:
    """Resolves the CLOB token ID for a Yes/No outcome from an active Gamma market."""
    url = f"{GAMMA_MARKETS_URL}?{urlencode({'id': market_id, 'active': 'true', 'closed': 'false'})}"
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout_seconds) as response:
        markets = json.load(response)
    if not markets:
        raise LookupError(f"Active market not found: {market_id}")
    market = markets[0]
    outcomes = json.loads(market["outcomes"])
    token_ids = json.loads(market["clobTokenIds"])
    try:
        return token_ids[outcomes.index(outcome)]
    except ValueError as exc:
        raise LookupError(f"Outcome not found: {outcome}") from exc
