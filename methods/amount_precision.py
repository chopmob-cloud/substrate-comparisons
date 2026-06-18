#!/usr/bin/env python3
"""
Amount precision: atomic on-chain amounts can exceed JSON's safe-integer range
(2^53). Encoding the amount as a JSON *number* (float64) silently rounds it, so
two operationally distinct amounts collapse to one value -- and therefore one
identity. The AlgoVoi substrate encodes the atomic amount as a *string*, which is
exact (and a strict RFC 8785 implementation rejects an unsafe integer outright,
which is why the string form is the discipline).

Run:  pip install algovoi-substrate ; python amount_precision.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import json
import sys

from algovoi_substrate import sha256_jcs

# The AlgoVoi side uses the substrate's own `sha256_jcs` (JCS RFC 8785 + SHA-256),
# the AlgoVoi implementation adapted to AlgoVoi's own design (canon jcs-rfc8785-v1).

A = 9007199254740993  # 2^53 + 1
B = 9007199254740992  # 2^53      (distinct atomic amounts, 1 unit apart)


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main() -> int:
    w = 70
    print("=" * w)
    print("AMOUNT PRECISION -- reproducible comparison (names no alternative impl)")
    print("=" * w)
    print(f"two distinct atomic amounts, one unit apart: {A} and {B}\n")

    # AlgoVoi: amount as a string -> exact.
    sa = sha256_jcs({"amount": str(A), "asset": "USDC"})
    sb = sha256_jcs({"amount": str(B), "asset": "USDC"})
    string_distinct = sa != sb
    print("[AlgoVoi substrate: amount as a string]")
    print(f"  {A} -> {sa}")
    print(f"  {B} -> {sb}")
    print(f"  distinct: {string_distinct}  -> exact; the two amounts keep two identities\n")

    # naive: amount as a JSON number (float64) -> precision loss.
    fa = _sha(json.dumps({"amount": float(A), "asset": "USDC"}, separators=(",", ":")))
    fb = _sha(json.dumps({"amount": float(B), "asset": "USDC"}, separators=(",", ":")))
    float_collision = fa == fb
    print("[naive: amount as a JSON number (float64)]")
    print(f"  {A} -> {fa}")
    print(f"  {B} -> {fb}")
    print(f"  collision: {float_collision}  -> rounded to the same value; two amounts, one identity\n")

    print("-" * w)
    ok = string_distinct and float_collision
    print("RESULT: a JSON-number amount loses precision past 2^53, collapsing distinct "
          "payments to one identity; the string-encoded atomic amount stays exact (and a "
          "strict RFC 8785 implementation rejects the unsafe integer rather than rounding)."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
