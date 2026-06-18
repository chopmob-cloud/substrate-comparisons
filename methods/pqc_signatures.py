#!/usr/bin/env python3
"""
Post-quantum signatures: the AlgoVoi substrate natively signs and verifies the
canonical record with PQC algorithms -- Falcon-1024 (FIPS 206, NIST L5) and
ML-DSA-65 (FIPS 204, NIST L3) -- over the same JCS (RFC 8785) canonical bytes used
for the classical path. A long-retention payment record signed only with a
classical scheme (Ed25519 / ES256) loses its non-repudiation once a
cryptographically-relevant quantum computer can forge those signatures; a
PQC-signed record does not.

This uses the AlgoVoi implementation (`algovoi-substrate-pqc`): real Falcon-1024
and ML-DSA-65 keypairs, signatures, and `verify_artefact` over the canonical
bytes. Names no alternative implementation; the algorithm-family classification is
the substrate's own registry.

Run:  pip install algovoi-substrate algovoi-substrate-pqc ; python pqc_signatures.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import sys

from algovoi_substrate import action_ref
from algovoi_substrate_pqc import (build_convergence_artefact,
                                   generate_falcon_1024_keypair,
                                   generate_ml_dsa_65_keypair,
                                   lookup_signature_algorithm, sign_falcon_1024,
                                   sign_ml_dsa_65, verify_artefact)

TS = 1716494400123


def main() -> int:
    w = 70
    print("=" * w)
    print("POST-QUANTUM SIGNATURES -- AlgoVoi native PQC (names no alternative impl)")
    print("=" * w)

    ar = action_ref(agent_id="merchant-gw", action_type="payment",
                   scope="order:INV-1", timestamp_ms=TS)
    payload = {"action_ref": ar, "state": "COMMITTED"}
    print(f"canonical record: action_ref={ar[:24]}... state=COMMITTED\n")

    # Native PQC signatures over the canonical record.
    fpk, fsk = generate_falcon_1024_keypair()
    fsig = sign_falcon_1024(payload, fsk, fpk)
    mpk, msk = generate_ml_dsa_65_keypair()
    msig = sign_ml_dsa_65(payload, msk, mpk)
    print("[AlgoVoi native PQC signatures over the JCS-canonical record]")
    print(f"  Falcon-1024  {fsig['fips']} NIST L{fsig['nist_level']}  sig={fsig['signature_length_bytes']} bytes")
    print(f"  ML-DSA-65    {msig['fips']} NIST L{msig['nist_level']}  sig={msig['signature_length_bytes']} bytes")

    art = build_convergence_artefact(payload, {"Falcon-1024": fsig, "ML-DSA-65": msig},
                                    artefact_id="demo-pqc-action-ref")
    res = verify_artefact(art)
    sigs_ok = all(s.ok for s in res.signatures)
    print(f"\n  canonical hash verifies: {res.canonical_sha_ok}")
    for s in res.signatures:
        print(f"  {s.algorithm:<12} signature verifies: {s.ok}")
    pqc_ok = res.canonical_sha_ok and sigs_ok

    print("\n[algorithm family -- the substrate's own registry]")
    for a in ["Falcon-1024", "ML-DSA-65", "Ed25519", "ES256"]:
        fam = lookup_signature_algorithm(a).family.value
        print(f"  {a:<12} -> {fam}{'  (quantum-resistant)' if fam == 'PQC' else '  (NOT quantum-resistant)'}")

    print("-" * w)
    print("RESULT: AlgoVoi natively signs and verifies the canonical record with PQC "
          "(Falcon-1024, ML-DSA-65) over the same JCS bytes; a classical-only stack "
          "(Ed25519/ES256) is not quantum-resistant, so a long-retention record loses "
          "non-repudiation once those signatures become forgeable."
          if pqc_ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if pqc_ok else 1


if __name__ == "__main__":
    sys.exit(main())
