#!/usr/bin/env python3
"""
Keep the corpus-derived counts in this comparison in sync with the single source
of truth: the AlgoVoi JCS conformance corpus manifest. The sets / vectors totals
(and the 8-implementation cross-validation figure) are NOT entered by hand here;
they are read from the corpus and either checked or written into the docs.

This is what makes the comparison *updateable*: when the corpus grows (a new
anchor set ships), run this and the comparison reflects it, instead of drifting.

Usage:
  python sync_counts.py --check                 # report drift, exit 1 if any
  python sync_counts.py --write                 # update README.md in place
  python sync_counts.py --check  <extra.mdx>    # also check extra files (e.g. the docs page)
  python sync_counts.py --write  <extra.mdx>    # also write extra files
  python sync_counts.py --manifest <path>       # override corpus manifest path

Default manifest path: ../algovoi-jcs-conformance-vectors/manifest.json (sibling checkout).
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MANIFEST = os.path.join(HERE, "..", "algovoi-jcs-conformance-vectors", "manifest.json")
DEFAULT_CORPUS_README = os.path.join(HERE, "..", "algovoi-jcs-conformance-vectors", "README.md")


def authoritative_counts(manifest_path: str) -> tuple[int, int, str]:
    """Read sets / vectors from the corpus manifest AND revalidate the manifest is
    internally consistent before we trust it (sets == len(anchor_sets);
    vectors == sum of per-set vector_count)."""
    with open(manifest_path, encoding="utf-8") as f:
        m = json.load(f)
    sets_field = int(m["total_anchor_sets"])
    vectors_field = int(m["total_vectors"])
    anchor = m.get("anchor_sets", [])
    sets_actual = len(anchor)
    vectors_actual = sum(int(s.get("vector_count", 0)) for s in anchor)
    problems = []
    if sets_field != sets_actual:
        problems.append(f"total_anchor_sets {sets_field} != len(anchor_sets) {sets_actual}")
    if vectors_field != vectors_actual:
        problems.append(f"total_vectors {vectors_field} != sum(vector_count) {vectors_actual}")
    if problems:
        raise SystemExit("CORPUS MANIFEST INCONSISTENT: " + "; ".join(problems))
    return sets_field, vectors_field, str(m.get("version", "?"))


def crossval_figure(corpus_readme_path: str) -> str | None:
    """The 8-implementation directly-executed figure (e.g. 880/880) from the corpus
    README badge. Used as a read-only consistency check, not rewritten here."""
    try:
        txt = open(corpus_readme_path, encoding="utf-8").read()
    except OSError:
        return None
    m = re.search(r"cross--validated-(\d+)%2F(\d+)", txt)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def _patterns(sets: int, vectors: int) -> list[tuple[re.Pattern, str]]:
    """Count-bearing phrasings tied to the corpus totals. Specific enough not to
    touch other ratios in the docs (880/880, 96/96, 192/192, etc.)."""
    return [
        # "28 sets / 223 vectors"
        (re.compile(r"\b\d+ sets / \d+ vectors\b"), f"{sets} sets / {vectors} vectors"),
        # "28 anchor sets, 223 vectors"
        (re.compile(r"\b\d+ anchor sets, \d+ vectors\b"), f"{sets} anchor sets, {vectors} vectors"),
        # the named-reference table row, last cell: "... | 28 / 223 |"
        (re.compile(r"(AlgoVoi JCS \(RFC 8785\) Substrate\*\*.*?\| )\d+ / \d+( \|)"),
         rf"\g<1>{sets} / {vectors}\g<2>"),
    ]


def process(path: str, sets: int, vectors: int, write: bool) -> tuple[int, list[str]]:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    pats = _patterns(sets, vectors)
    changes: list[str] = []
    new_text = text
    for pat, repl in pats:
        def _sub(mo: re.Match) -> str:
            before = mo.group(0)
            after = pat.sub(repl, before)
            if after != before:
                changes.append(f"{os.path.basename(path)}: {before.strip()[:60]!r} -> {after.strip()[:60]!r}")
            return after
        new_text = pat.sub(_sub, new_text)
    if write and new_text != text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
    return (1 if new_text != text else 0), changes


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync corpus-derived counts into the comparison.")
    ap.add_argument("--check", action="store_true", help="report drift, exit 1 if any")
    ap.add_argument("--write", action="store_true", help="update files in place")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("extra", nargs="*", help="extra files to check/write (e.g. the docs mdx)")
    args = ap.parse_args()
    if not (args.check or args.write):
        ap.print_help()
        return 2

    sets, vectors, version = authoritative_counts(args.manifest)
    xval = crossval_figure(DEFAULT_CORPUS_README)
    print(f"corpus manifest {version}: {sets} sets / {vectors} vectors"
          + (f" | cross-validation {xval}" if xval else ""))

    targets = [os.path.join(HERE, "README.md")] + [os.path.abspath(p) for p in args.extra]
    drift = 0
    all_changes: list[str] = []
    for t in targets:
        if not os.path.exists(t):
            print(f"  [skip] {t} (not found)")
            continue
        d, changes = process(t, sets, vectors, write=args.write)
        drift += d
        all_changes.extend(changes)
        verb = "updated" if (args.write and d) else ("DRIFT" if d else "in sync")
        print(f"  [{verb}] {t}")

    for c in all_changes:
        print("    -", c)

    if xval:
        for t in targets:
            if os.path.exists(t) and xval not in open(t, encoding="utf-8").read():
                print(f"  [warn] {os.path.basename(t)} does not mention cross-validation figure {xval}")

    if args.check and drift:
        print(f"\nRESULT: DRIFT in {drift} file(s). Run with --write to update.")
        return 1
    print("\nRESULT: in sync." if not drift else f"\nRESULT: wrote {drift} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
