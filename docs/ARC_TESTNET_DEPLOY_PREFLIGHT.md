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

## Official ERC-8183 route found after the initial SDK preflight

Arc’s current official **Create your first ERC-8183 job** tutorial provides a deployed Arc Testnet reference implementation:

```text
AgenticCommerce: 0x0747EEf0706327138c69792bF28Cd525089e4583
```

This removes the need to deploy the custom fallback contract for the builder demonstration. The installed Circle Wallet SDK's contract-execution route is sufficient because it calls an **existing** reference contract.

The official lifecycle is:

1. `createJob(provider, evaluator, expiredAt, description, hook)`
2. provider: `setBudget(jobId, amount, optParams)`
3. client: ERC-20 `approve(referenceContract, amount)`
4. client: `fund(jobId, optParams)`
5. provider: `submit(jobId, deliverableHash, optParams)`
6. evaluator: `complete(jobId, reasonHash, optParams)`

The reference flow proves a completed, receipt-backed escrow job. The ERC-8183 specification also defines the timeout/refund path: after `expiredAt`, any caller may use `claimRefund(jobId)` while the job is Funded or Submitted; the contract marks it Expired and returns escrow to the client. The reference-contract ABI/function selector must be verified in the dry-run before broadcast.

## Superseded custom deploy gate

The custom `AnalysisJobEscrow` remains a locally tested fallback/state-machine reference. It is no longer the default testnet path. The next testnet gate is a **dry-run of the official predeployed ERC-8183 reference flow**, using the existing Circle wallets and no new keys or wallets.

## Previous custom-contract deployment gate (superseded)

Before an Arc deployment, confirm the official Circle-supported deployment route for the current account (for example Smart Contract Platform or a documented Developer-Controlled Wallet deploy flow), including:

- source wallet selection;
- entity-secret ciphertext generation per request;
- constructor bytecode/calldata encoding;
- fee estimation and native test-token denomination; and
- returned transaction ID / Arcscan verification path.

Only after this gate and Onur's explicit `testnet deploy et` approval may the five testnet transactions above be broadcast.
