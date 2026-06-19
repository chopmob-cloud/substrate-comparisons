<!--
  Apache-2.0. Copyright 2026 Christopher Hopley / AlgoVoi (chopmob-cloud).
-->

# Results: where each method fails

Every line below is produced by a script in this repo. The hashes are real and
reproducible: run the named demo and you will get the same bytes. No
implementation, project, or person is named; methods are compared by technique.

The reference is the AlgoVoi substrate (integer epoch-millisecond + JCS), which
holds every property. Each alternative encoding fails at least one, shown here
with the exact evidence.

## 1. Second precision -> fails exactly-once

`methods/timestamp_encoding.py`, `methods/scale.py`

- Two distinct payments in the same second collapse to one identity:
  - payment at `+123ms` -> `12824b4b65956ba181ffe5acf9b50df853df9a08ebe53e3e1e859e5ea305433e`
  - payment at `+876ms` -> `12824b4b65956ba181ffe5acf9b50df853df9a08ebe53e3e1e859e5ea305433e`
  - identical. The second payment is indistinguishable from a retry and is dropped.
- At scale (counted from real hashes):

  | Payments | second precision dropped | integer-ms dropped |
  | --- | :---: | :---: |
  | 100 in 1s | 99 (99.0%) | 0 |
  | 1,000 in 1s | 999 (99.9%) | 0 |
  | 10,000 over 10s | 9,990 (99.9%) | 0 |
  | 60,000 over 60s | 59,940 (99.9%) | 0 |
  | 100,000 over 100s | 99,900 (99.9%, only 100 survive) | 0 |

- Consequence: at any realistic agentic rate, more than 99% of real payments are
  silently dropped.

## 2. RFC 3339 string timestamp -> fails byte-reproducibility

`methods/timestamp_encoding.py`

- The same moment, two encodings, two identities:
  - string `"2024-05-23T20:00:00.123Z"` -> `dd5c4e9d9242c12514672bed0e904775cda4441904c93fbb5704743f13890206`
  - integer `1716494400123` -> `66c9ec8bd3496493c064134e00736bcbd336826f3e25f0de2f81ad7d349512cf`
- Consequence: a party on the string form and a party on the integer form can
  never prove they mean the same payment. No cross-verification.

## 3. Ad-hoc / key-order-dependent canonicalization -> fails byte-reproducibility

`methods/canonicalization.py`

- The same object in two key orders hashes differently under a naive serializer:
  - order A -> `4bfb0c549c7ad02ae82432d6f11265849e68ed8e0307bc0ae4812851e3f7d6e7`
  - order B -> `90d6b51638af0608a9c168c795edde5eae8e4181877eebf521a951c1ea981aba`
- Under JCS, both orders give `cce8e66518e20342a34c2911486b5eb9bfea39c1bf44f2025241d41341089fe9`.
- Consequence: two implementations disagree on the identity of the identical
  record. Interop is impossible.

## 4. Naive "hash whatever" (no validation) -> fails adversarial rejection

`methods/adversarial_rejection.py`

- The reference rejects every malformed input; a naive method accepts each and
  mints a clean-looking identity:

  | Adversarial input | reference | naive |
  | --- | --- | --- |
  | RFC 3339 string timestamp | rejected (`ActionRefError`) | accepted -> `f03eec3a3653...` |
  | negative timestamp | rejected (`ActionRefError`) | accepted -> `6360c922f9db...` |
  | boolean timestamp | rejected (`ActionRefError`) | accepted -> `074cf50685fc...` |
  | non-hex identifier | rejected (`TransactionalError`) | accepted -> `f721dff5889e...` |
  | short identifier | rejected (`TransactionalError`) | accepted -> `1636c148ad94...` |

- Consequence: a malformed or forged record looks settled. No isolation.

## 5. Bare concatenation -> fails exactly-once (forgeable collision)

`methods/concatenation.py`

- Identity by `SHA-256(agent_id : action_type : scope : timestamp_ms)`. Two
  operationally distinct actions whose `:` falls on different field boundaries:
  - X: `action_type="screen"`, `scope="acme:order-42"`
  - Y: `action_type="screen:acme"`, `scope="order-42"`
  - both join to `agent-1:screen:acme:order-42:1716494400123` ->
    `3c903e974c86c8b3469f008e23e78543339a221ec7f73091690e383fd969feb1` (identical).
- The structured reference keeps them distinct:
  - X -> `5a73c2c33a0fdf95b83313a545f86cd81e0f2534948d6e8ce36cfd0c4a08763d`
  - Y -> `3dbdb483f16f0f6502c521850fb78d0dc91729e49976a94e5a9c44547c3fb133`
- Consequence: field boundaries are unrecoverable, so two distinct actions share
  one identity. It is also forgeable -- an actor controlling one field can
  re-target another action's identity.

## 6. camelCase field naming -> fails byte-reproducibility (cross-impl)

`methods/field_naming.py`

- The same logical action under two field-name conventions:
  - snake_case (AlgoVoi): `agent_id, action_type, scope, timestamp_ms`
  - camelCase: `agentId, actionType, scope, timestampMs`
- The two JCS-canonical forms hash to different identities -> the two
  implementations can never cross-verify. JCS fixes key order, not field names;
  the field set must be pinned.

