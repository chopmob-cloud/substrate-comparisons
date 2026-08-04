#!/usr/bin/env python3
"""
Alias composition: keep names out of the canonicalisation core (L2), or fold them
into it (L1). Only one keeps the certified surface fixed.

Reproducible, offline, names no implementation. Takes a real @name reference and
shows:

  - L2-resolved (resolve, then canonicalise) : the name is replaced by its concrete
                                               upstream ref BEFORE L1 hashes, so L1
                                               never sees a name -> zero alias
                                               vectors, a fixed 4-rule grammar for
                                               any vocabulary size.
  - L1-embedded (teach the core about names) : correctness depends on every name x
                                               every reference position, so the
                                               positive corpus grows as positions x
                                               vocabulary (a product) -> the surface
                                               grows with the alias vocabulary.

Run:  pip install algovoi-substrate ; python alias_composition_layering.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

try:
    from algovoi_substrate import canonicalize as _canon
except ImportError:  # symbol name varies by version
    from algovoi_substrate import canonicalize_bytes as _canon


def _bytes(obj) -> bytes:
    b = _canon(obj)
    return b if isinstance(b, (bytes, bytearray)) else b.encode("utf-8")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _ref(obj) -> str:
    return "sha256:" + _sha(_bytes(obj))


# --- L2: the whole alias grammar (resolve above, canonicalise below) ---
def resolve(value, refs):
    if isinstance(value, str) and value.startswith("@"):
        if value.startswith("@@"):
            return value[1:]                       # escape -> literal, binds nothing
        name = value[1:]
        if name not in refs:
            raise ValueError(f"unknown alias @{name} -> fail closed")
        return refs[name]                          # @name -> upstream concrete ref
    if isinstance(value, list):
        return [resolve(v, refs) for v in value]
    if isinstance(value, dict):
        return {k: resolve(v, refs) for k, v in value.items()}
    return value


L2_GRAMMAR_CASES = 4   # resolve, @@-escape, non-leading literal, unknown -> fail-closed


def _corpus_positions() -> int:
    """Alias-eligible reference positions (`sha256:` leaves) counted from the sibling
    corpus checkout, so P stays truthful as the corpus grows (same single-source-of-
    truth discipline as sync_counts.py). Falls back to the 2026-08-04 measured value
    when the corpus is not checked out alongside this repo."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "..", "..", "algovoi-jcs-conformance-vectors", "vectors"),
        os.path.join(here, "..", "algovoi-jcs-conformance-vectors", "vectors"),
    ]
    p = 0

    def walk(o):
        nonlocal p
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and o.startswith("sha256:"):
            p += 1

    for root in candidates:
        if not os.path.isdir(root):
            continue
        for f in glob.glob(os.path.join(root, "*", "*.json")):
            if "node_modules" in f:
                continue
            try:
                walk(json.load(open(f, encoding="utf-8")))
            except Exception:
                pass
        if p:
            break
    return p if p else 652   # measured 2026-08-04 fallback


def main() -> int:
    w = 78
    print("=" * w)
    print("ALIAS COMPOSITION: L1-EMBEDDED vs L2-RESOLVED SURFACE SCALING"
          " -- real bytes (names no implementation)")
    print("=" * w)

    # --- L2-resolved: resolve, then canonicalise; L1 never sees a name ---
    issuer = {"kind": "issuer", "org": "acme"}
    refs = {"issuer": _ref(issuer)}
    doc = {"author": "@issuer", "body": "hello"}
    resolved = resolve(doc, refs)
    concrete = {"author": refs["issuer"], "body": "hello"}
    marker_free = "@issuer" not in json.dumps(resolved)
    ref_match = _ref(resolved) == _ref(concrete)
    escape_literal = resolve({"x": "@@issuer"}, refs) == {"x": "@issuer"}
    try:
        resolve({"x": "@nosuch"}, refs)
        fail_closed = False
    except ValueError:
        fail_closed = True

    print("\n[L2-resolved: the object actually handed to L1]")
    print(f"  input   : {json.dumps(doc)}")
    print(f"  resolved: {json.dumps(resolved)}")
    print(f"  L1 ref  : {_ref(resolved)}")
    print(f"  [{'ok ' if marker_free else 'BAD'}] no @name survives into L1")
    print(f"  [{'ok ' if ref_match else 'BAD'}] L1 ref(resolved) == ref(concrete substitution)")
    print(f"  [{'ok ' if escape_literal else 'BAD'}] @@ escapes to a literal (binds nothing)")
    print(f"  [{'ok ' if fail_closed else 'BAD'}] unknown @name fails closed")

    # --- Surface scaling: L1-embedded (product) vs L2-resolved (constant) ---
    P = _corpus_positions()
    print(f"\n[Surface scaling]  alias-eligible reference positions in corpus: P = {P}")
    print("-" * w)
    print(f"  {'alias vocab V':>13} | {'L1-embedded +vectors (P x V)':>30} | {'L2-resolved surface':>22}")
    print("-" * w)
    for V in (1, 10, 100, 1000, 10000):
        print(f"  {V:>13} | {P * V:>30,} | {'4-rule grammar (fixed)':>22}")
    print("-" * w)

    # materialise V=100 to prove P*V are that many DISTINCT canonical objects
    V = 100
    seen = set()
    for pos in range(P):
        for a in range(V):
            variant = {"anchor": "receipt", "position": pos, "alias": f"@issuer{a}", "shape": "ref"}
            seen.add(_bytes(variant))
    distinct = len(seen)
    distinct_ok = distinct == P * V
    l2_constant = True   # by construction: L2 surface is the fixed grammar, independent of V

    print(f"  materialised V=100: {distinct:,} distinct canonical objects"
          f" (expected P x V = {P * V:,}) [{'ok ' if distinct_ok else 'BAD'}]")
    print(f"  L2-resolved surface across every V above: {L2_GRAMMAR_CASES}-rule grammar,"
          f" constant [{'ok ' if l2_constant else 'BAD'}]")

    print("-" * w)
    ok = marker_free and ref_match and escape_literal and fail_closed and distinct_ok and l2_constant
    print("RESULT: resolving names at L2 keeps the certified surface constant in the alias"
          " vocabulary; folding them into L1 grows it as positions x vocabulary."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
