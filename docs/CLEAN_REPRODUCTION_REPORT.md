# Clean Reproduction Report

**Run date:** 2026-07-23  
**Method:** Fresh shallow clone into `/tmp/outcomerail-clean`; separate Python virtual environment; no source working tree dependencies.

## Commands verified

```bash
git clone --depth 1 https://github.com/Scarpo-gh/outcome-rail.git /tmp/outcomerail-clean
python3 -m venv .venv
.venv/bin/pip install --upgrade pip pytest
.venv/bin/python -m py_compile *.py scripts/*.py
.venv/bin/pytest -q
/home/hermes/.foundry/bin/forge test -q
```

## Results

```text
Python: 50 passed
Foundry: passed
Clean clone status: main...origin/main
```

## Live public-data demo

A fresh public Gamma/CLOB demo was executed from the clean clone:

```text
market_id: 540817
outcome: Yes
action: BUY
size: 5
receipt verified: true
verdict: REDUCE
evidence log: 1 entry, valid: true
```

The resulting local receipt hash was:

```text
2bd534d2f73776bf6951061335e6ab1dc6012bd9099e00e925e740458d2fbb41
```

This was a read-only HTTP demonstration; it did not submit an order or use a wallet.

## Public-link check

All returned HTTP 200 during this run:

- https://scarpo-gh.github.io/outcome-rail/
- Job A create transaction
- Job A complete transaction
- Job B claimRefund transaction

See [ARC_EVIDENCE.md](ARC_EVIDENCE.md) for the exact Arcscan links.
