"""OutcomeRail evidence-log integrity verification CLI."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence_log import verify_evidence_log


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an append-only OutcomeRail evidence log")
    parser.add_argument("--log", required=True, help="JSONL evidence log yolu")
    path = Path(parser.parse_args().log)
    valid = verify_evidence_log(path)
    count = len(path.read_text().splitlines()) if path.exists() else 0
    print(json.dumps({"log": str(path), "entries": count, "valid": valid}, separators=(",", ":")))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
