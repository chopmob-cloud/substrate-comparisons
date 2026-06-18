#!/usr/bin/env python3
"""
Field-name determinism: even under JCS, two implementations that disagree on the
field NAMES (camelCase vs snake_case) hash the same logical record to different
bytes, so they cannot cross-verify.

JCS (RFC 8785) fixes key ORDER and value encoding, but it canonicalises whatever
keys it is given. If one implementation emits `timestampMs` and another emits
`timestamp_ms` for the same value, the canonical bytes differ and the two
identities never match. The AlgoVoi JCS (RFC 8785) Substrate pins the snake_case
field set (`agent_id, action_type, scope, timestamp_ms`); a camelCase variant of
the same record is a different identity.

Run:  pip install algovoi-substrate ; python field_naming.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import sys

from algovoi_substrate import action_ref, canonicalize

TS = 1716494400123


def _jcs_sha(obj: dict) -> str:
    c = canonicalize(obj)
    return hashlib.sha256(c.encode("utf-8") if isinstance(c, str) else c).hexdigest()


def main() -> int:
    w = 70
    print("=" * w)
    print("FIELD-NAME DETERMINISM -- reproducible comparison (names no alternative impl)")
    print("=" * w)
    print("the same logical action, two field-name conventions:\n")

    # AlgoVoi JCS (RFC 8785) Substrate: snake_case field set.
    snake = action_ref(agent_id="agent-1", action_type="payment",
                       scope="settlement", timestamp_ms=TS)
    # A camelCase implementation of the same record.
    camel = _jcs_sha({"agentId": "agent-1", "actionType": "payment",
                      "scope": "settlement", "timestampMs": TS})

    print("[AlgoVoi JCS (RFC 8785) Substrate -- snake_case action_ref]")
    print(f"  agent_id/action_type/scope/timestamp_ms -> {snake}")
    print("[camelCase variant of the same record]")
    print(f"  agentId/actionType/scope/timestampMs    -> {camel}\n")

    diverge = snake != camel
    print(f"  same logical action, different identity: {diverge}"
          "  -> the two implementations cannot cross-verify\n")

    print("-" * w)
    print("RESULT: JCS fixes key order, not the field NAMES. The field set must be "
          "pinned; AlgoVoi pins snake_case, so a camelCase variant is a distinct, "
          "non-interoperable identity."
          if diverge else "RESULT: demonstration did not hold -- investigate.")
    return 0 if diverge else 1


if __name__ == "__main__":
    sys.exit(main())
