# Arc Testnet deploy preflight

**Status:** 2026-07-20 — no transaction broadcast.

## Reused local infrastructure

- Existing Circle Testnet API key, Entity Secret, recovery material and two Developer-Controlled Wallets remain outside this repository.
- No API key, entity secret, wallet, faucet request, private key or live transaction was created for this preflight.
- Arc Testnet RPC previously responds with chain ID `5042002`.

## Historical custom-contract plan — superseded

The initial custom `AnalysisJobEscrow` plan is retained only as a local fallback
state-machine reference. It was **not deployed** and must not be read as live
Arc evidence. The builder-demo default is now the official predeployed ERC-8183
reference contract described below.

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

## Receipt-bound call-plan module

`scripts/arc_erc8183_dry_run.py` accepts a public wallet-state JSON and a
canonical OutcomeRail execution-receipt JSON. It rejects malformed, duplicate
key, tampered, or unverifiable receipts before converting the receipt hash to
the `bytes32` passed to Job A's `submit` call.

```bash
python scripts/arc_erc8183_dry_run.py --state public-wallet-state.json --receipt receipt.json
```

The output is only a deterministic JSON call plan for two separate jobs:

- **Job A:** `createJob`, `setBudget`, USDC `approve`, `fund`, `submit`, and
  `complete`, with the verified receipt hash bound as `deliverableHash`.
- **Job B:** a separate `createJob`, `setBudget`, USDC `approve`, `fund`, and
  post-expiry `claimRefund` path.

By default this module performs no Circle SDK import, network/API/RPC call, or
transaction broadcast; its preflight output is `DRY_RUN_NO_BROADCAST`. A real
broadcast is possible only for **one named lifecycle step** when all of the
following are supplied:

```text
--execute
--confirm ERC8183_EXECUTION_CONFIRMED
--step <named lifecycle step>
```

That guarded path may read a local Circle environment file and submit exactly
one contract-execution request. It is not a default demo path and should be
used only with explicit testnet authorization.

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
