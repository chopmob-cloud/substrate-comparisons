#!/usr/bin/env python3
"""
RFC 3339 millisecond-string grammar: still byte-fragile across producers.

Reproducible, offline, names no implementation. Pinning a timestamp to an RFC 3339
millisecond string does not make it byte-stable: the grammar admits several valid
encodings of the SAME instant, so two honest producers diverge.

  same instant, all valid RFC 3339:
    2024-05-23T20:00:00.123Z
    2024-05-23T20:00:00.123+00:00      (Z written as the +00:00 offset)
    2024-05-23T20:00:00.123000Z        (sub-second padded to microseconds)

Each is a different string, so each hashes to a different ref. The integer
epoch-millisecond form (1716494400123) has exactly ONE representation, so it
cannot diverge.

Run:  pip install algovoi-substrate ; python rfc3339_grammar.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import sys

from algovoi_substrate import action_ref, canonicalize

BASE = dict(agent_id="agent-1", action_type="payment", scope="settlement")


def _sha_jcs(obj: dict) -> str:
    c = canonicalize(obj)
    return hashlib.sha256(c.encode("utf-8") if isinstance(c, str) else c).hexdigest()


def main() -> int:
    w = 70
    print("=" * w)
    print("RFC 3339 MILLISECOND-STRING GRAMMAR -- reproducible comparison (names no implementation)")
    print("=" * w)
    print("the same instant (20:00:00.123 UTC), three valid RFC 3339 encodings:\n")

    variants = ["2024-05-23T20:00:00.123Z",
                "2024-05-23T20:00:00.123+00:00",
                "2024-05-23T20:00:00.123000Z"]
    hashes = []
    for v in variants:
        h = _sha_jcs({**BASE, "timestamp": v})
        hashes.append(h)
        print(f"  {v:<32} -> {h}")
    distinct = len(set(hashes))
    rfc_diverges = distinct > 1
    print(f"\n  distinct refs from one instant: {distinct}  -> honest producers diverge: {rfc_diverges}\n")

    i = action_ref(timestamp_ms=1716494400123, **BASE)
    print("[integer epoch-millisecond]  (exactly one representation of the instant)")
    print(f"  1716494400123 -> {i}")
    print("  single-valued: True\n")

    print("-" * w)
    ok = rfc_diverges
    print("RESULT: an RFC 3339 millisecond string is not byte-stable -- one instant has several "
          "valid encodings, so honest producers diverge. The integer epoch-millisecond form has "
          "one representation and cannot."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
