<!--
  Apache-2.0. Copyright 2026 Christopher Hopley / AlgoVoi (chopmob-cloud).
-->

# Substrate Methods: a reproducible comparison

Several methods are in use for building tamper-evident records of agentic
payments. This repository puts the common ones side by side and lets you decide
with **reproducible bytes, not opinion**.

It compares those methods against a named **reference**: the **AlgoVoi JCS
(RFC 8785) Substrate**, whose load-bearing properties are pinned by conformance
vectors you can run yourself - `action_ref_exactly_once_v1` (exactly-once) and
`adversarial_isolation_v1` (rejects malformed input) - and cross-validated across
8 independent implementations (880/880 byte-for-byte). The reference is named; the
alternative methods are compared by *technique* (no competitor named). Every
verdict below is produced by a script in this repo that you can run offline, with
nothing but Python, `algovoi-substrate`, and SHA-256. If you disagree, run the
demo and read the bytes. A full failure map with the exact hashes is in
[`RESULTS.md`](./RESULTS.md).

> **What `action_ref` means here.** Throughout, `action_ref` is the **AlgoVoi
> implementation** of action_ref, adapted to AlgoVoi's own design:
> `SHA-256(JCS(RFC 8785)({agent_id, action_type, scope, timestamp_ms}))` with an
> integer-millisecond `timestamp_ms`, canon version `jcs-rfc8785-v1`. The bare name
> `action_ref` is used across the ecosystem in mutually incompatible forms (string
> timestamps, bare concatenation); this comparison's named reference is specifically
> the AlgoVoi construction, and every reference value is produced by the
> `algovoi-substrate` package itself (`action_ref`, `sha256_jcs`,
> `settlement_action_binding`).

## Coverage at a glance

Every cell below is computed live from real bytes by [`coverage.py`](./coverage.py)
(hash a real record, read the result), not entered by hand. The reference holds
every property; each alternative technique fails at least one.

| Technique | Exactly-once | Byte-reproducible | Offline-verify | Adversarial-safe |
| --- | :---: | :---: | :---: | :---: |
| **AlgoVoi JCS (RFC 8785) Substrate (action_ref)** | yes | yes | yes | yes |
| second-precision timestamp | **no** | yes | yes | yes |
| RFC 3339 string timestamp | yes | **no** | yes | yes |
| bare concatenation | **no** | yes | yes | **no** |
| naive key-order serialization | yes | **no** | yes | yes |
| camelCase field naming | yes | **no** | yes | yes |
| forward-id / operator-report binding | yes | yes | yes | **no** |
| operator-attestation (no content-address) | yes | yes | **no** | yes |
| amount as JSON number (float64) | **no** | yes | yes | yes |
| ad-hoc number serialization (1.0 vs 1) | yes | **no** | yes | yes |

Run `python coverage.py` to regenerate this table from real bytes.

Two **bindings** sit on a separate axis from the four properties above - they ask
whether a later tamper or a *silent* policy change is detectable from the record
alone. The content-addressed bindings catch it; an operator-assigned id or a
version *label* does not (`coverage.py` computes these from real bytes too):

| Binding technique | Change detected from the record alone |
| --- | :---: |
| **AlgoVoi settlement_action_binding (action swap)** | yes |
| forward-id / operator-report (action swap) | **no** |
| **AlgoVoi policy_bound_ref (silent policy rotation)** | yes |
| policy id/version label (or operator attestation) | **no** |

