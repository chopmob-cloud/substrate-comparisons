<!--
  Apache-2.0. Copyright 2026 Christopher Hopley / AlgoVoi (chopmob-cloud).
-->

# Substrate Methods: a reproducible comparison

Several methods are in use for building tamper-evident records of agentic
payments. This repository puts the common ones side by side and lets you decide
with **reproducible bytes, not opinion**.

It compares those methods against a **reference**: the published AlgoVoi
substrate, whose two load-bearing properties are pinned by conformance vectors
you can run yourself - `action_ref_exactly_once_v1` (exactly-once) and
`adversarial_isolation_v1` (rejects malformed input). The alternative methods are
named only by *technique* - no project, no person. Every verdict below is
produced by a script in this repo that you can run offline, with nothing but
Python, `algovoi-substrate`, and SHA-256. If you disagree, run the demo and read
the bytes. A full failure map with the exact hashes is in [`RESULTS.md`](./RESULTS.md).

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
pip install algovoi-substrate
python methods/secondary_attempts.py     # reference: exactly-once
python methods/adversarial_rejection.py  # reference: rejects malformed input
python methods/timestamp_encoding.py
python methods/scale.py
python methods/canonicalization.py
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
