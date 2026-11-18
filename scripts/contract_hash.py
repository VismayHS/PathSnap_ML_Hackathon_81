#!/usr/bin/env python3
"""Compute/verify the reproducible PathSnap contract hash (protocol: 'contract hash').

aggregate = sha256(json.dumps({"version": v, "files": {relpath: sha256}}, sort_keys=True,
                              separators=(",", ":")).encode("utf-8"))
Usage:
  python3 scripts/contract_hash.py            # print hashes
  python3 scripts/contract_hash.py --write    # update contracts/current-manifest.json
  python3 scripts/contract_hash.py --check    # exit 1 if manifest is stale
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "contracts" / "current-manifest.json"
BOUNDARY_FILES = [
    "contracts/artifacts.schema.json",
    "contracts/fixtures/predict_response.synthetic.v0.1.0.json",
    "contracts/http.schema.json",
    "contracts/interfaces.md",
    "src/contracts.py",
]


def contract_version() -> str:
    for line in (ROOT / "src" / "contracts.py").read_text("utf-8").splitlines():
        if line.startswith("CONTRACT_VERSION"):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("CONTRACT_VERSION not found in src/contracts.py")


def compute() -> dict:
    files = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sorted(BOUNDARY_FILES)}
    version = contract_version()
    blob = json.dumps({"version": version, "files": files}, sort_keys=True, separators=(",", ":"))
    return {"version": version, "files": files,
            "aggregate_sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest()}


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()
    cur = compute()
    if args.write:
        MANIFEST.write_text(json.dumps(cur, indent=2, sort_keys=True) + "\n", "utf-8")
    elif args.check:
        old = json.loads(MANIFEST.read_text("utf-8"))
        if old != cur:
            print("contracts/current-manifest.json is stale", file=sys.stderr)
            return 1
    print(json.dumps(cur, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
