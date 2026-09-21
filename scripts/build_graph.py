#!/usr/bin/env python3
"""Build the unified knowledge graph across the source repos (derived layer).

Reads config/sources.yaml (+ the per-machine sources.local.yaml via
config.load_config). For each `kind: code` source, runs
    graphify extract <path> --code-only --out derived/sources/<name>
(AST only — no API/LLM, no cost), then merges every per-source graph.json.

Non-destructive by default: the merge writes to the STAGING copy
derived/sources/_unified/graph.json, NOT the committed graphify-out/graph.json.
A plain code-only build must never clobber the committed, deep-enriched graph —
that silent regression (1,254 -> 473) is exactly what the machine-aware refresh
guards against. `--promote` writes the merged graph to the committed
graphify-out/graph.json instead; `refresh` promotes only on the work machine
(Databricks live / a real backend).

`--deep` additionally runs an azure_wrapper deep extract when one is configured
(see config/sources.local.yaml); the code-only graph is always sufficient for
query/path/explain.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

from config import load_config, ROOT


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
        aw = cfg.get("azure_wrapper")
        if deep and aw:
            # LLM backend via Azure AI Foundry (AD auth); needs `az login`
            cmd = [aw["python"], aw["script"], src["path"], "--",
                   "--mode", "deep", "--out", out]
        else:
            cmd = ["graphify", "extract", src["path"], "--" + mode, "--out", out]
        rc = subprocess.run(cmd, check=False).returncode
        g = os.path.join(out, "graphify-out", "graph.json")
        if os.path.exists(g):
            graphs.append(g)
            log(f"  {src['name']}: rc={rc}, graph.json present")
        else:
            log(f"  WARN: {src['name']} rc={rc}, no graph.json produced")
    return graphs


STAGING = os.path.join(ROOT, "derived", "sources", "_unified", "graph.json")


def _merge_fresh(graphs, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if len(graphs) == 1:
        shutil.copyfile(graphs[0], dest)
    else:
        subprocess.run(["graphify", "merge-graphs", *graphs, "--out", dest], check=False)


def union_merge(base_path, frag_path, out_path):
    """Union a fresh graph (frag) into an existing committed graph (base),
    preserving the deep layer. Dedup by node id; keep a link only if both endpoints
    exist. This is the namespace-safe union (avoids graphify merge-graphs' repo-2
    mangling) so an --promote can never silently drop the 781 deep nodes."""
    base = json.load(open(base_path)) if os.path.exists(base_path) else {}
    frag = json.load(open(frag_path)) if os.path.exists(frag_path) else {}
    nodes = list(base.get("nodes", []))
    links = list(base.get("links", []))
    hedges = list(base.get("hyperedges", []))
    ids = {n.get("id") for n in nodes}
    seen_link = {(l.get("source"), l.get("target"), l.get("relation")) for l in links}
    seen_he = {h.get("id") for h in hedges}
    for n in frag.get("nodes", []):
        if n.get("id") and n.get("id") not in ids:
            nodes.append(n)
            ids.add(n.get("id"))
    for l in frag.get("links", []):
        if l.get("source") in ids and l.get("target") in ids:
            k = (l.get("source"), l.get("target"), l.get("relation"))
            if k not in seen_link:
                links.append(l)
                seen_link.add(k)
    for h in frag.get("hyperedges", []):
        if h.get("id") and h.get("id") not in seen_he \
                and all(x in ids for x in h.get("nodes", [])):
            hedges.append(h)
            seen_he.add(h.get("id"))
    merged = {
        "directed": base.get("directed", True),
        "multigraph": base.get("multigraph", False),
        "graph": base.get("graph", {}),
        "nodes": nodes,
        "links": links,
        "hyperedges": hedges,
    }
    json.dump(merged, open(out_path, "w"), indent=2)
    return merged


def merge(cfg, graphs, promote):
    # Always produce the fresh code-only union into staging first (non-destructive).
    _merge_fresh(graphs, STAGING)
    if not promote:
        log(f"merge {len(graphs)} graphs -> STAGING {STAGING} (committed graph untouched)")
        return STAGING
    # --promote: union the fresh graph into the committed graph, preserving the
    # deep layer (a plain overwrite would silently drop the 781 deep nodes).
    committed = os.path.join(ROOT, cfg.get("graph", "graphify-out/graph.json"))
    union_merge(committed, STAGING, committed)
    m = json.load(open(committed))
    log(f"promote (union, deep preserved) -> COMMITTED {committed}: "
        f"{len(m.get('nodes', []))} nodes")
    return committed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deep", action="store_true",
                    help="LLM/deep extract (needs an azure_wrapper; default is code-only)")
    ap.add_argument("--promote", action="store_true",
                    help="write the merged graph to the committed graphify-out/graph.json "
                         "(default: write to the staging copy and leave the committed graph "
                         "untouched — non-destructive)")
    args = ap.parse_args()
    cfg = load_config()
    graphs = extract(cfg, args.deep)
    if not graphs:
        sys.exit("no source graphs produced — check sources.yaml paths")
    dest = merge(cfg, graphs, args.promote)
    try:
        n = len(json.load(open(dest)).get("nodes", []))
    except (OSError, json.JSONDecodeError):
        n = -1
    log(f"{'promoted' if args.promote else 'staged'} graph: {dest} ({n} nodes)")
    if n < 0:
        sys.exit("unified graph.json missing or unreadable after merge")


if __name__ == "__main__":
    main()
