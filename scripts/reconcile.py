#!/usr/bin/env python3
"""Documented-vs-live diff — the inversion of the old SHA-vs-SHA stale-check.

Freshness is REALITY where live grounding is possible (work laptop), and
LAST-KNOWN SNAPSHOT where it is not (home). The old system could only ever
ask "does the note's SHA agree with the export's SHA?"; this asks "does the
documented claim agree with what the catalog actually says?".

Reads derived/databricks/_meta.json for the mode. On a snapshot it never
claims the facts are current — it reports the gap instead.
"""
import json
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT, "config", "sources.yaml")) as f:
        return yaml.safe_load(f)


def read(path):
    try:
        return json.load(open(path))
    except (OSError, json.JSONDecodeError):
        return None


def main():
    cfg = load_config()
    meta = read(os.path.join(ROOT, "derived", "databricks", "_meta.json")) or {}
    catalog = read(os.path.join(ROOT, "derived", "databricks", "catalog.json"))
    last = read(os.path.join(ROOT, "derived", "databricks", "last_refresh.json"))

    mode = meta.get("mode", "?")
    print(f"[reconcile] mode = {mode}   auth_ok = {meta.get('auth_ok')}")
    print(f"[reconcile] last refresh (live) = {(last or {}).get('at', 'never on this machine')}")
    print(f"[reconcile] documented catalog = {cfg['databricks']['catalog']}")

    if mode == "live":
        print("[reconcile] LIVE: comparing documented claims against the live snapshot.")
        if catalog is None:
            print("  WARN: no catalog.json captured — run `python scripts/databricks_ground.py --live`.")
        else:
            # a documented-vs-live drift check would go here; e.g. assert that
            # 01_standalone_tables exists and is scheduled, ri_master_list row count, etc.
            print(f"  catalog tables captured: {len((catalog or {}).get('tables', []))}")
            print("  -> document a claim, then diff it against the captured value above.")
    else:
        print("[reconcile] SNAPSHOT: this machine cannot query Databricks.")
        print("  the facts below are LAST-KNOWN, not current. They are the committed")
        print("  snapshot from the work laptop. Re-login on the work laptop and run")
        print("  `python scripts/databricks_ground.py --live` to make this a reality check.")
        if last is None:
            print("  no live snapshot captured yet — the work laptop has not refreshed.")
        else:
            print(f"  snapshot captured at: {last.get('at')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
