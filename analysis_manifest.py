"""OutcomeRail provenance manifest for a read-only analysis request."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlencode

SCHEMA_VERSION = "outcomerail.input-manifest.v1"


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class AnalysisInputManifest:
    market_id: str
    outcome: str
    action: str
    requested_size: str
    token_id: str
    observed_at: str
    snapshot_content_hash: str
    policy_content_hash: str

    def to_dict(self) -> dict:
        return {"action": self.action, "market_id": self.market_id, "observed_at": self.observed_at,
                "outcome": self.outcome, "policy_content_hash": self.policy_content_hash,
                "requested_size": self.requested_size, "schema": SCHEMA_VERSION,
                "snapshot_content_hash": self.snapshot_content_hash,
                "sources": {"clob_book_url": f"https://clob.polymarket.com/book?{urlencode({'token_id': self.token_id})}",
                            "gamma_market_url": f"https://gamma-api.polymarket.com/markets?{urlencode({'id': self.market_id})}"},
                "token_id": self.token_id}

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(_canonical(self.to_dict()).encode()).hexdigest()

    def to_json(self) -> str:
        return _canonical({**self.to_dict(), "content_hash": self.content_hash})


def build_input_manifest(**kwargs: str) -> AnalysisInputManifest:
    action = kwargs["action"].upper()
    if action not in {"BUY", "SELL"} or Decimal(kwargs["requested_size"]) <= 0:
        raise ValueError("action must be BUY/SELL and requested_size must be positive")
    for name in ("market_id", "outcome", "token_id", "observed_at", "snapshot_content_hash", "policy_content_hash"):
        if not kwargs[name]:
            raise ValueError(f"{name} is required")
    return AnalysisInputManifest(action=action, **{key: str(value) for key, value in kwargs.items() if key != "action"})
