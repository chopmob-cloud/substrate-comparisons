#!/usr/bin/env python3
"""
Build a TAP-shaped transaction receipt fixture, signed with post-quantum
algorithms over the JCS (RFC 8785) canonical bytes -- the AlgoVoi implementation.

Maps onto visa/trusted-agent-protocol#16 ("Transaction receipt signing for
post-authentication audit trail"): the receipt binds the original TAP request
signature, carries a hash of the transaction payload, a merchant id, an
integer-millisecond timestamp and a sequence number, and is signed by the merchant
(here with Falcon-1024 + ML-DSA-65, alongside the classical path) over the same
JCS-canonical bytes. Offline-verifiable: no issuer callback.

Writes receipt.json (the signed artefact). Verify it with verify.py.
Run:  pip install algovoi-substrate algovoi-substrate-pqc ; python build_receipt.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import json
import os
import sys

from algovoi_substrate import sha256_jcs
from algovoi_substrate_pqc import (build_convergence_artefact,
                                   generate_falcon_1024_keypair,
                                   generate_ml_dsa_65_keypair,
                                   sign_falcon_1024, sign_ml_dsa_65)

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    # TAP-shaped receipt (RFC #16 fields), AlgoVoi discipline: integer-ms timestamp,
    # JCS RFC 8785 canonicalisation, canon_version pinned in-band.
    receipt = {
        "tap_signature_ref": "sha256:" + sha256_jcs({"rfc9421_sig": "tap-request-demo"}),
        "transaction_payload_hash": "sha256:" + sha256_jcs(
            {"amount": "42.00", "currency": "USD", "order": "INV-1"}),
        "merchant_id": "did:web:merchant.example",
        "timestamp_ms": 1716494400123,
        "sequence": 1,
        "canon_version": "jcs-rfc8785-v1",
    }

    fpk, fsk = generate_falcon_1024_keypair()
    mpk, msk = generate_ml_dsa_65_keypair()
    signatures = {
        "Falcon-1024": sign_falcon_1024(receipt, fsk, fpk),
        "ML-DSA-65": sign_ml_dsa_65(receipt, msk, mpk),
    }
    artefact = build_convergence_artefact(
        receipt, signatures, artefact_id="tap-receipt-v0-001",
        context={"profile": "visa-tap-receipt", "ref": "visa/trusted-agent-protocol#16"})

    with open(os.path.join(HERE, "receipt.json"), "w", encoding="utf-8") as f:
        json.dump(artefact, f, indent=2, sort_keys=True)
    print("wrote receipt.json")
    print("expected_canonical_sha256:", artefact["expected_canonical_sha256"])
    print("signatures:", list(artefact["signatures"].keys()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
