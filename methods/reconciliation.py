#!/usr/bin/env python3
"""
Reconciliation: do independent parties agree on the same record?

Reproducible, offline, names no implementation. A regulated payment has several
parties (payer, payee, auditor, facilitator). For the record to be auditable,
every party must independently arrive at the SAME identity for it. That is only
possible if they share one canonical form.

Four parties compute the identity of the SAME logical payment, each with its own
encoding choice:

  - two on the canonical form (integer-ms + JCS), one of them supplying the
    fields in a different key order -> JCS makes them agree, byte-for-byte.
  - one on an RFC 3339 string timestamp, one on second precision -> each lands on
    a DIFFERENT identity. They cannot reconcile with the canonical parties, and
    (the point) they cannot reconcile with EACH OTHER either.

Interoperability is not a feature you add later; it is a property of the form.
Only the canonical form yields a shared identity. This uses only SHA-256, JCS,
and `algovoi-substrate`.

Run:  pip install algovoi-substrate ; python reconciliation.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import sys

from algovoi_substrate import action_ref, canonicalize

AGENT, TYPE, SCOPE = "agent-1", "payment", "settlement"
TS = 1716494400123  # one payment, at 20:00:00.123


def _sha_jcs(obj: dict) -> str:
    c = canonicalize(obj)
    return hashlib.sha256((c.encode("utf-8") if isinstance(c, str) else c)).hexdigest()


def main() -> int:
    # The canonical identity every conformant party should arrive at.
    canonical = action_ref(agent_id=AGENT, action_type=TYPE, scope=SCOPE, timestamp_ms=TS)

    parties = [
        ("party 1", "integer-ms + JCS",
         action_ref(agent_id=AGENT, action_type=TYPE, scope=SCOPE, timestamp_ms=TS)),
        ("party 2", "integer-ms + JCS, fields in different key order",
         _sha_jcs({"timestamp_ms": TS, "scope": SCOPE, "agent_id": AGENT, "action_type": TYPE})),
        ("party 3", "RFC 3339 string timestamp",
         _sha_jcs({"action_type": TYPE, "agent_id": AGENT, "scope": SCOPE,
                   "timestamp": "2024-05-23T20:00:00.123Z"})),
        ("party 4", "second precision",
         action_ref(agent_id=AGENT, action_type=TYPE, scope=SCOPE,
                    timestamp_ms=(TS // 1000) * 1000)),
    ]

    w = 78
    print("=" * w)
    print("RECONCILIATION -- do independent parties agree on the same record?")
    print("one payment; each party computes its identity under its own encoding")
    print("=" * w)
    print(f"{'party':9s} {'encoding':46s} {'identity':12s} {'reconciles'}")
    print("-" * w)
    reconciled = 0
    identities = {}
    for name, enc, ident in parties:
        ok = ident == canonical
        reconciled += 1 if ok else 0
        identities[name] = ident
        print(f"{name:9s} {enc:46s} {ident[:10]}... {'yes' if ok else 'NO'}")

    # do the two non-canonical parties at least agree with each other?
    p3, p4 = identities["party 3"], identities["party 4"]
    forks_agree = p3 == p4

    print("-" * w)
    print(f"{reconciled} of {len(parties)} parties reconcile on the canonical identity")
    print(f"the two non-canonical parties agree with each other: {'yes' if forks_agree else 'NO'}")
    print()
    ok = reconciled == 2 and not forks_agree
    if ok:
        print("Only the canonical form produces a shared identity. The non-canonical")
        print("encodings each land somewhere different -- they cannot reconcile with the")
        print("canonical parties, nor with one another. Interoperability is the form.")
        return 0
    print("DEMONSTRATION DID NOT HOLD -- investigate.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
