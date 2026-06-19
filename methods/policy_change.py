#!/usr/bin/env python3
"""
Policy rotation (P -> P'): snapshot binding inside the signed decision.

Reproducible, offline, names no implementation. A compliance gate evaluates an
action under a policy that is in force at decision time. Policies rotate: the
strict policy P in force today is replaced by P' tomorrow. The question a later
auditor asks is: *which policy actually admitted this action?*

A decision that binds only the action content

  action_ref = SHA-256(JCS(RFC 8785)({agent_id, action_type, scope, timestamp_ms}))

carries no record of the policy in force. Its digest is identical whether the
gate ran policy P or P', so after a rotation the decision cannot be bound back to
the policy that produced it. An action P would have denied can be presented as an
"ALLOW under P", and an ALLOW issued under a loosened P' is indistinguishable
from one issued under strict P.

The substrate binds a SNAPSHOT of the policy into the signed decision:

  policy_ref      = SHA-256(JCS(policy_document))
  signed_decision = SHA-256(JCS({action_ref, verdict, policy_ref}))

Now P and P' produce different signed decisions over the same action, so every
decision is verifiable against the exact policy snapshot in force when it was
made, and a rotation cannot be retro-applied to an earlier decision.

`action_ref` / `sha256_jcs` here are the AlgoVoi implementation (JCS RFC 8785 +
integer-ms timestamp_ms; canon `jcs-rfc8785-v1`).

Run:  pip install algovoi-substrate ; python policy_change.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import sys

from algovoi_substrate import action_ref, sha256_jcs

TS = 1716494400123

# An action the strict policy P denies (amount over P's cap) but the rotated,
# loosened policy P' allows.
ACTION = dict(agent_id="agent-1", action_type="transfer",
              scope="acct:INV-1:amount:5000", timestamp_ms=TS)

POLICY_P = {"policy_id": "aml.transfer", "version": 1,
            "max_amount": 1000, "deny_jurisdictions": ["XX"]}
POLICY_PRIME = {"policy_id": "aml.transfer", "version": 2,
                "max_amount": 100000, "deny_jurisdictions": []}


def _signed_decision(ar: str, verdict: str, policy_ref: str | None) -> str:
    body = {"action_ref": ar, "verdict": verdict}
    if policy_ref is not None:
        body["policy_ref"] = policy_ref
    return sha256_jcs(body)


def main() -> int:
    w = 70
    print("=" * w)
    print("POLICY ROTATION (P -> P') -- snapshot binding inside the signed decision")
    print("(names no implementation)")
    print("=" * w)

    ar = action_ref(**ACTION)
    ph_p = sha256_jcs(POLICY_P)
    ph_pp = sha256_jcs(POLICY_PRIME)
    print(f"action_ref (same under either policy): {ar}")
    print(f"policy P  snapshot: {ph_p}")
    print(f"policy P' snapshot: {ph_pp}\n")

    # --- unbound: decision carries no policy snapshot --------------------
    unbound_p = _signed_decision(ar, "ALLOW", None)
    unbound_pp = _signed_decision(ar, "ALLOW", None)
    unbound_collides = unbound_p == unbound_pp
    print("[decision WITHOUT policy snapshot]")
    print(f"  decided under P  -> {unbound_p}")
    print(f"  decided under P' -> {unbound_pp}")
    print(f"  identical: {unbound_collides}  -> the decision cannot be bound to the "
          "policy that produced it; a rotation is undetectable\n")

    # --- bound: decision carries the policy snapshot ---------------------
    bound_p = _signed_decision(ar, "ALLOW", ph_p)
    bound_pp = _signed_decision(ar, "ALLOW", ph_pp)
    bound_distinct = bound_p != bound_pp
    print("[decision WITH policy snapshot bound (the substrate)]")
    print(f"  decided under P  -> {bound_p}")
    print(f"  decided under P' -> {bound_pp}")
    print(f"  distinct: {bound_distinct}  -> each decision is verifiable against the "
          "exact policy snapshot in force; a rotation cannot be retro-applied\n")

    print("-" * w)
    ok = unbound_collides and bound_distinct
    print("RESULT: a decision that omits the policy snapshot is identical across a "
          "P -> P' rotation (the policy in force is unprovable); binding the policy "
          "snapshot inside the signed decision keeps each decision bound to its own "
          "policy. The substrate binds the snapshot."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
