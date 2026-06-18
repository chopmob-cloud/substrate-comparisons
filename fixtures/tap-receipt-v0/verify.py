#!/usr/bin/env python3
"""
Offline verification of the TAP-shaped receipt fixture: recompute the JCS canonical
hash from the receipt bytes and verify each PQC signature -- no issuer callback, no
network. The AlgoVoi implementation (algovoi-substrate-pqc).

Run:  pip install algovoi-substrate-pqc ; python verify.py
Apache-2.0. (c) AlgoVoi.
"""
import json, os, sys
from algovoi_substrate_pqc import verify_artefact

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    art = json.load(open(os.path.join(HERE, "receipt.json"), encoding="utf-8"))
    res = verify_artefact(art)
    print("canonical hash verifies:", res.canonical_sha_ok)
    print("  expected: ", res.canonical_sha_expected)
    print("  recomputed:", res.canonical_sha_recomputed)
    ok = res.canonical_sha_ok
    for s in res.signatures:
        print(f"  {s.algorithm:<12} signature verifies: {s.ok}")
        ok = ok and s.ok
    print("\nRESULT:", "VERIFIED offline (canonical hash + all PQC signatures)" if ok
          else "FAILED -- investigate")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
