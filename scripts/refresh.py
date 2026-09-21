#!/usr/bin/env python3
"""The environment-aware refresh — the load-bearing orchestration entrypoint.

One command set, aware of which computer it is on (the `machine` flag in the
per-machine config/sources.local.yaml; absent -> fall back to the Databricks
auth probe). The two machines have different capabilities, so refresh grounds
Databricks differently on each, and GitHub holds the union:

    home  (Databricks not reachable)  -> Databricks SNAPSHOT (consume committed).
    work  (Databricks live)          -> Databricks LIVE scan.

The committed graph (graphify-out/graph.json) is CONSUMED, never clobbered, on
both machines. The deep scan of the code repos is a recognized manual/invoked
step (the subagent LLM backend); it is NOT auto-run by refresh. A marker
(graphify-out/_meta.json, mirroring derived/databricks/_meta.json) makes the
committed graph's staleness honest, so a one-off deep pass is never presented as
refresh-regenerable — the design's core principle, "never present a stale
snapshot as live," applied to the graph.

Flags:
    --check       dry-run: probe + report, write nothing
    --code-only   force the Databricks snapshot path
    --live        force the Databricks live path
Read-only against Databricks (the user's scope decision). No triggering/monitoring.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

from config import load_config, ROOT


def step(script, *extra, check=False):
    args = [sys.executable, os.path.join(ROOT, "scripts", script), *extra]
    print(f"\n=== {script} {' '.join(extra) or ''} ===", file=sys.stderr)
    if check:
        print(f"  (dry-run) would run: {' '.join(args)}")
        return 0
    return subprocess.run(args, check=False).returncode


def read_json(path):
    try:
        return json.load(open(path))
    except (OSError, json.JSONDecodeError):
        return None


def write_graph_meta(cfg, check=False):
    """Stamp graphify-out/_meta.json so the committed graph's staleness is honest
    (mirrors derived/databricks/_meta.json). The deep layer is a one-off subagent
    pass, so its provenance is recorded and it is never presented as
    refresh-regenerable."""
    graph_path = os.path.join(ROOT, cfg.get("graph", "graphify-out/graph.json"))
    meta_path = os.path.join(ROOT, "graphify-out", "_meta.json")
    g = read_json(graph_path) or {}
    nodes = g.get("nodes", [])
    n_total = len(nodes)
    n_deep = sum(1 for x in nodes if x.get("_origin") == "deep")

    # Preserve the deep-pass provenance across refreshes; seed it from the graph
    # itself (the _origin:"deep" count) if no prior marker exists.
    prior = read_json(meta_path) or {}
    deep_pass = prior.get("deep_pass") or {
        "at": "2026-09-20 (--deep passthrough)",
        "by": "Claude Code subagents",
        "method": "subagent one-off",
        "nodes": n_deep,
    }
    machine = cfg.get("machine")
    # Can THIS machine reproduce the deep layer? home: no backend -> False.
    # A real backend (azure_wrapper / an API key) or the work machine -> True.
    regenerable = bool(cfg.get("azure_wrapper")) or (machine == "work")
    mode = "snapshot"  # refresh never promotes the graph; it only consumes it.

    meta = {
        "mode": mode,
        "regenerable_here": regenerable,
        "machine": machine,
        "deep_pass": deep_pass,
        "nodes": n_total,
        "deep_nodes": n_deep,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "note": ("consumed (non-destructive): the committed graph was not rebuilt. "
                 "The deep layer is a one-off subagent pass — regenerate it via the "
                 "manual deep scan, not via refresh."),
    }
    if check:
        print(f"[graph _meta] would stamp {meta_path}: mode={mode} "
              f"regenerable_here={regenerable} nodes={n_total} (deep {n_deep})",
              file=sys.stderr)
        return meta
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    return meta


def report():
    meta = read_json(os.path.join(ROOT, "graphify-out", "_meta.json")) or {}
    db_meta = read_json(os.path.join(ROOT, "derived", "databricks", "_meta.json")) or {}
    print("\n" + "=" * 52)
    print(f"  refresh complete   machine = {meta.get('machine', '?')}   "
          f"graph = {meta.get('mode', '?')}   "
          f"databricks = {'LIVE' if db_meta.get('live') else 'snapshot'}")
    print(f"  graph nodes = {meta.get('nodes', '?')} (deep {meta.get('deep_nodes', '?')})  "
          f"regenerable_here = {meta.get('regenerable_here', '?')}")
    print(f"  databricks auth_ok = {db_meta.get('auth_ok')}  "
          f"captured_at = {db_meta.get('captured_at', '?')}")
    print(f"  -> query with:  graphify query \"<question>\" "
          f"--graph {os.path.join(ROOT, 'graphify-out', 'graph.json')}")
    print("=" * 52)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="probe + report; write nothing")
    ap.add_argument("--code-only", action="store_true",
                    help="force the Databricks snapshot path (never live)")
    ap.add_argument("--live", action="store_true",
                    help="force the Databricks live path (work laptop)")
    args = ap.parse_args()

    cfg = load_config()

    # 1. Databricks grounding: the probe decides live vs snapshot and writes
    #    derived/databricks/_meta.json. --live forces live; --code-only forces
    #    the snapshot path (no --live). The machine flag is the domain, the
    #    probe is the grounding check ("both").
    dflag = ["--live"] if args.live else []
    if args.code_only:
        dflag = []  # snapshot path: no --live
    step("databricks_ground.py", *dflag, check=args.check)

    # 2. The committed graph is CONSUMED, never clobbered. build_graph.py writes
    #    only to the staging copy (derived/sources/_unified) here, so a code-only
    #    scan can report drift without touching the committed deep-enriched graph.
    #    The manual deep scan is the only thing that promotes it.
    step("build_graph.py", check=args.check)

    # 3. Stamp the graph _meta.json (honesty marker) so a one-off deep pass is
    #    never presented as refresh-regenerable.
    write_graph_meta(cfg, check=args.check)

    report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
