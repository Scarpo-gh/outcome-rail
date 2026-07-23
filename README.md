# OutcomeRail

A **read-only execution-feasibility and provenance-receipt layer** for public prediction-market data.

> Prototype / hackathon V1. This is educational developer infrastructure. It does not provide trading, wagering, custody, investment advice, or profitability guarantees.

## V1 scope

- Requested-size VWAP from visible order-book levels for a simulated direction; this is not an order or recommendation.
- `PROCEED`, `REDUCE`, and `BLOCK` execution-feasibility verdicts.
- Top-of-book spread and visible-depth evidence.
- Deterministic SHA-256 report hashes.
- Canonical, off-chain verifiable execution receipts that bind a snapshot, input, policy, and result into one hash.
- A read-only Polymarket Gamma/CLOB snapshot adapter as the first public-data adapter.

## Decision rules

| Verdict | Rule |
|---|---|
| `PROCEED` | The requested size is fully supported by the visible book. |
| `REDUCE` | At least half, but not all, of the requested size is visible. |
| `BLOCK` | Less than half of the requested size is visible. |

This is only a visible-liquidity assessment. The public CLOB adapter also carries the snapshot `timestamp` and `hash`; V1 uses REST snapshots and does not silently hide stale-data or HTTP failures.

## Receipt evidence

`receipt.py` produces an off-chain receipt for pre-execution analysis. The receipt binds the full order-book snapshot content hash, CLOB source metadata, requested size and direction, policy identifier and version, and the `PROCEED` / `REDUCE` / `BLOCK` result into one SHA-256 hash. `verify_execution_receipt()` rejects a modified field.

This V1 receipt is **not financial settlement, a wager, or an investment signal**: it does not perform trading, custody, payments, automated orders, or make profitability claims. Polymarket is only the first public-data adapter; the product has no credential, account, or access-restriction-bypass functionality.

## Policy v1.1 guardrails

`policy.py` can only make the base VWAP report more conservative; it never relaxes a `BLOCK` verdict. The default policy is:

- Snapshot age over 30 seconds, or an unparsable/future source timestamp → `BLOCK` (`STALE_SNAPSHOT`).
- Spread over 0.03 → `REDUCE` (`WIDE_SPREAD`).
- Largest price gap across book levels in the requested direction over 0.02 → `REDUCE` (`LARGE_PRICE_GAP`).

The policy thresholds and content hash are written to the receipt. Run a read-only demo against a real public token:

```bash
# Preferred public-market path
python3 scripts/demo_receipt.py --market-id <gamma-market-id> --outcome Yes --action BUY --size 10

# Alternative: known public CLOB token ID
python3 scripts/demo_receipt.py --token-id <public-clob-token-id> --action BUY --size 10
```

The market path resolves the outcome token through Gamma and also binds a canonical input-manifest hash to the receipt. The manifest covers the public Gamma market and CLOB book endpoint URLs; the CLOB source timestamp and hash are retained in the receipt snapshot. By default, the market command writes a local hash-chained evidence entry to `evidence/outcomerail.jsonl`; that file is not committed. This log alone is not immutable against local filesystem write access. Verify its internal integrity with:

```bash
python3 scripts/verify_evidence.py --log evidence/outcomerail.jsonl
```

The Arc anchor command is experimental and outside the public-demo scope because it broadcasts a transaction. Run it only with separate explicit approval, on testnet, and with local credentials.

Source capabilities that can be adapted: [`docs/SOURCE_ADAPTATION.md`](docs/SOURCE_ADAPTATION.md).

For the Arc builder story, live demo command, verification steps, and architecture, see [`docs/BUILDER_DEMO.md`](docs/BUILDER_DEMO.md).

Public demo: [scarpo-gh.github.io/outcome-rail](https://scarpo-gh.github.io/outcome-rail/)

Arc Testnet evidence: [`docs/ARC_EVIDENCE.md`](docs/ARC_EVIDENCE.md). Builder demo script: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md). Checkpoint presentation: [`docs/checkpoint-2-deck.html`](docs/checkpoint-2-deck.html). Mid-submission video: [`docs/assets/outcomerail-mid-submission-update.mp4`](docs/assets/outcomerail-mid-submission-update.mp4). Mid-submission summary: [`docs/MID_SUBMISSION_SUMMARY.md`](docs/MID_SUBMISSION_SUMMARY.md). Clean-clone verification: [`docs/CLEAN_REPRODUCTION_REPORT.md`](docs/CLEAN_REPRODUCTION_REPORT.md).

## Run locally

```bash
cd outcome-rail
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip pytest
pytest -q
```

## Read-only local API

`POST /v1/analyze` returns a public market snapshot with its receipt and manifest. It does not trade or write an evidence log. For local usage, a `curl` example, error contract, and security boundaries, see [`docs/API.md`](docs/API.md).

```bash
python3 scripts/serve_api.py
```

The default address is loopback-only: `http://127.0.0.1:8080`.

## Security boundaries

- The project does not request or store Polymarket trading credentials.
- It does not execute automated trades.
- Circle API keys, Entity Secrets, and recovery files are not included in this repository.
- The Arc integration binds a verified receipt hash to a bounded **testnet** analysis-job lifecycle. For evidence and Arcscan links, see [`docs/BUILDER_DEMO.md`](docs/BUILDER_DEMO.md#arc-integration). Mainnet, real USDC, and user funds are out of scope.