## 7. Forward-id / operator-report binding -> not tamper-evident

`methods/settlement_binding.py`

- The substrate's `settlement_action_binding` (the four-field `binding_ref`)
  changes when the action is swapped (swap detected). A forward-id receipt (`rcpt-0001`)
  is unchanged when the action is swapped (swap NOT detected) -> the id does not
  bind the action; it only points at it.

## 8. Operator-attestation -> fails offline verifiability

`methods/offline_verification.py`

- A content-addressed identity is the hash of the bytes; a holder recomputes it
  offline and compares. An operator-assigned id is not a function of the bytes, so
  recomputing from the action yields a different value -> it cannot be verified
  offline; it requires the operator's key/endpoint, and that only proves the
  operator asserted it, not that it is true.

## 9. Issuer callback / read-at-decision -> fails offline verifiability

Architectural, not a byte demo. Verification requires querying a live issuer
endpoint, so the record cannot be verified from itself.

## 10. Amount as a JSON number -> fails exactly-once (precision loss)

`methods/amount_precision.py`

- Two atomic amounts one unit apart, `9007199254740993` and `9007199254740992`, both
  round to the same float64 -> one identity (a distinct payment dropped). The AlgoVoi
  string-encoded amount keeps them distinct; strict RFC 8785 rejects the unsafe integer.

## 11. Ad-hoc number serialization -> fails byte-reproducibility

`methods/number_canonicalization.py`

- `1.0` and `1` are the same value but serialize to different bytes under an ad-hoc
  encoder -> two implementations diverge. JCS maps both to `1`.

## 12. Rail-coupled identity -> not correlatable across rails

`methods/rail_agnostic.py`

- The AlgoVoi `action_ref` is identical across Base/Solana/Hedera (no rail in the
  identity) -> correlatable and de-duplicable across rails. A rail-coupled identity
  changes per rail, so the same action on two rails reads as two unrelated actions.

## 13. Classical-only signatures -> not quantum-resistant

`methods/pqc_signatures.py`

- AlgoVoi natively signs the canonical record with Falcon-1024 (FIPS 206, NIST L5) and
  ML-DSA-65 (FIPS 204, NIST L3); both verify over the JCS canonical bytes via
  `verify_artefact`. A classical-only stack (Ed25519/ES256) is not quantum-resistant, so
  a long-retention record loses non-repudiation once a quantum computer can forge it.

## 14. Policy version label / operator attestation -> misses silent policy rotation

`methods/policy_binding.py`

- A record sealed under policy `P` is recomputed under an edited `P'` that keeps the
  identical `policy_id` and version label (`aml.transfer/v1`), changing only a rule
  (amount ceiling raised, jurisdiction block dropped) -- a *silent* rotation.
- Content-addressed policy binding (`policy_bound_ref` over the policy bytes, bound
  to a frozen subject):
  - `policy_ref(P)`  -> `sha256:acc943b05fa8e8096e5b313288bc4f919cc2661f167c833770509a53049afa1c`
  - `policy_ref(P')` -> `sha256:8d3fadb3a401a230c8ef200ae50e4442fcfbf67c0b799860474396758847c8ed`
  - sealed under `P`     -> `sha256:2bbfbddf937276723df8d96e55697a2e5714c006e874d30123d2e44891ade08b`
  - recompute under `P'` -> `sha256:0fe26cbee4a1d9121d139697c0c95d88cd4a905114f7235ba58fa8998b651174`
  - the two differ -> rotation detected (the record fails to recompute).
- Version label: `aml.transfer/v1` under both `P` and `P'` -> unchanged -> rotation
  NOT detected. Operator attestation ("policy X applied") -> likewise unchanged.
- Consequence: with a label or an attestation, an operator can edit the rules under
  a sealed record and the record shows nothing. Only the content hash binds the
  policy bytes. (`policy_ref(P)` reproduces the published `policy_binding_v1`
  conformance value. Detectability only -- acting on the mismatch is a runtime
  verifier decision, not part of the construction.)

## The cross-cutting failure: reconciliation

`methods/reconciliation.py`

Four parties compute the identity of one payment:

| Party | Encoding | Identity | Reconciles |
| --- | --- | --- | :---: |
| 1 | integer-ms + JCS | `66c9ec8bd3...` | yes |
| 2 | integer-ms + JCS, different key order | `66c9ec8bd3...` | yes |
| 3 | RFC 3339 string timestamp | `dd5c4e9d92...` | no |
| 4 | second precision | `12824b4b65...` | no |

Only the two canonical parties share an identity. Party 3 and party 4 each land
somewhere different, so they cannot reconcile with the canonical parties, and
they do not agree with each other either. Each non-canonical form is an island.

## Summary

| Property | integer-ms + JCS (reference) | second precision | RFC 3339 string | ad-hoc canon. | naive | issuer callback |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| exactly-once | yes | **no** | yes | - | - | - |
| byte-reproducible | yes | yes | **no** | **no** | - | - |
| offline verifiable | yes | yes | yes | yes | yes | **no** |
| rejects malformed | yes | yes | yes | - | **no** | - |
| parties reconcile | yes | no | no | no | - | - |

The reference is the only method that holds all of them. Reproduce any cell:
`pip install algovoi-substrate` and run the named demo.
