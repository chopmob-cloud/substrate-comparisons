#!/usr/bin/env python3
"""
Offline verifiability: can a holder verify the record with only a hash function
and the retained bytes -- no callback to the issuer, no trust in an operator key?

A content-addressed identity IS the hash of the record's bytes, so a holder
recomputes it offline and compares. An operator-attestation identity (an
operator-assigned id, signed by the operator) is NOT derived from the bytes:
recomputing from the action tells you nothing about the id, so verification
requires the operator's key/endpoint and, even then, only proves the operator
*asserted* it -- not that it is true.

Run:  pip install algovoi-substrate ; python offline_verification.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import sys

from algovoi_substrate import action_ref

# action_ref / the reference here is the AlgoVoi implementation, adapted to
# AlgoVoi's own design (JCS RFC 8785 + integer-ms timestamp_ms; canon jcs-rfc8785-v1).

TS = 1716494400123
FIELDS = dict(agent_id="agent-1", action_type="payment", scope="settlement")


def main() -> int:
    w = 70
    print("=" * w)
    print("OFFLINE VERIFIABILITY -- reproducible comparison (names no alternative impl)")
    print("=" * w)

    stored = action_ref(timestamp_ms=TS, **FIELDS)
    print("[AlgoVoi content-addressed identity]")
    print(f"  stored identity      -> {stored}")
    # A holder recomputes from the retained bytes alone -- no network, no key.
    recomputed = action_ref(timestamp_ms=TS, **FIELDS)
    offline_ok = recomputed == stored
    print(f"  recomputed offline   -> {recomputed}")
    print(f"  verifies offline: {offline_ok}  -> hash function + bytes, no issuer call\n")

    # An operator-attestation identity: an id the operator assigns, not a function
    # of the record bytes.
    operator_id = "att-9f3c1d"
    recompute_from_bytes = action_ref(timestamp_ms=TS, **FIELDS)
    operator_offline_ok = recompute_from_bytes == operator_id
    print("[operator-attestation identity: operator-assigned id, signed by the operator]")
    print(f"  operator id          -> {operator_id}")
    print(f"  recompute from bytes -> {recompute_from_bytes}")
    print(f"  verifies offline: {operator_offline_ok}  -> the id is not a function of the "
          "bytes; you must hold the operator key / call the operator, and that only "
          "proves assertion, not truth\n")

    print("-" * w)
    ok = offline_ok and not operator_offline_ok
    print("RESULT: a content-addressed identity verifies from the bytes alone; an "
          "operator-attestation cannot be checked offline and reduces to trusting the "
          "operator."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
