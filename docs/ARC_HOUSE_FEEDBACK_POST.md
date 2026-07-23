# Arc House / Discord — Technical Feedback Post

> This is a draft for publication; it has not yet been sent to Arc House or Discord.

## Title

**Feedback request: verifiable, read-only prediction-market analysis jobs on Arc**

## Post metni

Hi all — I’m building **OutcomeRail**, a read-only execution-quality layer for prediction-market agents.

Given a public Polymarket `market_id`, outcome, side and requested size, it:

- resolves the public outcome token through Gamma;
- reads the public CLOB orderbook;
- computes requested-size VWAP and visible-depth availability;
- applies deterministic freshness, spread and price-gap guardrails;
- returns `PROCEED`, `REDUCE`, or `BLOCK`;
- produces a canonical input manifest and tamper-evident execution receipt.

The current V1 is intentionally narrow: no trade placement, custody, wallet connection, private credentials, or settlement. A live public-data smoke run produces a verified receipt and an append-only local evidence entry.

Architecture / demo package: https://scarpo-gh.github.io/outcome-rail/

I’d appreciate feedback on one specific next step: **what is the simplest Arc-native model for a bounded agent analysis job?**

My current direction is:

```text
agent opens a small test-USDC analysis job
→ OutcomeRail returns a receipt within a bounded TTL
→ contract verifies required receipt fields / a trusted verifier attestation
→ release to provider, otherwise refund
```

Questions:

1. For an early testnet prototype, is a signed callback/attestation more practical than attempting full on-chain verification of an off-chain orderbook receipt?
2. What is the minimum useful on-chain job schema beyond `job_id`, requester, provider, amount, expiry and receipt hash?
3. Are there existing Arc examples or builders working on similar agent-payment / escrow flows that would be useful to study?

I’m looking for architecture feedback, not trading advice or promotion. Happy to share the sanitized code/demo once it is published.

## Pre-publication checklist

- Replace `<PUBLIC_REPO_OR_DEMO_URL>` with the actual public URL.
- Link only a working, sanitized repository/demo.
- Do not share wallet addresses, API keys, `.env`, recovery files, or private logs.
- Do not request rewards, airdrops, or roles beyond “test-USDC”.
- Record concrete feedback received after publication in a dated note under `docs/`; update the same Arc House thread instead of posting a second one.
