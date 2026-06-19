#!/usr/bin/env python3
"""
Policy binding: can a record prove WHICH policy was in force when it was sealed,
and is a later, silent change to that policy detectable from the record alone?

The AlgoVoi binding is content-addressed. `policy_ref` is the SHA-256 over the
JCS (RFC 8785) canonical form of the policy document itself; `policy_bound_ref`
binds that policy hash to a frozen subject the policy governed (here a real
settlement<->action `binding_ref` produced by `algovoi-substrate`). Because the
binding is over the policy *bytes*, a record sealed under policy P does not
recompute under any changed policy P' -- including a SILENT change that keeps the
same policy id and version label but edits a rule. The two common alternatives --
carrying a policy id/version *label*, or an operator attestation that "policy X
was applied" -- do not change when the rule content changes, so the rotation is
not caught.

`policy_ref` / `policy_bound_ref` are the AlgoVoi `algovoi-policy-binding` package
(Apache-2.0), additive over the frozen substrate; this names no alternative impl.

Run:  pip install algovoi-substrate algovoi-policy-binding ; python policy_binding.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import sys

from algovoi_policy_binding import policy_bound_ref, policy_ref
from algovoi_substrate import (action_ref, settlement_action_binding,
                               sha256_jcs, transition_hash)

TS = 1716494400123

# A real frozen subject: a settlement<->action binding_ref over a committed action.
_AR = action_ref(agent_id="merchant-gw", action_type="payment",
                 scope="order:INV-1", timestamp_ms=TS)
_TH = transition_hash(action_ref=_AR, state="COMMITTED", transition_timestamp_ms=TS,
                      authority_verified_at_ms=TS, revocation_check_at_ms=TS)
_SETTLEMENT = sha256_jcs({"payment_hash": "demo-settlement-INV-1"})
_RETENTION = "sha256:" + sha256_jcs({"retention_chain": "demo-head-1"})
SUBJECT = settlement_action_binding(action_ref=_AR, transition_hash=_TH,
                                    settlement_ref=_SETTLEMENT, retention_chain_ref=_RETENTION)

# The policy in force when the record was sealed.
P = {"policy_id": "aml.transfer", "version": 1, "max_amount": 1000,
     "deny_jurisdictions": ["XX"]}
# A SILENT rotation: SAME policy_id and SAME version label, but a rule was edited
# (the amount ceiling raised and the jurisdiction block dropped).
P_SILENT = {"policy_id": "aml.transfer", "version": 1, "max_amount": 100000,
            "deny_jurisdictions": []}


def _label(policy: dict) -> str:
    # The common alternative: a human/version label, not a content hash.
    return f'{policy["policy_id"]}/v{policy["version"]}'


def main() -> int:
    w = 74
    print("=" * w)
    print("POLICY BINDING -- reproducible comparison (names no alternative impl)")
    print("=" * w)
    print(f"subject (settlement binding_ref): {SUBJECT}\n")

    # [1] AlgoVoi content-addressed policy binding.
    sealed = policy_bound_ref(SUBJECT, policy_ref(P))
    under_silent = policy_bound_ref(SUBJECT, policy_ref(P_SILENT))
    content_detects = sealed != under_silent
    print("[AlgoVoi content-addressed policy binding: policy_bound_ref(subject, policy_ref)]")
    print(f"  policy_ref(P)            -> {policy_ref(P)}")
    print(f"  policy_ref(P', silent)   -> {policy_ref(P_SILENT)}")
    print(f"  sealed under P           -> {sealed}")
    print(f"  recompute under P'       -> {under_silent}")
    print(f"  rotation detected: {content_detects}  -> the bound ref breaks; record fails to recompute\n")

    # [2] Policy id/version label carried in the record.
    label_sealed, label_silent = _label(P), _label(P_SILENT)
    label_detects = label_sealed != label_silent
    print("[policy id/version label carried in the record]")
    print(f"  label under P            -> {label_sealed}")
    print(f"  label under P' (silent)  -> {label_silent}")
    print(f"  rotation detected: {label_detects}  -> label unchanged; the silent edit is NOT caught\n")

    # [3] Operator attestation: "policy X was applied" (no content address).
    attest_sealed = attest_silent = "operator-signed: aml.transfer applied"
    attest_detects = attest_sealed != attest_silent
    print("[operator attestation: 'policy X was applied' (no content address)]")
    print(f"  attestation under P      -> {attest_sealed}")
    print(f"  attestation under P'     -> {attest_silent}")
    print(f"  rotation detected: {attest_detects}  -> attestation unchanged; proves assertion, not bytes\n")

    print("-" * w)
    ok = content_detects and not label_detects and not attest_detects
    if ok:
        print("RESULT: only the content-addressed policy_bound_ref catches a SILENT policy")
        print("rotation -- a record sealed under P fails to recompute under an edited P'. A")
        print("version label or an operator attestation is unchanged by the edit, so the")
        print("rotation is invisible in the record.")
    else:
        print("RESULT: demonstration did not hold -- investigate.")
    # Honest scope note (architectural, not a byte demo): the binding ENABLES
    # rejection; it is REALIZED only when a verifier/gate rejects on a
    # policy_bound_ref mismatch. That enforcement (fail-closed) is a runtime
    # posture decision, not a property of the substrate construction.
    print("\nscope: this proves detectability (version-provable + rotation-detectable),")
    print("offline, from bytes. Acting on a mismatch is a runtime verifier decision.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
