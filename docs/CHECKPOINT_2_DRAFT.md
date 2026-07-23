# Checkpoint 2 — Submission Draft

> Use this draft only after the live Encode form fields are reviewed. Do not invent a video URL, deployment URL, or requirement that the form does not ask for.

## Project name

OutcomeRail

## One-line description

OutcomeRail is a read-only agent infrastructure layer that turns public prediction-market snapshots into deterministic, verifiable execution-feasibility receipts.

## Progress update

We built a deterministic public-data analysis engine using Polymarket Gamma/CLOB as the first adapter. It produces a canonical receipt that binds the market input, orderbook snapshot, policy version, verdict, and evidence hash. The engine is read-only: it does not trade, request Polymarket credentials, connect user wallets, or custody assets.

On Arc Testnet, we demonstrated two bounded ERC-8183 test-USDC analysis jobs using Arc's predeployed reference contract. Job A followed create → budget → approve → fund → submit(verified OutcomeRail receipt hash) → complete. Job B followed create → budget → approve → fund → expiry → claimRefund. The two terminal paths demonstrate receipt-backed delivery and timeout protection separately.

## Links

- Repository: https://github.com/Scarpo-gh/outcome-rail
- Public demo: https://scarpo-gh.github.io/outcome-rail/
- Arc evidence: [ARC_EVIDENCE.md](ARC_EVIDENCE.md)
- Builder demo flow: [DEMO_SCRIPT.md](DEMO_SCRIPT.md)

## Technical proof

- Python suite: `50 passed`
- Foundry lifecycle suite: passing
- Job A completion: https://testnet.arcscan.app/tx/0x5968dfe24910eb734fcaaa96cfa7afc9152fbb3611b271f211f1d801312a5ea7
- Job B refund: https://testnet.arcscan.app/tx/0x94865921d18d15f0c9c3391c0cd7eaa17b887651fc74b0af4bf6ec0e5f565f4e

## What we want feedback on

For a bounded agentic public-data analysis job, is a canonical receipt hash sufficient as the deliverable commitment, or should the next version include a signed callback and a standardized deliverable schema?

## Explicit scope boundary

This is a testnet demonstration only. It does not use mainnet, real USDC, user funds, custody, wallet-connect, automated trading, wagering access, or investment/profit claims.
