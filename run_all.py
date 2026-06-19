#!/usr/bin/env python3
"""
Run the whole comparison from one command: every method demo + regenerate the
graphs. Real bytes throughout; names no implementation.

Run:  pip install algovoi-substrate ; python run_all.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
METHODS = [
    "timestamp_encoding.py",
    "rfc3339_grammar.py",
    "secondary_attempts.py",
    "concatenation.py",
    "canonicalization.py",
    "unicode_normalization.py",
    "field_naming.py",
    "settlement_binding.py",
    "replay_resistance.py",
    "policy_change.py",
    "fail_closed.py",
    "offline_verification.py",
    "jws_reencoding.py",
    "amount_precision.py",
    "number_canonicalization.py",
    "rail_agnostic.py",
    "pqc_signatures.py",
    "adversarial_rejection.py",
    "reconciliation.py",
    "scale.py",
]


def _run(path: str) -> int:
    r = subprocess.run([sys.executable, path], cwd=HERE)
    return r.returncode


def main() -> int:
    fails = []
    for m in METHODS:
        p = os.path.join(HERE, "methods", m)
        if not os.path.exists(p):
            continue
        print(f"\n>>> methods/{m}")
        if _run(p) != 0:
            fails.append(m)
    print("\n>>> coverage.py")
    if _run(os.path.join(HERE, "coverage.py")) != 0:
        fails.append("coverage.py")
    print("\n" + "=" * 60)
    if fails:
        print("FAILED:", ", ".join(fails))
        return 1
    print("ALL DEMOS PASSED -- every verdict reproduced from real bytes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
