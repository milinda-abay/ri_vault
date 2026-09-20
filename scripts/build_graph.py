#!/usr/bin/env python3
"""Build the unified knowledge graph across the source repos (derived layer).

Reads config/sources.yaml. For each `kind: code` source, runs
    graphify extract <path> --code-only --out derived/sources/<name>
(AST only — no API/LLM, no cost), then merges every per-source graph.json into
the canonical graphify-out/graph.json via `graphify merge-graphs`.

Idempotent and safe to run on every refresh. `--deep` additionally runs a
curated-subset deep extract (the cross-repo bridge) when an LLM backend exists;
the code-only graph is always sufficient for query/path/explain.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT, "config", "sources.yaml")) as f:
        return yaml.safe_load(f)


def log(*a):
    print("[build_graph]", *a, file=sys.stderr)


def extract(cfg, deep):
    out_dir = os.path.join(ROOT, "derived", "sources")
    os.makedirs(out_dir, exist_ok=True)
    graphs = []
    mode = "deep" if deep else "code-only"
    for src in cfg["sources"]:
        if src.get("kind") != "code":
            continue
        out = os.path.join(out_dir, src["name"])
        log(f"extract {src['name']} ({mode}) -> {out}")
        rc = subprocess.run(
            ["graphify", "extract", src["path"], "--" + mode, "--out", out],
            check=False,
        ).returncode
        g = os.path.join(out, "graphify-out", "graph.json")
        if os.path.exists(g):
            graphs.append(g)
            log(f"  {src['name']}: rc={rc}, graph.json present")
        else:
            log(f"  WARN: {src['name']} rc={rc}, no graph.json produced")
    return graphs


def merge(cfg, graphs):
    dest = os.path.join(ROOT, cfg.get("graph", "graphify-out/graph.json"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if len(graphs) == 1:
        shutil.copyfile(graphs[0], dest)
        log(f"unified graph = single source ({graphs[0]})")
    else:
        log(f"merge {len(graphs)} graphs -> {dest}")
        subprocess.run(
            ["graphify", "merge-graphs", *graphs, "--out", dest], check=False
        )
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deep", action="store_true",
                    help="LLM/deep extract (needs a backend; default is code-only)")
    args = ap.parse_args()
    cfg = load_config()
    graphs = extract(cfg, args.deep)
    if not graphs:
        sys.exit("no source graphs produced — check sources.yaml paths")
    dest = merge(cfg, graphs)
    try:
        n = len(json.load(open(dest)).get("nodes", []))
    except (OSError, json.JSONDecodeError):
        n = -1
    log(f"unified graph: {dest} ({n} nodes)")
    if n < 0:
        sys.exit("unified graph.json missing or unreadable after merge")


if __name__ == "__main__":
    main()
