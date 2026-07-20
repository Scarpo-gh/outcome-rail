# Arc Testnet deploy preflight

**Status:** 2026-07-20 — no transaction broadcast.

## Reused local infrastructure

- Existing Circle Testnet API key, Entity Secret, recovery material and two Developer-Controlled Wallets remain outside this repository.
- No API key, entity secret, wallet, faucet request, private key or live transaction was created for this preflight.
- Arc Testnet RPC previously responds with chain ID `5042002`.

## Contract demo transaction plan

The intended testnet proof requires separate, bounded jobs:

1. Deploy `AnalysisJobEscrow`.
2. Job A: requester `createJob(provider, requestHash, deadline)` with a small test-only amount.
3. Job A: provider `settleJob(jobId, receiptHash)`.
4. Job B: requester creates and funds a second job.
5. Job B: after deadline, requester calls `refundExpiredJob(jobId)`.

This produces separate deploy, settlement, and refund evidence. It does not trade, custody user funds, connect a user wallet, or use mainnet value.

## SDK dry-run result

The installed Circle Developer-Controlled Wallet Python SDK exposes:

- transfer transactions;
- contract-execution transactions; and
- fee estimation.

Its inspected contract-execution request requires `contractAddress` plus a function signature/call data. The installed SDK does **not** expose a distinct contract-deployment transaction method. Therefore no contract deployment request will be fabricated or broadcast from this route.

## Deployment gate

Before an Arc deployment, confirm the official Circle-supported deployment route for the current account (for example Smart Contract Platform or a documented Developer-Controlled Wallet deploy flow), including:

- source wallet selection;
- entity-secret ciphertext generation per request;
- constructor bytecode/calldata encoding;
- fee estimation and native test-token denomination; and
- returned transaction ID / Arcscan verification path.

Only after this gate and Onur's explicit `testnet deploy et` approval may the five testnet transactions above be broadcast.
