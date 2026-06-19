#!/usr/bin/env python3
"""
Replay resistance: content-binding vs instance-binding.

Reproducible, offline, names no implementation. A content-addressed action ref is
derived from the action's content alone:

  action_ref = SHA-256(JCS(RFC 8785)({agent_id, action_type, scope, timestamp_ms}))

If two genuinely distinct executions carry identical content (same fields, same
millisecond), their content-address is identical, so content-addressing alone
cannot distinguish a real second execution from a replay of the first. The
substrate binds the action to its settlement INSTANCE:

  binding_ref = settlement_action_binding(action_ref, transition_hash,
                                          settlement_ref, retention_chain_ref)

`settlement_ref` is the on-chain payment hash, unique per execution, so two
identical-content actions settled by two different payments produce two different
binding_refs. The instances stay distinct and a replay is caught.

`action_ref` here is the AlgoVoi implementation (JCS RFC 8785 + integer-ms
timestamp_ms; canon `jcs-rfc8785-v1`).

Run:  pip install algovoi-substrate ; python replay_resistance.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import sys

from algovoi_substrate import (action_ref, settlement_action_binding,
                               sha256_jcs, transition_hash)

TS = 1716494400123
RETENTION = "sha256:" + sha256_jcs({"retention_chain": "demo-head-1"})


def _binding(ar: str, settlement: str) -> str:
    th = transition_hash(action_ref=ar, state="COMMITTED", transition_timestamp_ms=TS,
                        authority_verified_at_ms=TS, revocation_check_at_ms=TS)
    return settlement_action_binding(action_ref=ar, transition_hash=th,
                                    settlement_ref=settlement, retention_chain_ref=RETENTION)


def main() -> int:
    w = 70
    print("=" * w)
    print("REPLAY RESISTANCE -- content-binding vs instance-binding (names no implementation)")
    print("=" * w)
    print("two genuinely distinct executions carrying IDENTICAL action content:\n")

    common = dict(agent_id="agent-1", action_type="payment", scope="order:INV-1", timestamp_ms=TS)
    ar1 = action_ref(**common)
    ar2 = action_ref(**common)   # identical content -> identical content-address
    content_collides = ar1 == ar2
    print("[content-address only: action_ref]")
    print(f"  execution 1 -> {ar1}")
    print(f"  execution 2 -> {ar2}")
    print(f"  collide: {content_collides}  -> a replay cannot be told from a real second execution\n")

    # each execution is settled by its OWN on-chain payment (distinct payment hash)
    pay1 = sha256_jcs({"payment_hash": "settlement-INV-1-exec-1"})
    pay2 = sha256_jcs({"payment_hash": "settlement-INV-1-exec-2"})
    b1 = _binding(ar1, pay1)
    b2 = _binding(ar2, pay2)
    instance_distinct = b1 != b2
    print("[instance-binding: binding_ref over (action_ref + settlement payment hash)]")
    print(f"  execution 1 -> {b1}")
    print(f"  execution 2 -> {b2}")
    print(f"  distinct: {instance_distinct}  -> the two executions stay distinct; replay is caught\n")

    print("-" * w)
    ok = content_collides and instance_distinct
    print("RESULT: content-addressing alone collides on identical content (replay-exposed); "
          "binding the action to its settlement instance keeps distinct executions distinct. "
          "The substrate is instance-bound, not only content-bound."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
