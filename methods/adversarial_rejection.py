#!/usr/bin/env python3
"""
Adversarial rejection: does the method reject malformed input, or hash it anyway?

Reproducible, offline. This is the second reference property (the first is
exactly-once, in secondary_attempts.py). A content-addressed method must REJECT
inputs that violate its discipline at the validation layer, not silently compute
a valid-looking hash for them. A hash computed over an invalid record is a record
that looks settled but is not.

Two approaches, same five adversarial inputs:

  - validating (the reference)  : raises on each -> the bad record never gets an
                                  identity. This is the adversarial_isolation_v1
                                  property of the published substrate.
  - naive "hash whatever"       : canonicalises and hashes anything handed to it
                                  -> every malformed record gets a clean-looking
                                  identity it should never have had.

Run:  pip install algovoi-substrate ; python adversarial_rejection.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import sys

from algovoi_substrate import action_ref, canonicalize, transition_hash

BASE = dict(agent_id="agent-1", action_type="payment", scope="settlement")
GOOD_AR = action_ref(timestamp_ms=1716494400000, **BASE)


def _naive_hash(obj: dict) -> str:
    c = canonicalize(obj)
    return hashlib.sha256((c.encode("utf-8") if isinstance(c, str) else c)).hexdigest()


def _validating(fn) -> tuple[bool, str]:
    """Returns (rejected, detail)."""
    try:
        fn()
        return False, "ACCEPTED (no validation)"
    except Exception as e:
        return True, f"rejected [{type(e).__name__}]"


CASES = [
    ("RFC 3339 string timestamp",
     lambda: action_ref(timestamp_ms="2024-05-23T20:00:00Z", **BASE),
     {**BASE, "timestamp_ms": "2024-05-23T20:00:00Z"}),
    ("negative timestamp",
     lambda: action_ref(timestamp_ms=-1, **BASE),
     {**BASE, "timestamp_ms": -1}),
    ("boolean timestamp",
     lambda: action_ref(timestamp_ms=True, **BASE),
     {**BASE, "timestamp_ms": True}),
    ("non-hex action_ref",
     lambda: transition_hash(action_ref="z" * 64, state="COMMITTED",
                             transition_timestamp_ms=1, authority_verified_at_ms=1,
                             revocation_check_at_ms=1),
     {"action_ref": "z" * 64, "state": "COMMITTED"}),
    ("short action_ref",
     lambda: transition_hash(action_ref="abcd", state="COMMITTED",
                             transition_timestamp_ms=1, authority_verified_at_ms=1,
                             revocation_check_at_ms=1),
     {"action_ref": "abcd", "state": "COMMITTED"}),
]


def main() -> int:
    w = 74
    print("=" * w)
    print("ADVERSARIAL REJECTION -- validate and reject, or silently hash?")
    print("=" * w)
    print(f"{'adversarial input':30s} {'validating (reference)':26s} {'naive hash-whatever'}")
    print("-" * w)
    all_rejected, all_naive_accept = True, True
    for label, bad_call, naive_obj in CASES:
        rejected, detail = _validating(bad_call)
        all_rejected = all_rejected and rejected
        naive = _naive_hash(naive_obj)
        all_naive_accept = all_naive_accept and bool(naive)
        print(f"{label:30s} {detail:26s} accepted -> {naive[:12]}...")
    print("-" * w)
    ok = all_rejected and all_naive_accept
    if ok:
        print("The reference rejects every malformed input; the naive method hands each one")
        print("a clean-looking identity. Validation is the difference between a settled")
        print("record and a forged-looking one.")
        return 0
    print("DEMONSTRATION DID NOT HOLD -- investigate.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