At realistic agentic-payment rates the cost of one of those failures
(exactly-once under a coarse timestamp) is most of the payments (counted from real
hashes; the full table is under [At scale](#at-scale)):

| Payments | second-precision dropped | integer epoch-ms dropped |
| --- | :---: | :---: |
| 100 in 1s | 98.0% | 0.0% |
| 1,000 in 1s | 99.8% | 0.0% |
| 10,000 over 10s | 99.9% | 0.0% |

### Vectors: us vs other substrate vectors, cross-validated

A comparison is only as good as the vectors behind it, and a vector set is only
trustworthy if independent implementations agree on it byte-for-byte. The
**AlgoVoi JCS (RFC 8785) Substrate** conformance corpus is published and
independently cross-validated; the common alternative is a single-implementation
vector set with no independent agreement.

| Vector set | Independent implementations | Byte-for-byte agreement | Sets / vectors |
| --- | :---: | :---: | :---: |
| **AlgoVoi JCS (RFC 8785) Substrate** | **8** (8 languages, incl. the RFC 8785 author's Java) | **880/880** | 27 / 213 |
| single-implementation vector set | 1 | none reported | varies |

Source: the public corpus
[`chopmob-cloud/algovoi-jcs-conformance-vectors`](https://github.com/chopmob-cloud/algovoi-jcs-conformance-vectors)
(manifest pins the sets, vectors, and the cross-validation runs). Run them yourself.

### Adversarial rejection: single-implementation vs cross-implementation

Rejecting a malformed input is a property of the validator, not of the bytes. A
single-implementation conformance set can show its own reference implementation
rejecting an attack. It cannot show that independent implementations reject it the
same way.

The AlgoVoi adversarial set is cross-validated across all eight implementations:
every one accepts the valid control and rejects each of the eleven isolated attacks
(a non-integer timestamp, a non-hex action reference, an empty state, a broken chain
link, a stale content hash, and so on). Eight implementations times twelve vectors
is 96 fail-closed verdicts, all green.

| Property | single-implementation set | AlgoVoi (8 implementations) |
| --- | :---: | :---: |
| Input bytes agree across implementations | not shown | yes |
| Every implementation rejects each attack identically | not shown (one impl) | 96/96 |

Reference-implementation rejection runs here in
[`methods/adversarial_rejection.py`](./methods/adversarial_rejection.py). The eight
independent implementations all failing closed on the same attacks, with its
attestation, is in the corpus at `composition/adversarial_gauntlet/` (one command:
`bash run_gauntlet.sh`).

Regenerate everything (methods + results + graphs) from one command:
`python run_all.py`.

## The reference: what the substrate holds

The comparison is anchored on two properties the published substrate proves, both
reproducible from a single command:

- **Exactly-once** (`action_ref_exactly_once_v1`) - a genuine retry collapses to
  the same identity (skipped, no double spend); a distinct action stays distinct;
  a non-committed state cannot pass as settled. Demo:
  [`methods/secondary_attempts.py`](./methods/secondary_attempts.py).
- **Adversarial rejection** (`adversarial_isolation_v1`) - malformed inputs (an
  RFC 3339 timestamp, a negative, a boolean, a non-hex or short identifier) are
  rejected at the validation layer, not hashed into a clean-looking identity.
  Demo: [`methods/adversarial_rejection.py`](./methods/adversarial_rejection.py).

Every method below is measured against these two properties, plus byte
reproducibility and offline verifiability.

## What "works" means here

A method is judged only against the three properties that actually matter for a
regulated agentic payment record:

- **Exactly-once identity** - two operationally distinct actions must get two
  distinct identifiers. If two real payments can collapse to one identifier, the
  second is indistinguishable from a retry and can be silently dropped.
- **Cross-implementation byte-reproducibility** - the same logical record must
  hash to the same bytes in every language and on every platform, or independent
  parties cannot verify each other.
- **Offline verifiability** - a holder of the record can verify it with a hash
  function and a JSON parser, without calling back to the issuer.

## Timestamp encoding

| Method | Exactly-once | Byte-reproducible | Offline | Demo |
| --- | :---: | :---: | :---: | --- |
| integer epoch-millisecond | yes | yes | yes | [`methods/timestamp_encoding.py`](./methods/timestamp_encoding.py) |
| second precision | **no** | yes | yes | same |
| RFC 3339 string | yes | **no** (string vs number diverges) | yes | same |

`methods/timestamp_encoding.py` shows it directly: under second precision, two
payments 753 ms apart collapse to one identifier (exactly-once breaks); under an
RFC 3339 string the same moment produces a different identifier than the integer
form, so the two cannot cross-verify.

### At scale

The single-collision case is not an edge case; it is the common case at volume.
[`methods/scale.py`](./methods/scale.py) computes the REAL `action_ref` of every
payment in a burst and counts how many collide (a collision is a real payment
dropped, because it is indistinguishable from a retry):

| Payments | integer epoch-millisecond dropped | second precision dropped |
| --- | :---: | :---: |
| 100 in 1 second | 0% | 99.0% |
| 1,000 in 1 second | 0% | 99.9% |
| 10,000 over 10 seconds | 0% | 99.9% |
| 60,000 over 60 seconds | 0% | 99.9% |
| 100,000 over 100 seconds | 0% | 99.9% (only 100 of 100,000 survive) |

At any realistic agentic payment rate, second precision loses more than 99% of
payments; integer epoch-millisecond loses none. To be precise rather than
absolute: integer-millisecond also has a resolution limit (one identity per
millisecond, so ~1000 payments/second), but that ceiling is 1000x higher than
second precision and sits far above any real workload. These are counted from
real hashes, not modelled.

**Measured in a clean container.** A fresh `python:3.12-slim` install of the
published packages (`algovoi-substrate`, `algovoi-policy-binding`,
`algovoi-compliance-gate-lite` from PyPI) reproduces 1,000,000 distinct `action_ref`
values with zero collisions, and the second-precision drop above (99.8 to 99.9
percent) exactly. Collision freedom is a property of the construction and is the
same on any host. Throughput is the host's: on a single core the million completed
in about 8.5 seconds (roughly 118,000 per second), with the full `policy_ref` plus
`policy_bound_ref` plus `gate_ref` chain at about 43,000 per second. Both scale with
cores. A blank `node:20-slim` box reproduces the same `policy_bound_ref` and
`gate_ref` values byte for byte from the npm packages.

## RFC 3339 millisecond-string grammar

Pinning the timestamp to an RFC 3339 *millisecond* string does not make it
byte-stable. One instant has several valid encodings, so honest producers still
diverge.

| Technique | Byte-reproducible across producers | Demo |
| --- | :---: | --- |
| AlgoVoi integer epoch-millisecond | yes (one representation) | [`methods/rfc3339_grammar.py`](./methods/rfc3339_grammar.py) |
| RFC 3339 millisecond string | **no** (`.123Z`, `.123+00:00`, `.123000Z` are one instant, three byte sequences) | same |

`methods/rfc3339_grammar.py` hashes three valid RFC 3339 encodings of a single
instant and shows they produce three different identities, while the integer
epoch-millisecond form has exactly one.

## Handling secondary attempts (the working method)

The reason timestamp precision matters is what happens on a *secondary attempt*.
A content-addressed exactly-once method uses the action identity itself to tell
a genuine retry from a distinct action. [`methods/secondary_attempts.py`](./methods/secondary_attempts.py)
demonstrates all four behaviours:

| Secondary attempt | Behaviour |
| --- | --- |
| identical action re-presented (genuine retry) | same identity -> absorbed, SKIPPED, no double spend |
| distinct action 1 ms later | different identity -> processed as new, not skipped |
| a non-committed (PENDING) state | different hash -> cannot pass as settled |
| a different party, identical parameters | different identity -> cannot impersonate another's action |

This is why a coarser timestamp is not a free simplification: it removes the
method's ability to distinguish a distinct action from a retry, which is the
exact failure quantified in the scale table above. Precision and correct
secondary-attempt handling are the same property viewed from two sides.

## Canonicalization

| Method | Byte-reproducible across implementations | Demo |
| --- | :---: | --- |
| JCS (RFC 8785) | yes | [`methods/canonicalization.py`](./methods/canonicalization.py) |
| ad-hoc / key-order-dependent serialization | **no** | same |

`methods/canonicalization.py` shows that JCS hashes the same logical object to
identical bytes regardless of input key order, while a naive serialization
produces different bytes for the same object, so two implementations disagree.

## Unicode normalization and UTF-8 emission

RFC 8785 performs no Unicode normalization and emits printable non-ASCII as
literal UTF-8. An implementation that normalizes a string, or escapes non-ASCII
as `\uXXXX`, changes the bytes and the identity.

| Technique | Byte-reproducible across implementations | Demo |
| --- | :---: | --- |
| hash the signed bytes as received (RFC 8785, literal UTF-8) | yes | [`methods/unicode_normalization.py`](./methods/unicode_normalization.py) |
| normalize NFC/NFD, or `\u`-escape non-ASCII, before hashing | **no** | same |

`methods/unicode_normalization.py` shows NFC and NFD of the same glyph hash to
different identities, and that a `\u`-escaping serializer diverges from the
canonical literal-UTF-8 bytes.

## Concatenation vs structured identity

A common shortcut derives the action identity by joining the fields into one
string and hashing it: `SHA-256(agent_id : action_type : scope : timestamp_ms)`.
The delimiter can also appear *inside* a field value, so the field boundaries are
not recoverable and two operationally distinct actions can produce the identical
joined string -- and therefore the identical identity.

| Method | Exactly-once | Adversarial-safe | Demo |
| --- | :---: | :---: | --- |
| structured object under JCS (`action_ref`) | yes | yes | [`methods/concatenation.py`](./methods/concatenation.py) |
| delimiter-joined concatenation | **no** | **no** (forgeable collision) | same |

[`methods/concatenation.py`](./methods/concatenation.py) shows it with real
hashes: two distinct actions (`action_type="screen", scope="acme:order-42"` vs
`action_type="screen:acme", scope="order-42"`) collapse to **one** concatenation
identity, while the structured `action_ref` keeps them distinct. A coalition that
standardises on a delimiter-joined `action_ref` inherits this collision; the
structured form does not have it. It is also an attack surface: an actor who
controls one field can re-target another action's identity.

## Field-name determinism

JCS fixes key *order* and value encoding, but it canonicalises whatever field
*names* it is given. The field set must be pinned, or two implementations diverge.

| Technique | Byte-reproducible across implementations | Demo |
| --- | :---: | --- |
| AlgoVoi snake_case field set (`agent_id, action_type, scope, timestamp_ms`) | yes | [`methods/field_naming.py`](./methods/field_naming.py) |
| camelCase variant (`agentId, actionType, scope, timestampMs`) | **no** | same |

`methods/field_naming.py` hashes the same logical action under both conventions and
shows the identities never match.

## Settlement &lt;-&gt; action binding

| Technique | Tamper-evident (action swap detected) | Demo |
| --- | :---: | --- |
| AlgoVoi content-addressed binding (substrate `settlement_action_binding` -> `binding_ref`) | yes | [`methods/settlement_binding.py`](./methods/settlement_binding.py) |
| forward-id / operator-report (settlement carries an assigned receipt id) | **no** | same |

`methods/settlement_binding.py` swaps the action and shows the content-addressed
binding breaks (caught), while the forward id is unchanged (not caught) -- so a
forward id does not actually bind.

## Policy binding (which ruleset was in force, and silent rotation)

A record should be able to prove *which* policy was in force when it was sealed,
and a later change to that policy should be detectable from the record alone. The
hard case is a **silent rotation**: the operator keeps the same `policy_id` and
version *label* but edits a rule. A content hash of the policy catches it; a
label or an "operator applied policy X" attestation does not.

| Technique | Silent rotation detected (same label, edited rule) | Demo |
| --- | :---: | --- |
| AlgoVoi content-addressed binding (`policy_bound_ref` over the policy bytes, bound to a frozen subject) | yes | [`methods/policy_binding.py`](./methods/policy_binding.py) |
| policy id/version label carried in the record | **no** | same |
| operator attestation ("policy X was applied") | **no** | same |

`methods/policy_binding.py` seals a record under policy `P`, then recomputes under
an edited `P'` that keeps the identical `policy_id`/version label: the
`policy_bound_ref` changes (rotation caught), while the label and the attestation
are unchanged (rotation invisible). `policy_ref` / `policy_bound_ref` are the
`algovoi-policy-binding` package (Apache-2.0), additive over the frozen substrate.

This proves *detectability* - version-provable and rotation-detectable, offline,
from bytes. Acting on a detected mismatch (rejecting the record) is a runtime
verifier decision, not a property of the construction; it is listed here as the
detectability demo, not an enforcement claim.

## Replay resistance (instance-binding vs content-binding)

A content-addressed identity is derived from content alone, so two distinct
executions with identical content share one identity, and a replay cannot be told
from a real second execution. Binding the action to its settlement instance keeps
them apart.

| Technique | Distinct executions stay distinct | Demo |
| --- | :---: | --- |
| AlgoVoi binding_ref (action_ref + settlement payment hash) | yes | [`methods/replay_resistance.py`](./methods/replay_resistance.py) |
| content-address only (identity from content) | **no** (identical content gives one identity) | same |

`methods/replay_resistance.py` shows two identical-content executions collapse to
one content-address, while the binding_ref over each settlement instance keeps
them distinct. The substrate is instance-bound, not only content-bound.

## Offline verifiability

| Technique | Verifiable from bytes alone (no issuer call) | Demo |
| --- | :---: | --- |
| AlgoVoi content-addressed identity | yes | [`methods/offline_verification.py`](./methods/offline_verification.py) |
| operator-attestation (operator-assigned id, operator-signed) | **no** (needs issuer key/endpoint; proves assertion, not truth) | same |

## JWS envelope vs claims object

A signed receipt can be content-addressed over the JWS compact form or over the
JCS-canonical claims object. The compact form is not unique: any intermediary
that re-serializes or re-signs changes it, so a hash over the envelope breaks on
re-encoding.

| Technique | Survives re-encoding by an intermediary | Demo |
| --- | :---: | --- |
| hash the JCS-canonical claims object | yes | [`methods/jws_reencoding.py`](./methods/jws_reencoding.py) |
| hash the JWS compact form (header.payload.signature) | **no** (re-encode or re-sign gives different bytes) | same |

`methods/jws_reencoding.py` carries the same claims through two producers and
shows the compact-form hash diverges while the JCS claims-object hash is
identical.

## Amount precision

| Technique | Exactly-once | Demo |
| --- | :---: | --- |
| AlgoVoi atomic amount as a string | yes | [`methods/amount_precision.py`](./methods/amount_precision.py) |
| amount as a JSON number (float64) | **no** (rounds past 2^53; two amounts -> one identity) | same |

Atomic on-chain amounts exceed JSON's safe-integer range; a JSON-number amount
silently rounds, collapsing distinct payments. AlgoVoi encodes the atomic amount as
a string (and strict RFC 8785 rejects the unsafe integer outright).

## Number canonicalization

| Technique | Byte-reproducible across implementations | Demo |
| --- | :---: | --- |
| AlgoVoi JCS (RFC 8785) number form | yes (`1.0` -> `1`, `1e3` -> `1000`) | [`methods/number_canonicalization.py`](./methods/number_canonicalization.py) |
| ad-hoc serialization (preserves spelling) | **no** (`1.0` != `1`) | same |

## Rail-agnostic identity

The AlgoVoi `action_ref` carries no settlement rail, so the same action has one
identity across Base, Solana, Hedera, and every other rail, and a verifier
correlates and de-duplicates it across rails. A rail-coupled identity changes per
rail, so the same action on two rails looks like two unrelated actions.

| Technique | Correlatable across rails | Demo |
| --- | :---: | --- |
| AlgoVoi action_ref (no rail in the identity) | yes | [`methods/rail_agnostic.py`](./methods/rail_agnostic.py) |
| rail-coupled identity (rail folded into the hash) | **no** | same |

## Post-quantum signatures

The AlgoVoi substrate natively signs and verifies the canonical record with
post-quantum algorithms, over the same JCS (RFC 8785) bytes as the classical path. A
long-retention payment record signed only with a classical scheme loses its
non-repudiation once those signatures become forgeable by a quantum computer.

| Signing | Quantum-resistant | Demo |
| --- | :---: | --- |
| AlgoVoi native PQC: Falcon-1024 (FIPS 206, L5) + ML-DSA-65 (FIPS 204, L3) | yes | [`methods/pqc_signatures.py`](./methods/pqc_signatures.py) |
| classical-only: Ed25519 / ES256 | **no** | same |

`methods/pqc_signatures.py` produces real Falcon-1024 and ML-DSA-65 signatures over an
`action_ref` record and verifies them with the substrate's `verify_artefact` (requires
`algovoi-substrate-pqc`). The algorithm-family classification is the substrate's own
registry; the PQC signatures cover the same `expected_jcs_bytes_b64` as the classical path.

## Reconciliation: do independent parties agree?

**Reconciliation** is when two or more independent parties to the same payment
each compute the record's identity from their own copy of the data, then check
that they arrived at the same answer. It is how a payer, a payee, and an auditor
confirm they are describing the same event - without trusting any one party's
word for it, and without a central server to ask.

For that to work, every party must derive the *same bytes* from the same record.
So reconciliation is only possible on a shared canonical form: if two parties
encode the record differently, they compute different identities and can never
prove they are talking about the same payment.

A regulated payment has several such parties - payer, payee, auditor,
facilitator - so this is the real test of a substrate, not a nicety.
[`methods/reconciliation.py`](./methods/reconciliation.py) runs four parties over
one payment:

| Party | Encoding | Reconciles |
| --- | --- | :---: |
| 1 | integer-ms + JCS | yes |
| 2 | integer-ms + JCS, fields in a different key order | yes |
| 3 | RFC 3339 string timestamp | no |
| 4 | second precision | no |

The two canonical parties agree byte-for-byte even though one ordered its fields
differently - JCS absorbs that. The two non-canonical parties each land on a
different identity, so they cannot reconcile with the canonical parties **or with
each other**. Interoperability is not a feature added later; it is a property of
the form. Only the canonical form produces an identity independent parties can
share.

## Verification model (architectural, not a byte demo)

| Method | Offline verifiable | Note |
| --- | :---: | --- |
| offline content-addressed | yes | holder verifies with SHA-256 + JSON parser; no issuer contact |
| issuer callback / read-at-decision-time | **no** | verification requires querying a live issuer endpoint |

This row is a property of the design, not something a single script proves; it
is listed for completeness and marked as such.

## Run it

```bash
pip install algovoi-substrate algovoi-policy-binding
python methods/secondary_attempts.py     # reference: exactly-once
python methods/adversarial_rejection.py  # reference: rejects malformed input
python methods/timestamp_encoding.py
python methods/scale.py
python methods/canonicalization.py
python methods/settlement_binding.py    # binding survives an action swap?
python methods/policy_binding.py        # silent policy rotation detected?
python methods/reconciliation.py        # do independent parties agree?
```

Each prints its comparison and exits `0` when the demonstrated properties hold.

## Why this exists

Choosing a substrate method is a one-way door: records made under one method do
not interoperate with another, and some methods quietly fail properties you only
notice in production. The intent here is to make that choice on the merits,
before the door closes, with evidence anyone can reproduce.

## License

Apache License, Version 2.0. Copyright 2026 Christopher Hopley / AlgoVoi
(chopmob-cloud). The reference substrate used by the demos is published as
`algovoi-substrate` (PyPI) under the same license.
