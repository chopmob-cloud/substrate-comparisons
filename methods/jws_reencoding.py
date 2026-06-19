#!/usr/bin/env python3
"""
JWS envelope vs claims object: which content-address survives an intermediary.

Reproducible, offline, names no implementation. A signed receipt can be
content-addressed two ways:

  - over the JWS COMPACT form: base64url(header).base64url(payload).base64url(sig)
  - over the JCS-canonical CLAIMS OBJECT: SHA-256(JCS(RFC 8785)(claims))

The compact form is not unique. Any intermediary that re-serialises the header or
payload, or re-signs, produces a different compact string for the SAME claims, so
a hash taken over the compact form breaks on re-encoding. The hash over the JCS
claims object is identical for every encoding of the same claims, so it
cross-verifies through any number of intermediaries.

Run:  pip install algovoi-substrate ; python jws_reencoding.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys

from algovoi_substrate import sha256_jcs

CLAIMS = {"agent_id": "agent-1", "action_type": "payment",
          "scope": "settlement", "timestamp_ms": 1716494400123}


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _compact(header: dict, payload_json: str, sig: bytes) -> str:
    # A valid JWS compact serialisation: header.payload.signature (base64url).
    return ".".join([_b64u(json.dumps(header, separators=(",", ":")).encode("utf-8")),
                     _b64u(payload_json.encode("utf-8")),
                     _b64u(sig)])


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main() -> int:
    w = 70
    print("=" * w)
    print("JWS ENVELOPE vs CLAIMS OBJECT -- reproducible comparison (names no implementation)")
    print("=" * w)
    print("the same claims, carried by two honest producers / intermediaries:\n")

    # Producer A: header {alg}, payload in author order, signature s_A.
    payload_a = json.dumps(CLAIMS, separators=(",", ":"))
    compact_a = _compact({"alg": "ES256"}, payload_a, b"signature-A-bytes")

    # Producer B (or a relaying intermediary): adds `typ` to the header,
    # re-serialises the payload with sorted keys, and re-signs -> different
    # compact bytes, IDENTICAL claims.
    payload_b = json.dumps(CLAIMS, sort_keys=True)
    compact_b = _compact({"alg": "ES256", "typ": "JWT"}, payload_b, b"signature-B-bytes")

    ca, cb = _sha(compact_a), _sha(compact_b)
    compact_breaks = ca != cb
    print("[hash over the JWS compact form]")
    print(f"  producer A -> {ca}")
    print(f"  producer B -> {cb}")
    print(f"  diverges: {compact_breaks}  -> re-encoding / re-signing breaks the match\n")

    ja = sha256_jcs(CLAIMS)
    jb = sha256_jcs(json.loads(payload_b))   # same claims, decoded from B's payload
    claims_stable = ja == jb
    print("[hash over the JCS-canonical claims object]")
    print(f"  producer A -> {ja}")
    print(f"  producer B -> {jb}")
    print(f"  identical: {claims_stable}  -> cross-verifies through any intermediary\n")

    print("-" * w)
    ok = compact_breaks and claims_stable
    print("RESULT: a hash over the JWS compact form breaks on re-encoding; a hash over the JCS "
          "claims object is stable across producers and intermediaries. Bind to the claims, not "
          "to the envelope."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
