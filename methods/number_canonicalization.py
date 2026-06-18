#!/usr/bin/env python3
"""
Number canonicalization: JCS (RFC 8785) maps numerically-equal values to one
canonical form (1.0 -> 1, 1e3 -> 1000, -0 -> 0), so two implementations that
mean the same number agree on the bytes. An ad-hoc serialization preserves the
input spelling, so `1.0` and `1` hash differently and the two implementations
diverge on the same value.

Run:  pip install algovoi-substrate ; python number_canonicalization.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import json
import sys

from algovoi_substrate import canonicalize, sha256_jcs

# The AlgoVoi side uses the substrate's own `sha256_jcs` / `canonicalize` -- the
# AlgoVoi implementation adapted to AlgoVoi's own design (canon jcs-rfc8785-v1).


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _naive_sha(obj: dict) -> str:
    return _sha(json.dumps(obj, separators=(",", ":")))


def main() -> int:
    w = 70
    print("=" * w)
    print("NUMBER CANONICALIZATION -- reproducible comparison (names no alternative impl)")
    print("=" * w)
    print("the same value written two ways: 1.0 and 1\n")

    j_a, j_b = sha256_jcs({"rate": 1.0}), sha256_jcs({"rate": 1})
    jcs_agree = j_a == j_b
    print("[AlgoVoi JCS (RFC 8785)]")
    print(f"  canonical(1.0) -> {canonicalize({'rate': 1.0})}")
    print(f"  canonical(1)   -> {canonicalize({'rate': 1})}")
    print(f"  1.0 -> {j_a}")
    print(f"  1   -> {j_b}")
    print(f"  agree: {jcs_agree}  -> numerically-equal values share one identity\n")

    n_a, n_b = _naive_sha({"rate": 1.0}), _naive_sha({"rate": 1})
    naive_diverge = n_a != n_b
    print("[ad-hoc number serialization (preserves input spelling)]")
    print(f"  1.0 -> {n_a}")
    print(f"  1   -> {n_b}")
    print(f"  diverge: {naive_diverge}  -> two implementations disagree on the same value\n")

    print("-" * w)
    ok = jcs_agree and naive_diverge
    print("RESULT: JCS gives one canonical form per numeric value; ad-hoc serialization "
          "diverges on numerically-equal inputs, so two implementations cannot cross-verify."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
