# OutcomeRail — Arc Testnet Evidence

**Network:** Arc Testnet (`5042002`)  
**Reference contract:** `0x0747EEf0706327138c69792bF28Cd525089e4583`  
**Scope:** Bounded, two-wallet, test-USDC ERC-8183 demonstration. This is not trading, wagering, mainnet settlement, custody, or a user-wallet flow.

## Receipt binding

OutcomeRail generated and verified a canonical public-data execution receipt before it was passed as the Job A deliverable commitment:

```text
receipt hash
0x2257db655f069e89c00ff637e36c46612911d5eb3f80fa4d96c68a381c76a02b
```

The receipt came from a read-only public Polymarket snapshot. Its analytical result was `BLOCK`; it was delivered as an evidence object, not as a trade instruction.

## Job A — receipt delivery and completion

**Job ID:** `159281`  
**Budget:** `5` test-USDC

| Lifecycle step | Arcscan transaction |
|---|---|
| `createJob` | [0x7c5f…a635](https://testnet.arcscan.app/tx/0x7c5fb3eb26fb6df90eb26af43a8a898dc30d6eb54703ea763849ca0b8f16a635) |
| `setBudget` | [0x8124…4d77](https://testnet.arcscan.app/tx/0x8124665d7d6433baa3de320ac9be10f7e3b488ffc4b3ae898d3c5b54896d4d77) |
| test-USDC `approve` | [0x00d5…2615](https://testnet.arcscan.app/tx/0x00d55da8eadb78aa43dc7a36bedb58540c2c60d2cef5709b7f74e1a9e1252615) |
| `fund` | [0x71cb…a589](https://testnet.arcscan.app/tx/0x71cb7cfd7521286ee742468c57255dd80a8d76a6de3fef791eac63582bdea589) |
| `submit` receipt hash | [0x4065…832e](https://testnet.arcscan.app/tx/0x40659649ee965ce59de1fe0f985d6fff89d1de8958521ca6460e0dc9309f832e) |
| `complete` | [0x5968…5ea7](https://testnet.arcscan.app/tx/0x5968dfe24910eb734fcaaa96cfa7afc9152fbb3611b271f211f1d801312a5ea7) |

## Job B — expiry and refund

**Job ID:** `159283`  
**Budget:** `5` test-USDC

| Lifecycle step | Arcscan transaction |
|---|---|
| `createJob` | [0x5778…0f04](https://testnet.arcscan.app/tx/0x5778d7a58a5246c0f273a85c208d695577312ed10b8fd561f0c2c0106b6a0f04) |
| `setBudget` | [0x4527…46c7](https://testnet.arcscan.app/tx/0x45275f5878ddefd78d0cb5c8c65927e6c98f7948d334494e5a451cbd781b46c7) |
| test-USDC `approve` | [0x49a0…291c](https://testnet.arcscan.app/tx/0x49a012b36f86add4e3c45b70240a5909765434cb7825b690679f0af4b039291c) |
| `fund` | [0x88ba…710e](https://testnet.arcscan.app/tx/0x88ba57c48791d2d689ef5e65e3768215a0c8229e226c294d7969aa0cd25d710e) |
| post-expiry `claimRefund` | [0x9486…5f4e](https://testnet.arcscan.app/tx/0x94865921d18d15f0c9c3391c0cd7eaa17b887651fc74b0af4bf6ec0e5f565f4e) |

## Reproduction boundaries

- The receipt engine and preflight are covered by the repository test suite.
- The execution adapter requires explicit per-step authorization and a literal confirmation token; it does not run by default.
- Credentials, entity secrets, recovery material, private keys, and wallet identifiers are not committed.
- No mainnet assets or user assets were used.
