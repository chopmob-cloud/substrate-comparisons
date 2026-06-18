#!/usr/bin/env python3
"""
Concatenation vs structured canonicalization: which methods preserve field
boundaries, and which let two distinct actions collide into one identity.

Reproducible, offline, names no implementation. A common shortcut derives the
action identity by joining the fields into one string with a delimiter and
hashing that:  SHA-256( agent_id : action_type : scope : timestamp_ms ).
The problem is that the delimiter can also appear *inside* a field value, so the
field boundaries are not recoverable -- two operationally distinct actions can
produce the identical joined string, hence the identical identity. That is a
forgeable collision: an attacker who controls one field can re-target a victim's
action identity.

The reference derives the identity from the JCS (RFC 8785) canonical form of the
structured object, where field boundaries are preserved, so the same two actions
stay distinct.

Run:  pip install algovoi-substrate ; python concatenation.py
Apache-2.0. (c) AlgoVoi.
"""
from __future__ import annotations

import hashlib
import sys

from algovoi_substrate import action_ref

TS = 1716494400123  # fixed integer epoch-millisecond, same for both actions


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _concat_id(agent_id: str, action_type: str, scope: str, ts_ms: int) -> str:
    # A typical bare-concatenation identity with a ':' delimiter.
    return _sha(f"{agent_id}:{action_type}:{scope}:{ts_ms}")


def _jcs_id(agent_id: str, action_type: str, scope: str, ts_ms: int) -> str:
    # The reference: identity from the JCS-canonical structured object.
    return action_ref(agent_id=agent_id, action_type=action_type,
                      scope=scope, timestamp_ms=ts_ms)


def main() -> int:
    w = 70
    print("=" * w)
    print("CONCATENATION vs STRUCTURED -- reproducible comparison (names no implementation)")
    print("=" * w)

    # Two operationally DISTINCT actions. The ':' that delimits the concat form
    # also appears inside the field values, so the joined strings coincide.
    # Action X: a 'screen' action, scope 'acme:order-42'
    X = dict(agent_id="agent-1", action_type="screen", scope="acme:order-42", ts_ms=TS)
    # Action Y: a DIFFERENT action_type/scope split that re-joins identically.
    Y = dict(agent_id="agent-1", action_type="screen:acme", scope="order-42", ts_ms=TS)

    print("two operationally DISTINCT actions:")
    print(f"  X: action_type={X['action_type']!r}  scope={X['scope']!r}")
    print(f"  Y: action_type={Y['action_type']!r}  scope={Y['scope']!r}\n")

    cx = _concat_id(X["agent_id"], X["action_type"], X["scope"], X["ts_ms"])
    cy = _concat_id(Y["agent_id"], Y["action_type"], Y["scope"], Y["ts_ms"])
    concat_collision = cx == cy
    print("[bare concatenation: SHA-256(agent_id:action_type:scope:timestamp_ms)]")
    print(f"  X -> {cx}")
    print(f"  Y -> {cy}")
    print(f"  collision: {concat_collision}  -> two distinct actions share one identity (forgeable)\n")

    jx = _jcs_id(X["agent_id"], X["action_type"], X["scope"], X["ts_ms"])
    jy = _jcs_id(Y["agent_id"], Y["action_type"], Y["scope"], Y["ts_ms"])
    jcs_distinct = jx != jy
    print("[reference: action_ref = SHA-256(JCS({agent_id,action_type,scope,timestamp_ms}))]")
    print(f"  X -> {jx}")
    print(f"  Y -> {jy}")
    print(f"  distinct: {jcs_distinct}  -> field boundaries preserved; no collision\n")

    print("-" * w)
    ok = concat_collision and jcs_distinct
    print("RESULT: bare concatenation collapses two distinct actions to one identity "
          "(field boundaries lost); only the structured JCS form keeps them distinct."
          if ok else "RESULT: demonstration did not hold -- investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
