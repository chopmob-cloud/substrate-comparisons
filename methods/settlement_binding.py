#!/usr/bin/env python3
"""
Settlement<->action binding: does the link between a settlement and the action it
paid for survive tampering? The AlgoVoi binding is content-addressed -- it is the
substrate's own `settlement_action_binding(action_ref, transition_hash,
settlement_ref, retention_chain_ref)` -> a "sha256:"-prefixed `binding_ref`. Swap
the action and the binding_ref changes (the swap is detected). A forward-id
binding (the settlement record just carries an operator-assigned receipt id) does
NOT change when the action is swapped -- the id still "points", now at forged
content.

`action_ref` here is the AlgoVoi implementation, adapted to AlgoVoi's own design:
SHA-256(JCS(RFC 8785)({agent_id, action_type, scope, timestamp_ms})) with
integer-millisecond `timestamp_ms` (canon version `jcs-rfc8785-v1`).

Run:  pip install algovoi-substrate ; python settlement_binding.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import sys

from algovoi_substrate import (action_ref, settlement_action_binding,
                               sha256_jcs, transition_hash)

TS = 1716494400123
# settlement_ref is a 64-char lowercase SHA-256 hex (the on-chain payment hash).
SETTLEMENT = sha256_jcs({"payment_hash": "demo-settlement-INV-1"})
RETENTION = "sha256:" + sha256_jcs({"retention_chain": "demo-head-1"})


def _binding(ar: str) -> str:
    # AlgoVoi substrate's own content-addressed binding (binding_ref).
    th = transition_hash(action_ref=ar, state="COMMITTED", transition_timestamp_ms=TS,
                        authority_verified_at_ms=TS, revocation_check_at_ms=TS)
    return settlement_action_binding(action_ref=ar, transition_hash=th,
                                    settlement_ref=SETTLEMENT, retention_chain_ref=RETENTION)


def main() -> int:
    w = 70
    print("=" * w)
    print("SETTLEMENT<->ACTION BINDING -- reproducible comparison (names no alternative impl)")
    print("=" * w)

    real = action_ref(agent_id="merchant-gw", action_type="payment",
                     scope="order:INV-1", timestamp_ms=TS)
    forged = action_ref(agent_id="attacker", action_type="payment",
                       scope="order:INV-1", timestamp_ms=TS)
    forward_id = "rcpt-0001"  # operator-assigned, not derived from the bytes

    print(f"settlement_ref: {SETTLEMENT[:18]}...")
    print(f"real action_ref:   {real}")
    print(f"forged action_ref: {forged}\n")

    cb_real = _binding(real)
    cb_forged = _binding(forged)
    content_detects = cb_real != cb_forged
    print("[AlgoVoi content-addressed binding: settlement_action_binding(...) -> binding_ref]")
    print(f"  bound to real action   -> {cb_real}")
    print(f"  bound to forged action -> {cb_forged}")
    print(f"  swap detected: {content_detects}  -> the binding_ref breaks when the action is swapped\n")

    fwd_real, fwd_forged = forward_id, forward_id  # the id is identical regardless of action
    forward_detects = fwd_real != fwd_forged
    print("[forward-id binding: settlement carries an operator-assigned receipt id]")
    print(f"  id over real action   -> {fwd_real}")
    print(f"  id over forged action -> {fwd_forged}")
    print(f"  swap detected: {forward_detects}  -> the id is unchanged; the swap is NOT caught\n")

    print("-" * w)
    ok = content_detects and not forward_detects
    print("RESULT: only the content-addressed binding_ref is tamper-evident -- it breaks "
          "when the action is swapped; a forward-id binding does not bind, because the id "
          "survives a content swap unchanged."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
