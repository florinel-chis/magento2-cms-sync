"""
Run a fake Magento REST API on a local port.

    cd backend
    python -m tests.magento_stub --port 8081 --token secret --seed demo        # "source"
    python -m tests.magento_stub --port 8082 --token secret --seed demo-dest   # "destination"

Then add both as instances in the UI (URL http://127.0.0.1:8081, token "secret") and
compare / sync between them without a real Magento.
"""
from __future__ import annotations

import argparse

import uvicorn

from .app import FakeMagento, create_app
from .seeds import PROFILES, seed_profile


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m tests.magento_stub", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--token", action="append", default=None,
                        help="accepted bearer token (repeatable; default: test-token)")
    parser.add_argument("--name", default=None, help="instance name shown in logs")
    parser.add_argument("--seed", choices=list(PROFILES), default="demo",
                        help="stock = the 4 default CMS pages; demo adds blocks; demo-dest is a drifted copy")
    parser.add_argument("--blocks", type=int, default=0, help="also generate N numbered blocks (pagination tests)")
    parser.add_argument("--emit-store-id", action="store_true",
                        help="include store_id in responses (stock Magento does not)")
    parser.add_argument("--lenient", action="store_true",
                        help="ignore unknown input properties instead of rejecting them like Magento")
    args = parser.parse_args()

    magento = FakeMagento(name=args.name or f"stub:{args.port}", tokens=args.token or ["test-token"],
                          emit_store_id=args.emit_store_id, strict_properties=not args.lenient)
    seed_profile(magento, args.seed, args.blocks)
    print(f"Fake Magento '{magento.name}' on http://{args.host}:{args.port}/rest/V1 "
          f"| tokens={sorted(magento.tokens)} | blocks={len(magento.blocks)} pages={len(magento.pages)}")
    uvicorn.run(create_app(magento), host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
