# TAP-shaped receipt fixture (AlgoVoi, PQC-signed)

A runnable transaction-receipt fixture for the pattern in
[visa/trusted-agent-protocol#16](https://github.com/visa/trusted-agent-protocol/issues/16)
("Transaction receipt signing for post-authentication audit trail"), built on the
AlgoVoi substrate. Apache-2.0. Names no alternative implementation.

## What it is

`receipt.json` is a TAP-shaped receipt, signed by the merchant over the JCS
(RFC 8785) canonical bytes, with **post-quantum signatures** (Falcon-1024 / FIPS 206,
ML-DSA-65 / FIPS 204) alongside the classical path. It maps onto the RFC's fields:

| RFC #16 field | fixture field |
| --- | --- |
| original TAP signature (binds the authenticated request) | `tap_signature_ref` |
| hash of the transaction payload | `transaction_payload_hash` |
| merchant signature over both | the `signatures` (Falcon-1024 + ML-DSA-65) |
| timestamp + sequence (ordering) | `timestamp_ms` (integer epoch-ms), `sequence` |

Canonicalisation is pinned in-band (`canon_version: jcs-rfc8785-v1`), so the receipt
verifies **offline** from its own bytes — no issuer callback.

## Why PQC here

A payment audit trail has a long retention horizon. A classically-signed receipt
loses non-repudiation once those signatures become forgeable by a quantum computer;
the same JCS-canonical bytes signed with Falcon-1024 / ML-DSA-65 do not. The receipt
carries both, so it interoperates with classical verifiers today and survives the
transition.

## Verify it yourself

```
pip install algovoi-substrate algovoi-substrate-pqc
python verify.py        # recompute the canonical hash + verify every signature, offline
python build_receipt.py # regenerate the fixture from real keypairs
```

`verify.py` recomputes the JCS canonical hash from the receipt bytes and verifies each
signature against its embedded public key — fully offline.
