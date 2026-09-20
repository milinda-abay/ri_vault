#!/usr/bin/env python3
"""The environment-aware refresh — the load-bearing orchestration entrypoint.

Probes Databricks auth first (a real authenticated query), then branches:
    live     (work laptop): build graph + query Databricks + update snapshot
    snapshot (home):        build code-only graph + use the committed snapshot
Then writes derived/databricks/_meta.json {mode, auth_ok, captured_at, workspace}
and prints a short report. A stale snapshot is never presented as live.

Flags:
    --check       dry-run: probe + report, write nothing
    --code-only   graph via AST only (default; no API/LLM, no cost)
    --live        force live grounding even if the probe fails (work laptop)
Read-only against Databricks (the user's scope decision). No triggering/monitoring.
"""
import argparse
import json
import os
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)  # ri_vault/


def load_config():
    with open(os.path.join(ROOT, "config", "sources.yaml")) as f:
        return yaml.safe_load(f)


def step(script, *extra, check=False):
    args = [sys.executable, os.path.join(ROOT, "scripts", script), *extra]
    print(f"\n=== {script} {' '.join(extra) or ''} ===", file=sys.stderr)
    if check:
        print(f"  (dry-run) would run: {' '.join(args)}")
        return 0
    return subprocess.run(args, check=False).returncode


def report():
    meta_path = os.path.join(ROOT, "derived", "databricks", "_meta.json")
    graph_path = os.path.join(ROOT, "graphify-out", "graph.json")
    try:
        meta = json.load(open(meta_path))
    except (OSError, json.JSONDecodeError):
        meta = {}
    n = -1
    try:
        n = len(json.load(open(graph_path)).get("nodes", []))
    except (OSError, json.JSONDecodeError):
        pass
    mode = meta.get("mode", "?")
    print("\n" + "=" * 52)
    print(f"  refresh complete   mode = {mode}   "
          f"databricks = {'LIVE' if meta.get('live') else 'snapshot'}")
    print(f"  auth_ok = {meta.get('auth_ok')}   captured_at = {meta.get('captured_at', '?')}")
    print(f"  unified graph = {n} nodes  ({graph_path})")
    print(f"  -> query with:  graphify query \"<question>\" "
          f"--graph {graph_path}")
    print("=" * 52)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="probe + report; write nothing")
    ap.add_argument("--code-only", action="store_true",
                    help="graph via AST only (default; --live implies deep-capable)")
    ap.add_argument("--live", action="store_true",
                    help="force live grounding even if the probe fails (work laptop)")
    args = ap.parse_args()

    cfg = load_config()
    deep = not args.code_only and not args.check  # default here is code-only

    # 1. build the unified graph (code-only by default — cheap, no API)
    gflag = [] if deep else ["--code-only"]
    step("build_graph.py", *gflag, check=args.check)

    # 2. Databricks grounding: probe auth -> live or snapshot
    dflag = ["--live"] if args.live else []
    step("databricks_ground.py", *dflag, check=args.check)

    report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
