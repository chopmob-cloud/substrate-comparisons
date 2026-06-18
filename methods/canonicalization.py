#!/usr/bin/env python3
"""
Canonicalization: which methods are byte-reproducible across implementations.

Reproducible, offline, names no implementation. Takes one logical object,
presents it with two different key orders, and shows:

  - JCS (RFC 8785)            : both orderings hash to the SAME bytes -> two
                                implementations always agree.
  - naive key-order-dependent : the two orderings hash to DIFFERENT bytes -> two
                                implementations disagree on the same object.

Run:  pip install algovoi-substrate ; python canonicalization.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import json
import sys

from algovoi_substrate import canonicalize

# The same logical object, presented in two different key orders.
OBJ_A = {"scope": "settlement", "amount_minor": 100000, "agent_id": "agent-1"}
OBJ_B = {"agent_id": "agent-1", "scope": "settlement", "amount_minor": 100000}


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _jcs_sha(obj: dict) -> str:
    c = canonicalize(obj)
    return _sha(c.encode("utf-8") if isinstance(c, str) else c)


def _naive_sha(obj: dict) -> str:
    # A typical key-order-preserving serialization (no canonicalization).
    return _sha(json.dumps(obj, separators=(",", ":")).encode("utf-8"))


def main() -> int:
    w = 70
    print("=" * w)
    print("CANONICALIZATION -- reproducible comparison (names no implementation)")
    print("=" * w)
    print("one logical object, two key orderings:\n")
    print(f"  A: {OBJ_A}")
    print(f"  B: {OBJ_B}\n")

    jcs_a, jcs_b = _jcs_sha(OBJ_A), _jcs_sha(OBJ_B)
    jcs_ok = jcs_a == jcs_b
    print("[JCS (RFC 8785)]")
    print(f"  A -> {jcs_a}")
    print(f"  B -> {jcs_b}")
    print(f"  identical: {jcs_ok}  -> implementations always agree\n")

    nv_a, nv_b = _naive_sha(OBJ_A), _naive_sha(OBJ_B)
    naive_diff = nv_a != nv_b
    print("[naive key-order-dependent serialization]")
    print(f"  A -> {nv_a}")
    print(f"  B -> {nv_b}")
    print(f"  different: {naive_diff}  -> implementations disagree on the same object\n")

    print("-" * w)
    ok = jcs_ok and naive_diff
    print("RESULT: only JCS is byte-reproducible regardless of key order."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
