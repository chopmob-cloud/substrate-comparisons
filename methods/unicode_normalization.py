#!/usr/bin/env python3
"""
Unicode normalisation + UTF-8 emission: two footguns RFC 8785 makes explicit.

Reproducible, offline, names no implementation. RFC 8785 (JCS) performs NO Unicode
normalisation and emits printable non-ASCII as literal UTF-8. Two consequences:

  - NFC vs NFD: the same glyph in composed (NFC) and decomposed (NFD) form is two
    different byte sequences, so it hashes to two different refs. An implementer
    who normalises a string before hashing matches the wrong ref.
  - UTF-8 emission: a serialiser that escapes non-ASCII as \\uXXXX (for example a
    naive json.dumps with ensure_ascii=True) produces different bytes than the
    literal UTF-8 RFC 8785 requires -- a common cause of one implementation
    diverging from the rest.

Run:  pip install algovoi-substrate ; python unicode_normalization.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import json
import sys
import unicodedata

from algovoi_substrate import canonicalize


def _sha_jcs(obj: dict) -> str:
    c = canonicalize(obj)
    return hashlib.sha256(c.encode("utf-8") if isinstance(c, str) else c).hexdigest()


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main() -> int:
    w = 70
    print("=" * w)
    print("UNICODE NORMALISATION + UTF-8 EMISSION -- reproducible comparison (names no implementation)")
    print("=" * w)

    name_nfc = unicodedata.normalize("NFC", "café")   # 'é' = U+00E9 (composed)
    name_nfd = unicodedata.normalize("NFD", "café")   # 'e' + U+0301 (decomposed)
    nfc_differs = name_nfc != name_nfd                     # same glyph, different code points
    h_nfc = _sha_jcs({"merchant": name_nfc})
    h_nfd = _sha_jcs({"merchant": name_nfd})
    nfc_hash_differs = h_nfc != h_nfd
    print("[NFC vs NFD of the same glyph]  (RFC 8785 does NO normalisation)")
    print(f"  NFC -> {h_nfc}")
    print(f"  NFD -> {h_nfd}")
    print(f"  differs: {nfc_hash_differs}  -> do NOT normalise before hashing; the signed bytes are authoritative\n")

    literal = _sha_jcs({"merchant": name_nfc})             # RFC 8785: literal UTF-8
    escaped = _sha(json.dumps({"merchant": name_nfc}, ensure_ascii=True, separators=(",", ":")))
    emit_differs = literal != escaped
    print("[literal UTF-8 vs \\u-escaped emission]  (same string, two serialisers)")
    print(f"  RFC 8785 literal UTF-8 -> {literal}")
    print(f"  ensure_ascii escape    -> {escaped}")
    print(f"  differs: {emit_differs}  -> a \\u-escaping serialiser diverges from the canonical bytes\n")

    print("-" * w)
    ok = nfc_differs and nfc_hash_differs and emit_differs
    print("RESULT: RFC 8785 normalises nothing and emits literal UTF-8, so NFC/NFD and "
          "\\u-escaping each change the bytes and the ref. Hash the signed bytes as received."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
