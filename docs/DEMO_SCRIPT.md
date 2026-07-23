# OutcomeRail — Three-Minute Builder Demo

## Purpose

Show that OutcomeRail produces a deterministic receipt from public prediction-market data and has proved two bounded ERC-8183 terminal paths on Arc Testnet.

## 0:00–0:25 — Problem

> When an agent delivers a public-data analysis, the request, data, policy, and result must remain verifiably connected afterwards. An API response alone does not provide that provenance chain.

## 0:25–0:55 — OutcomeRail receipt

Show:

```bash
python3 scripts/demo_receipt.py --market-id <active-gamma-market-id> --outcome Yes --action BUY --size 5
```

Emphasize:

- Only public Gamma/CLOB data is read.
- VWAP, visible depth, and freshness/spread guardrails are evaluated.
- The result is `PROCEED`, `REDUCE`, or `BLOCK`.
- Snapshot, policy, input, and result are bound to one SHA-256 receipt hash.

> This is not a trading signal or order. The demonstration receipt had a `BLOCK` verdict; the purpose is delivery of analytical evidence.

## 0:55–1:45 — Job A: receipt → complete

Show: [`ARC_EVIDENCE.md`](ARC_EVIDENCE.md#job-a--receipt-delivery-and-completion)

> In Job A, the requester opened the job and funded its 5 test-USDC budget. The provider delivered a verified OutcomeRail receipt hash with `submit`. The evaluator closed the same job with `complete`.

Emphasize:

```text
create → budget → approve → fund → submit(receipt hash) → complete
```

## 1:45–2:25 — Job B: expiry → refund

Show: [`ARC_EVIDENCE.md`](ARC_EVIDENCE.md#job-b--expiry-and-refund)

> In the same bounded model, Job B was funded but no deliverable was submitted. After the deadline, `claimRefund` was executed.

Emphasize:

```text
create → budget → approve → fund → expiry → claimRefund
```

## 2:25–3:00 — Boundaries and next question

> OutcomeRail does not trade, request Polymarket credentials, connect user wallets, provide custody, or use mainnet or real USDC. Polymarket is only the first public-data adapter.

Builder-feedback question:

> For agentic analysis delivery, is a receipt hash alone sufficient, or should the next version use a signed callback or a standardized deliverable schema?

## Live-demo checklist

```bash
pytest -q
/home/hermes/.foundry/bin/forge test -q
python3 scripts/verify_evidence.py --log evidence/outcomerail.jsonl
```

Use only verifiable Arcscan links and repository test output in the presentation.
