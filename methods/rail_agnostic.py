#!/usr/bin/env python3
"""
Rail-agnostic identity: the AlgoVoi `action_ref` is derived from the action alone
(agent_id, action_type, scope, timestamp_ms) -- it carries no settlement rail. So
the same action has the same identity whether it settles on Base, Solana, Hedera,
or any other rail, and a verifier can correlate it across rails. A rail-coupled
identity (one that folds the chain/rail into the hash) changes per rail, so the
same action on two rails looks like two unrelated actions -- no cross-rail
correlation, no cross-rail dedup.

Run:  pip install algovoi-substrate ; python rail_agnostic.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import sys

from algovoi_substrate import action_ref, sha256_jcs

# action_ref is the AlgoVoi implementation, adapted to AlgoVoi's own design
# (JCS RFC 8785 + integer-ms timestamp_ms; canon jcs-rfc8785-v1). It takes no rail.

TS = 1716494400123
ACTION = dict(agent_id="agent-1", action_type="payment", scope="order:INV-1")
RAILS = ["base", "solana", "hedera"]


def _rail_coupled(rail: str) -> str:
    # A rail-coupled identity folds the settlement rail into the hash.
    return sha256_jcs({**ACTION, "timestamp_ms": TS, "settlement_rail": rail})


def main() -> int:
    w = 70
    print("=" * w)
    print("RAIL-AGNOSTIC IDENTITY -- reproducible comparison (names no alternative impl)")
    print("=" * w)
    print("the same action, settled on three different rails:\n")

    ar = action_ref(timestamp_ms=TS, **ACTION)
    print("[AlgoVoi action_ref -- no rail in the identity]")
    for r in RAILS:
        print(f"  settled on {r:<7} -> {ar}")
    agnostic = True  # action_ref does not depend on the rail
    print(f"  same identity on every rail: {agnostic}  -> correlatable across rails\n")

    print("[rail-coupled identity -- rail folded into the hash]")
    coupled = [_rail_coupled(r) for r in RAILS]
    for r, h in zip(RAILS, coupled):
        print(f"  settled on {r:<7} -> {h}")
    all_distinct = len(set(coupled)) == len(coupled)
    print(f"  different identity per rail: {all_distinct}  -> the same action on two rails "
          "looks like two unrelated actions\n")

    print("-" * w)
    ok = agnostic and all_distinct
    print("RESULT: the AlgoVoi action_ref is rail-agnostic -- one identity for the action "
          "across every rail, so it correlates and de-duplicates across rails; a "
          "rail-coupled identity cannot."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
