#!/usr/bin/env python3
"""
Fail-closed before invocation: the default gateway posture.

Reproducible, offline, names no implementation. A gateway decides whether to
INVOKE a tool or DENY it, based on a signed decision receipt. The receipt binds
the action by its content address:

  action_ref = SHA-256(JCS(RFC 8785)({agent_id, action_type, scope, timestamp_ms}))

A sound verification recomputes the action_ref from the LIVE call and requires it
to equal the receipt's action_ref with an ALLOW verdict. The question is what the
gateway does when that verification does not hold -- because the receipt is
missing, or the call was tampered with after the receipt was issued.

  fail-open posture:   admit unless something explicitly says DENY
  fail-closed posture: deny unless a verified ALLOW is present  (the substrate)

The negative test runs three calls through both postures:
  1. a clean call with its valid receipt
  2. a tampered call (recipient redirected) carrying the original receipt
  3. a call with no receipt at all

`action_ref` here is the AlgoVoi implementation (JCS RFC 8785 + integer-ms
timestamp_ms; canon `jcs-rfc8785-v1`).

Run:  pip install algovoi-substrate ; python fail_closed.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import sys

from algovoi_substrate import action_ref

TS = 1716494400123

CALL_CLEAN = dict(agent_id="agent-1", action_type="transfer",
                  scope="recipient:ALICE:amount:50", timestamp_ms=TS)
# attacker redirects the recipient after the receipt was signed
CALL_TAMPERED = dict(CALL_CLEAN, scope="recipient:MALLORY:amount:50")


def _verify(receipt: dict | None, call: dict) -> bool:
    """Sound positive check: recompute action_ref from the live call and match."""
    if not receipt:
        return False
    return receipt.get("verdict") == "ALLOW" and receipt.get("action_ref") == action_ref(**call)


def _fail_closed(receipt: dict | None, call: dict) -> str:
    return "INVOKE" if _verify(receipt, call) else "DENY"


def _fail_open(receipt: dict | None, call: dict) -> str:
    # admits unless an explicit, verified DENY is present; absence/mismatch -> INVOKE
    explicit_deny = bool(receipt) and receipt.get("verdict") == "DENY" \
        and receipt.get("action_ref") == action_ref(**call)
    return "DENY" if explicit_deny else "INVOKE"


def main() -> int:
    w = 70
    print("=" * w)
    print("FAIL-CLOSED BEFORE INVOCATION -- default gateway posture (names no implementation)")
    print("=" * w)

    # a genuine signed ALLOW receipt over the clean call
    receipt = {"action_ref": action_ref(**CALL_CLEAN), "verdict": "ALLOW"}
    print(f"signed ALLOW receipt action_ref: {receipt['action_ref']}")
    print(f"tampered call recomputes to:     {action_ref(**CALL_TAMPERED)}\n")

    cases = [
        ("clean call + valid receipt", receipt, CALL_CLEAN),
        ("tampered call + original receipt", receipt, CALL_TAMPERED),
        ("no receipt", None, CALL_CLEAN),
    ]
    print(f"{'case':<34}{'fail-open':<12}{'fail-closed'}")
    results = {}
    for name, rcpt, call in cases:
        fo = _fail_open(rcpt, call)
        fc = _fail_closed(rcpt, call)
        results[name] = (fo, fc)
        print(f"{name:<34}{fo:<12}{fc}")
    print()

    fo_t, fc_t = results["tampered call + original receipt"]
    fo_m, fc_m = results["no receipt"]
    _, fc_clean = results["clean call + valid receipt"]

    print("-" * w)
    ok = (
        fc_clean == "INVOKE"          # a verified ALLOW still invokes
        and fc_t == "DENY"            # tampered call is denied before invocation
        and fc_m == "DENY"            # missing receipt is denied before invocation
        and fo_t == "INVOKE"          # fail-open invokes the tampered call
        and fo_m == "INVOKE"          # fail-open invokes with no receipt at all
    )
    print("RESULT: the fail-open posture invokes the tampered call and the "
          "no-receipt call before any sound verification; the fail-closed posture "
          "denies both and invokes only on a verified ALLOW. The substrate's "
          "default posture is fail-closed."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
