"""Runs the OutcomeRail read-only WSGI API only on local loopback."""
from __future__ import annotations

import argparse
import ipaddress
import sys
from pathlib import Path
from wsgiref.simple_server import make_server

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api import create_app


def _loopback_host(value: str) -> str:
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("host must be a loopback IP address") from exc
    if not isinstance(address, ipaddress.IPv4Address) or not address.is_loopback:
        raise argparse.ArgumentTypeError("host must be an IPv4 loopback address")
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OutcomeRail read-only Analysis API")
    parser.add_argument("--host", default="127.0.0.1", type=_loopback_host, help="Loopback IP address only")
    parser.add_argument("--port", default=8080, type=int, help="Dinlenecek TCP portu")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    with make_server(args.host, args.port, create_app()) as server:
        print(f"OutcomeRail API listening on http://{args.host}:{args.port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
