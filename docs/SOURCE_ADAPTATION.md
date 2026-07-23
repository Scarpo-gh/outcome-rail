# OutcomeRail — Source-Bot Adaptation Map

## Design adopted directly

| Source | Evidence | OutcomeRail counterpart |
|---|---|---|
| bot_v21 | Requested-size depth, order-book gaps, and exit-depth risks. | V1 requested-size VWAP / visible-depth verdict. Position management and order operations were not transferred. |
| PolyProbe | Combined Gamma metadata and CLOB order books; preference for the official CLOB SDK during Cloudflare issues. | Read-only Gamma/CLOB adapter; `BookSnapshot` retains source time and CLOB hash. |
| ProBot | Deterministic pre-filter before an LLM; append-only analysis record. | The receipt is first built from a deterministic snapshot, policy, and result. LLM signals can be added only as a separate, versioned analysis input. |

## V1 receipt boundary

`receipt.py` binds the following fields into one SHA-256 proof:

- Token ID, CLOB source time/hash, and full snapshot content hash.
- Requested size and `BUY` / `SELL` direction.
- Policy identifier and version.
- VWAP result, visible execution size, spread, verdict, and rule identifiers.
- OutcomeRail observation time.

Receipt verification rejects a modified verdict, policy, snapshot, or input.

## Intentionally excluded

- bot_v21 order placement, rebalancing, position state, and private WebSocket layers: OutcomeRail remains a non-trading pre-execution analysis product.
- bot_v21 reward/Q-score logic: it is LP-specific and is not mixed into the general execution-quality verdict.
- ProBot LLM, external sports data, and whale commentary: they are not written into a receipt before source/evidence versioning is designed separately. LLM output must not be fixed as a direct financial decision.
- PolyProbe Telegram/UI and user analytics: these are presentation/distribution layers and are not imported into the core.

## Next safe extensions

1. **Policy v1.1 (completed):** parameterized max-spread, max-gap, and snapshot-age rules; the policy payload/content hash is included in the receipt.
2. **Analysis input manifest:** when ProBot-like external data or an LLM is used, bind the raw-source hash, provider, timestamp, and confidence level in a separate manifest.
3. **Arc provenance:** a new Arc Testnet anchor transaction for a receipt hash may occur only with explicit approval. The existing test transfer is not a product receipt; it is only project-level technical evidence.

## Security

During import review, `alerts_ws.log`, `positions_ws_archive.jsonl`, and `events.db` were not brought into product code. Private credential/configuration files were not read or copied into OutcomeRail.
