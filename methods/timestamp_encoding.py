#!/usr/bin/env python3
"""
Timestamp encoding: which methods preserve exactly-once and interoperate.

Reproducible, offline, names no implementation. Compares three timestamp
encodings on a single agent action identity:

  identity_ref = SHA-256(JCS({agent_id, action_type, scope, <timestamp field>}))

  - integer epoch-millisecond : two sub-second actions stay distinct; canonical.
  - second precision          : two sub-second actions COLLIDE to one ref ->
                                exactly-once breaks, a real action is dropped.
  - RFC 3339 string           : different bytes than the integer form -> cannot
                                cross-verify with it.

Run:  pip install algovoi-substrate ; python timestamp_encoding.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import sys

from algovoi_substrate import action_ref, canonicalize

AGENT_ID, ACTION_TYPE, SCOPE = "agent-1", "payment", "settlement"
SECOND_MS = 1716494400000          # exactly on a wall-clock second
T1, T2 = SECOND_MS + 123, SECOND_MS + 876   # two distinct payments, same second


def _sha_jcs(obj: dict) -> str:
    c = canonicalize(obj)
    return hashlib.sha256((c.encode("utf-8") if isinstance(c, str) else c)).hexdigest()


def main() -> int:
    w = 70
    print("=" * w)
    print("TIMESTAMP ENCODING -- reproducible comparison (names no implementation)")
    print("=" * w)
    print(f"identity: agent_id={AGENT_ID!r} action_type={ACTION_TYPE!r} scope={SCOPE!r}")
    print("two distinct payments inside one second: +123ms and +876ms\n")

    r1 = action_ref(agent_id=AGENT_ID, action_type=ACTION_TYPE, scope=SCOPE, timestamp_ms=T1)
    r2 = action_ref(agent_id=AGENT_ID, action_type=ACTION_TYPE, scope=SCOPE, timestamp_ms=T2)
    ms_ok = r1 != r2
    print("[integer epoch-millisecond]")
    print(f"  +123ms -> {r1}")
    print(f"  +876ms -> {r2}")
    print(f"  distinct: {ms_ok}  -> exactly-once holds\n")

    rs = action_ref(agent_id=AGENT_ID, action_type=ACTION_TYPE, scope=SCOPE, timestamp_ms=SECOND_MS)
    collide = True  # both truncate to SECOND_MS
    print("[second precision]  (both truncate to the same second)")
    print(f"  +123ms -> {rs}")
    print(f"  +876ms -> {rs}")
    print(f"  collision: {collide}  -> exactly-once BREAKS; second payment dropped as a retry\n")

    rfc = _sha_jcs({"action_type": ACTION_TYPE, "agent_id": AGENT_ID,
                    "scope": SCOPE, "timestamp": "2024-05-23T20:00:00.123Z"})
    diverges = rfc != r1
    print("[RFC 3339 string]  (same moment, string-encoded)")
    print(f"  string  -> {rfc}")
    print(f"  integer -> {r1}")
    print(f"  diverges: {diverges}  -> cannot cross-verify with the integer form\n")

    print("-" * w)
    ok = ms_ok and collide and diverges
    print("RESULT: integer epoch-millisecond is the only one of the three that keeps"
          if ok else "RESULT: demonstration did not hold -- investigate.")
    if ok:
        print("        exactly-once AND stays byte-reproducible. Run it; the bytes decide.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
