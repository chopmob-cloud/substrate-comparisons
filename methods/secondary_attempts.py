#!/usr/bin/env python3
"""
Secondary attempts: how a content-addressed exactly-once method handles retries.

Reproducible, offline, names no implementation. This is the positive counterpart
to the failure modes in the other demos: the same precision that makes weaker
encodings drop payments is exactly what lets a content-addressed method tell a
genuine retry from a distinct action, and stop one party impersonating another.

It exercises the same properties pinned by the published exactly-once and
adversarial-isolation conformance sets, using a neutral identity:

  1. retry (idempotent)  : re-present the SAME committed transition -> SAME hash
                           -> recognised as the same effect, SKIPPED. No double spend.
  2. distinct action     : a payment 1 ms later -> different identity -> processed
                           as new, NOT skipped.
  3. state load-bearing  : a PENDING transition cannot reproduce the COMMITTED
                           hash -> a non-committed state cannot pass as settled.
  4. isolation           : a different agent with identical parameters -> different
                           identity -> one party cannot impersonate another's action.

Run:  pip install algovoi-substrate ; python secondary_attempts.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import sys

from algovoi_substrate import action_ref, transition_hash

ID = dict(agent_id="agent-1", action_type="payment", scope="settlement")
TS = 1716494400000


def _committed(ar: str) -> str:
    return transition_hash(action_ref=ar, state="COMMITTED",
                           transition_timestamp_ms=1716494500000,
                           authority_verified_at_ms=1716494500300,
                           revocation_check_at_ms=1716494500500)


def main() -> int:
    w = 72
    print("=" * w)
    print("SECONDARY ATTEMPTS -- content-addressed exactly-once handling")
    print("=" * w)

    ar = action_ref(timestamp_ms=TS, **ID)
    print(f"action_ref: {ar}\n")

    # 1. Retry -> same hash -> SKIP.
    first = _committed(ar)
    retry = _committed(ar)
    idempotent = first == retry
    print("[1] genuine retry (identical committed transition re-presented)")
    print(f"    first -> {first}")
    print(f"    retry -> {retry}")
    print(f"    identical: {idempotent}  -> recognised as the same effect, SKIPPED (no double spend)\n")

    # 2. Distinct action -> different identity -> processed as new.
    ar_next = action_ref(timestamp_ms=TS + 1, **ID)
    distinct = ar_next != ar
    print("[2] distinct action (same agent, 1 ms later)")
    print(f"    +1ms -> {ar_next}")
    print(f"    different identity: {distinct}  -> processed as NEW, not skipped\n")

    # 3. State is load-bearing -> PENDING cannot pass as COMMITTED.
    pending = transition_hash(action_ref=ar, state="PENDING",
                              transition_timestamp_ms=1716494400000,
                              authority_verified_at_ms=1716494400500,
                              revocation_check_at_ms=1716494400800)
    state_bound = pending != first
    print("[3] state is load-bearing")
    print(f"    PENDING   -> {pending}")
    print(f"    COMMITTED -> {first}")
    print(f"    distinct: {state_bound}  -> a PENDING transition cannot pass as settled\n")

    # 4. Isolation -> a different agent cannot impersonate the action.
    other = dict(ID); other["agent_id"] = "agent-2"
    ar_other = action_ref(timestamp_ms=TS, **other)
    isolated = ar_other != ar
    print("[4] isolation (different agent, identical action_type/scope/timestamp)")
    print(f"    agent-2 -> {ar_other}")
    print(f"    isolated: {isolated}  -> one party cannot claim another's action\n")

    print("-" * w)
    ok = idempotent and distinct and state_bound and isolated
    if ok:
        print("DEMONSTRATED: retries are absorbed (skipped), distinct actions stay distinct,")
        print("non-committed states cannot pass as settled, and agents are isolated.")
        return 0
    print("DEMONSTRATION DID NOT HOLD -- investigate.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
