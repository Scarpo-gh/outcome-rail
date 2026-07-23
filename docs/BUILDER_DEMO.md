# OutcomeRail — Arc Builder Demo Package

## One sentence

**OutcomeRail** is read-only agent infrastructure that evaluates a Polymarket order-book snapshot through its first public-data adapter and produces a deterministic execution-feasibility/provenance receipt.

> It does not request trading, wagering, custody, wallet, or Polymarket credentials; it provides no profitability, outcome-prediction, or investment-result guarantees.

## What it solves

An agent or user may ask: “For this outcome and this size, how feasible is a BUY or SELL against the visible book?” Using only public Gamma and CLOB data, OutcomeRail produces:

- requested-size VWAP and visible executable quantity;
- a `PROCEED`, `REDUCE`, or `BLOCK` verdict;
- snapshot-freshness, spread, and price-gap guardrails;
- a canonical input manifest;
- a receipt verified against modification with SHA-256; and
- an optional append-only local evidence chain.

## Working flow

```text
market_id + outcome + BUY/SELL + requested_size
        │
        ▼
Public Gamma API ──► outcome token id
        │
        ▼
Public CLOB API ───► timestamp + book hash + visible bid/ask levels
        │
        ▼
OutcomeRail core ──► requested-size VWAP / visible depth
        │
        ├──────────► policy v1.1: snapshot age, spread, price gap
        │
        ▼
Canonical manifest ─► execution receipt ─► local evidence entry
                                      │
                                      ▼
                              independent verification
```

Public demo: [https://scarpo-gh.github.io/outcome-rail/](https://scarpo-gh.github.io/outcome-rail/)

Detailed visual: [`outcomerail-architecture.html`](outcomerail-architecture.html). If a browser or panel blocks the file URL, use the directly viewable SVG version: [`outcomerail-architecture.svg`](outcomerail-architecture.svg).

## Read-only local API

For agent/tool integration outside the CLI, use the local WSGI endpoint: `POST /v1/analyze`. Its contract, `curl` example, and error surface are in [`API.md`](API.md). The API starts only on `127.0.0.1`; GitHub Pages is a static demo and does not host the API.

## Two-minute live demo

This command performs only public HTTP reads. It does not submit orders or use authentication, wallets, or transfers.

```bash
cd /home/hermes/outcome-rail
python3 scripts/demo_receipt.py \
  --market-id <active-gamma-market-id> \
  --outcome Yes \
  --action BUY \
  --size 10
```

Expected JSON surface:

```json
{
  "manifest": {"schema": "outcomerail.input-manifest.v1", "content_hash": "..."},
  "receipt": {
    "schema": "outcomerail.execution-receipt.v1",
    "input": {"manifest_hash": "..."},
    "analysis": {"verdict": "PROCEED | REDUCE | BLOCK"}
  },
  "verified": true,
  "evidence_entry": {"entry_hash": "..."}
}
```

Then verify the evidence chain:

```bash
python3 scripts/verify_evidence.py --log evidence/outcomerail.jsonl
```

Example successful verification:

```json
{"log":"evidence/outcomerail.jsonl","entries":1,"valid":true}
```

## Verifiability claim

The receipt binds the following fields into one hash:

- token ID, source-book timestamp/hash, and snapshot content hash;
- requested size, direction, market ID, and outcome;
- policy ID, version, thresholds, and content hash;
- VWAP result, spread, rule IDs, and verdict; and
- input-manifest hash and observation time.

`verify_execution_receipt()` returns `false` if any of these fields is modified later. The evidence log binds each entry to the preceding entry hash.

## Arc integration

The product layer remains off-chain and read-only. On Arc Testnet, two **test-USDC** ERC-8183 proofs were produced for OutcomeRail. They are not trading, wagers, or user funds; they are a bounded analysis-job demonstration between separate test wallets.

### Job A — receipt delivery and completion

- Job ID: `159281`
- Verified OutcomeRail receipt hash: `0x2257db655f069e89c00ff637e36c46612911d5eb3f80fa4d96c68a381c76a02b`
- [createJob](https://testnet.arcscan.app/tx/0x7c5fb3eb26fb6df90eb26af43a8a898dc30d6eb54703ea763849ca0b8f16a635) → [setBudget](https://testnet.arcscan.app/tx/0x8124665d7d6433baa3de320ac9be10f7e3b488ffc4b3ae898d3c5b54896d4d77) → [approve](https://testnet.arcscan.app/tx/0x00d55da8eadb78aa43dc7a36bedb58540c2c60d2cef5709b7f74e1a9e1252615) → [fund](https://testnet.arcscan.app/tx/0x71cb7cfd7521286ee742468c57255dd80a8d76a6de3fef791eac63582bdea589) → [submit](https://testnet.arcscan.app/tx/0x40659649ee965ce59de1fe0f985d6fff89d1de8958521ca6460e0dc9309f832e) → [complete](https://testnet.arcscan.app/tx/0x5968dfe24910eb734fcaaa96cfa7afc9152fbb3611b271f211f1d801312a5ea7)

### Job B — expiry and refund

- Job ID: `159283`
- [createJob](https://testnet.arcscan.app/tx/0x5778d7a58a5246c0f273a85c208d695577312ed10b8fd561f0c2c0106b6a0f04) → [setBudget](https://testnet.arcscan.app/tx/0x45275f5878ddefd78d0cb5c8c65927e6c98f7948d334494e5a451cbd781b46c7) → [approve](https://testnet.arcscan.app/tx/0x49a012b36f86add4e3c45b70240a5909765434cb7825b690679f0af4b039291c) → [fund](https://testnet.arcscan.app/tx/0x88ba57c48791d2d689ef5e65e3768215a0c8229e226c294d7969aa0cd25d710e) → [claimRefund](https://testnet.arcscan.app/tx/0x94865921d18d15f0c9c3391c0cd7eaa17b887651fc74b0af4bf6ec0e5f565f4e)

These proofs are testnet-only: they involve no mainnet, real USDC, custody, wallet-connect, or automated trading.

## Builder feedback request

For a copyable English draft for Arc House/Discord, see [`ARC_HOUSE_FEEDBACK_POST.md`](ARC_HOUSE_FEEDBACK_POST.md). It has not been published.

The requested feedback is specific:

1. What is the minimum deliverable for an agent-paid analysis job: only a receipt, or a signed callback/API response as well?
2. How should freshness, spread, and price-gap thresholds be versioned by market type?
3. What is the simplest, verifiable test-USDC escrow/release model for this job on Arc?

## Explicitly out of scope

- Order submission, automated trading, wallet connection, or custody.
- User funds, settlement, or real-money flows.
- LLM-based price prediction or investment advice.
- Private WebSockets, private Polymarket credentials, or personal data.

## Reproduce

```bash
cd /home/hermes/outcome-rail
python3 -m py_compile analysis_manifest.py analysis_job.py policy.py receipt.py scripts/demo_receipt.py
pytest -q
```

For the demo package’s technical boundaries, also see [`SOURCE_ADAPTATION.md`](SOURCE_ADAPTATION.md).
