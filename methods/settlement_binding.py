#!/usr/bin/env python3
"""
Settlement<->action binding: does the link between a settlement and the action it
paid for survive tampering? A content-addressed binding breaks when either side
is swapped (the swap is detected). A forward-id binding (the settlement record
just carries an operator-assigned receipt id pointing at the action) does NOT
break when the action is swapped -- the id still "points", now at forged content.

Run:  pip install algovoi-substrate ; python settlement_binding.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import sys

from algovoi_substrate import action_ref, canonicalize

TS = 1716494400123
SETTLEMENT = "0x9c1f4ad2b7e84410a0f7c2d6e1b3f59a7c0d2e4f6a8b1c3d5e7f9a0b1c2d3e4f6"


def _jcs_sha(obj: dict) -> str:
    c = canonicalize(obj)
    return hashlib.sha256(c.encode("utf-8") if isinstance(c, str) else c).hexdigest()


def _content_binding(ar: str, settlement: str) -> str:
    # AlgoVoi: the binding is the hash of the structured pair -> recomputable.
    return _jcs_sha({"action_ref": ar, "settlement_ref": settlement})


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

    cb_real = _content_binding(real, SETTLEMENT)
    cb_forged = _content_binding(forged, SETTLEMENT)
    content_detects = cb_real != cb_forged
    print("[AlgoVoi content-addressed binding: SHA-256(JCS({action_ref, settlement_ref}))]")
    print(f"  bound to real action   -> {cb_real}")
    print(f"  bound to forged action -> {cb_forged}")
    print(f"  swap detected: {content_detects}  -> the binding breaks when the action is swapped\n")

    fwd_real, fwd_forged = forward_id, forward_id  # the id is identical regardless of action
    forward_detects = fwd_real != fwd_forged
    print("[forward-id binding: settlement carries an operator-assigned receipt id]")
    print(f"  id over real action   -> {fwd_real}")
    print(f"  id over forged action -> {fwd_forged}")
    print(f"  swap detected: {forward_detects}  -> the id is unchanged; the swap is NOT caught\n")

    print("-" * w)
    ok = content_detects and not forward_detects
    print("RESULT: only the content-addressed binding is tamper-evident -- it breaks "
          "when the action is swapped; a forward-id binding does not bind, because the "
          "id survives a content swap unchanged."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
