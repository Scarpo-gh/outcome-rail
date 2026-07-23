# Arc Testnet Evidence Bundle

This tracked bundle makes the checkpoint claims reviewable from a repository clone.

## Contents

- `receipt.json` — canonical OutcomeRail receipt submitted for Job A.
- `receipt-verification.json` — recorded verification result and local command.
- `arc-lifecycle.json` — receipt-to-job mapping, Job IDs, lifecycle methods, transaction hashes, and testnet scope.

## Verify the receipt

```bash
python3 - <<'PY'
import json
from receipt import verify_execution_receipt
receipt = json.load(open("docs/evidence/arc-testnet-2026-07-23/receipt.json"))
assert verify_execution_receipt(receipt)
print(receipt["receipt_hash"])
PY
```

## Verify a transaction externally

Each `tx_hash` in `arc-lifecycle.json` resolves at:

```text
https://testnet.arcscan.app/tx/<tx_hash>
```

The bundle contains no credentials, entity secrets, private keys, recovery material, or wallet IDs.
