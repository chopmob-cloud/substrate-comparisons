#!/usr/bin/env python3
"""
At scale: how many real payments each timestamp encoding drops.

Reproducible, offline, names no implementation. For a burst of N distinct
payments (same agent / type / scope, distinct moments), this computes the REAL
action_ref of every payment under each encoding and counts the unique
identities. Under exactly-once (action_ref is the identity, SKIP-on-retry),
every collision after the first in a bucket is a real payment silently dropped.

    dropped = N - (unique action_refs)

  - integer epoch-millisecond : one identity per millisecond -> lossless up to
                                ~1000 payments/second.
  - second precision          : one identity per SECOND -> every payment beyond
                                the first in any second is dropped.

This is not a model or an estimate: it hashes every payment and counts the set.

Run:  pip install algovoi-substrate ; python scale.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import sys

from algovoi_substrate import action_ref

AGENT_ID, ACTION_TYPE, SCOPE = "agent-1", "payment", "settlement"
BASE_MS = 1716494400000


def _ref(ts_ms: int) -> str:
    return action_ref(agent_id=AGENT_ID, action_type=ACTION_TYPE, scope=SCOPE, timestamp_ms=ts_ms)


def run(n: int, window_ms: int) -> tuple[int, int]:
    """N distinct payments evenly spaced across window_ms. Returns (unique under
    integer-ms, unique under second-precision), computed from real hashes."""
    ms_ids, sec_ids = set(), set()
    for i in range(n):
        t = BASE_MS + (i * window_ms) // n       # distinct logical moments
        ms_ids.add(_ref(t))
        sec_ids.add(_ref((t // 1000) * 1000))    # truncate to the second
    return len(ms_ids), len(sec_ids)


SCENARIOS = [
    ("100 payments in 1 second", 100, 1_000),
    ("1,000 payments in 1 second", 1_000, 1_000),
    ("10,000 payments in 10 seconds (1k/s)", 10_000, 10_000),
    ("60,000 payments in 60 seconds (1k/s)", 60_000, 60_000),
    ("100,000 payments in 100 seconds (1k/s)", 100_000, 100_000),
]


def main() -> int:
    w = 78
    print("=" * w)
    print("AT SCALE -- real payments dropped per timestamp encoding (names no implementation)")
    print("dropped = payments - unique identities; every drop is a lost payment")
    print("=" * w)
    hdr = f"{'scenario':40s} {'N':>7} {'ms drop':>12} {'second drop':>16}"
    print(hdr); print("-" * w)
    second_catastrophic = True
    ms_clean_in_range = True
    for label, n, window in SCENARIOS:
        ms_u, sec_u = run(n, window)
        ms_drop, sec_drop = n - ms_u, n - sec_u
        ms_pct, sec_pct = 100 * ms_drop / n, 100 * sec_drop / n
        print(f"{label:40s} {n:>7} {ms_drop:>6} ({ms_pct:4.1f}%) {sec_drop:>9} ({sec_pct:5.1f}%)")
        if sec_pct < 90:
            second_catastrophic = False
        # within <=1000/s, integer-ms must be lossless
        if (n / (window / 1000)) <= 1000 and ms_drop != 0:
            ms_clean_in_range = False
    print("-" * w)
    print("integer epoch-millisecond: lossless up to ~1000 payments/second")
    print("                           (resolution threshold is 1000x higher than second precision).")
    print("second precision:          drops essentially every payment beyond one per second.")
    print()
    ok = second_catastrophic and ms_clean_in_range
    print("RESULT: at any realistic agentic payment rate, second precision loses >99% of"
          if ok else "RESULT: demonstration did not hold -- investigate.")
    if ok:
        print("        payments while integer-millisecond loses none. Run it; these are real hashes.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
