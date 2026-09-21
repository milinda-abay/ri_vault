#!/usr/bin/env python3
"""Shared config loading for the refresh family of scripts.

Reads config/sources.yaml (committed + synced) and, when present,
config/sources.local.yaml (git-ignored, per-machine). The local file is the
per-machine override — the flag that tells each command *which computer it is on*
(`machine: home|work`) plus optional `paths` / `azure_wrapper` overrides.

`machine` is the domain selector: home = deep-scan domain (the code repos),
work = Databricks domain. When absent, callers fall back to the Databricks auth
probe (a real `catalogs list` query) to decide live vs snapshot. See the module
docstring of refresh.py.
"""
import os

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT, "config", "sources.yaml")) as f:
        cfg = yaml.safe_load(f)
    # Optional per-machine override (git-ignored): {machine, paths, azure_wrapper}.
    # `machine` is the flag that makes one command set aware of which computer it
    # is on; each machine sets its own, and it is never synced (that is the point).
    local = os.path.join(ROOT, "config", "sources.local.yaml")
    if os.path.exists(local):
        with open(local) as f:
            lc = yaml.safe_load(f) or {}
        if "azure_wrapper" in lc:
            cfg["azure_wrapper"] = lc["azure_wrapper"]
        if "machine" in lc:
            cfg["machine"] = lc["machine"]
        paths = lc.get("paths") or {}
        for src in cfg.get("sources", []):
            if src.get("name") in paths:
                src["path"] = paths[src["name"]]
    return cfg


if __name__ == "__main__":
    import json
    import sys

    sys.exit(json.dumps(load_config(), indent=2, default=str))
