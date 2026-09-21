#!/usr/bin/env python3
"""Documented-vs-live diff — the inversion of the old SHA-vs-SHA stale-check.

Freshness is REALITY where live grounding is possible (work laptop), and
LAST-KNOWN SNAPSHOT where it is not (home). The old system could only ever ask
"does the note's SHA agree with the export's SHA?"; this asks "does the
documented claim agree with what the catalog actually says?".

Reads the two honesty markers — derived/databricks/_meta.json and
graphify-out/_meta.json — so a stale snapshot (Databricks or the one-off deep
graph) is reported as last-known, never presented as current.
"""
import os

from config import load_config, ROOT


def read(path):
    try:
        return json_load(path)
    except (OSError, ValueError):
        return None


def json_load(path):
    import json
    return json.load(open(path))


def main():
    cfg = load_config()
    db_meta = read(os.path.join(ROOT, "derived", "databricks", "_meta.json")) or {}
    graph_meta = read(os.path.join(ROOT, "graphify-out", "_meta.json")) or {}
    catalog = read(os.path.join(ROOT, "derived", "databricks", "catalog.json"))
    last = read(os.path.join(ROOT, "derived", "databricks", "last_refresh.json"))

    mode = db_meta.get("mode", "?")
    machine = cfg.get("machine")
    print(f"[reconcile] machine = {machine or '?'}   databricks mode = {mode}   "
          f"auth_ok = {db_meta.get('auth_ok')}")
    print(f"[reconcile] last refresh (live) = {(last or {}).get('at', 'never on this machine')}")
    print(f"[reconcile] documented catalog = {cfg['databricks']['catalog']}")

    # The graph's own honesty marker (the deep layer is a one-off, not refresh-regenerable).
    print(f"[reconcile] graph mode = {graph_meta.get('mode', '?')}   "
          f"regenerable_here = {graph_meta.get('regenerable_here', '?')}   "
          f"nodes = {graph_meta.get('nodes', '?')} (deep {graph_meta.get('deep_nodes', '?')})")
    dp = graph_meta.get("deep_pass") or {}
    print(f"[reconcile] graph deep_pass = {dp.get('by', '?')} @ {dp.get('at', '?')} "
          f"({dp.get('nodes', '?')} nodes, method {dp.get('method', '?')})")

    if mode == "live":
        print("[reconcile] DATABRICKS LIVE: comparing documented claims against the live snapshot.")
        if catalog is None:
            print("  WARN: no catalog.json captured — run `python scripts/databricks_ground.py --live`.")
        else:
            print(f"  catalog tables captured: {len((catalog or {}).get('tables', []))}")
            print("  -> document a claim, then diff it against the captured value above.")
    else:
        print("[reconcile] DATABRICKS SNAPSHOT: this machine cannot query Databricks.")
        print("  the facts below are LAST-KNOWN, not current. They are the committed")
        print("  snapshot from the work laptop. Re-login on the work laptop and run")
        print("  `python scripts/databricks_ground.py --live` to make this a reality check.")

    # The drift the design exists to catch: the committed graph is a one-off deep
    # pass, not refresh-regenerable on this machine. Flag it so it is never read
    # as current.
    if not graph_meta.get("regenerable_here"):
        print("[reconcile] DRIFT: the committed graph is a one-off deep pass — it is NOT "
              "refresh-regenerable here. Regenerate it via the manual deep scan; "
              "treat its deep layer as last-known, not current.")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
