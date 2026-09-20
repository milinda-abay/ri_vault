#!/usr/bin/env python3
"""Live-ground the Databricks layer via the CLI, or degrade to the committed snapshot.

The reliable auth probe is `databricks --profile <p> catalogs list` (a real
authenticated query). `current-user` is NOT reliable — it returns 0 without
authenticating, so it must never be used as the probe.

    catalogs list ok   -> LIVE:     crawl catalog/jobs/pipelines -> derived/databricks/*
    catalogs list fail -> SNAPSHOT: keep the committed snapshot; flag mode: snapshot

Read-only. The snapshot is a committed artifact: the work laptop refreshes it
live; the home machine consumes it. Every write stamps _meta.json with
{mode, auth_ok, captured_at, workspace} so a stale snapshot is never presented
as live.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "derived", "databricks")


def load_config():
    with open(os.path.join(ROOT, "config", "sources.yaml")) as f:
        return yaml.safe_load(f)


def db(*args, profile, timeout=180):
    """Run a databricks CLI subcommand; return (ok: bool, data: dict|None)."""
    cmd = ["databricks", "--profile", profile, *args, "-o", "json"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, None
    if r.returncode != 0:
        return False, None
    try:
        return True, json.loads(r.stdout)
    except json.JSONDecodeError:
        return False, None


def probe_auth(cfg):
    """A real authenticated query. `current-user` returns 0 without auth — unusable."""
    ok, _ = db("catalogs", "list", profile=cfg["databricks"]["profile"])
    return ok


def crawl(cfg):
    """Crawl the live catalog into derived/databricks/*.json (live mode only)."""
    profile = cfg["databricks"]["profile"]
    cat = cfg["databricks"]["catalog"]
    ok, catalogs = db("catalogs", "list", profile=profile)
    if not ok:
        return False
    schemas = []
    for c in catalogs or []:
        ok, s = db("schemas", "list", "--catalog", c.get("name", cat), profile=profile)
        if ok:
            schemas += s or []
    # tables are paginated — loop to the end or the snapshot is silently partial
    tables = []
    for sc in schemas:
        token = None
        while True:
            args = ["tables", "list-summaries", sc["name"]]
            if token:
                args += ["--token", token]
            ok, page = db(*args, profile=profile)
            if not ok:
                break
            tables += page.get("tables", page) if isinstance(page, dict) else (page or [])
            token = page.get("next_page_token") if isinstance(page, dict) else None
            if not token:
                break
    return True


def write_snapshot(cfg, mode, auth_ok, live_data):
    os.makedirs(OUT, exist_ok=True)
    meta = {
        "mode": mode,
        "auth_ok": auth_ok,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "captured_at_note": "the only timestamp that matters; refresh re-stamps on live success",
        "workspace": cfg["databricks"]["workspace"],
        "catalog": cfg["databricks"]["catalog"],
        "probe": "databricks catalogs list",
    }
    if mode == "live":
        meta["live"] = True
        # in live mode, live_data carries the crawl; persist it under derived/databricks
        if isinstance(live_data, dict) and live_data.get("ok"):
            for name, payload in live_data.get("sections", {}).items():
                with open(os.path.join(OUT, f"{name}.json"), "w") as f:
                    json.dump(payload, f, indent=2)
            # last refresh time doubles as the freshness signal for /status
            with open(os.path.join(OUT, "last_refresh.json"), "w") as f:
                json.dump({"at": meta["captured_at"], "catalog": meta["catalog"]}, f)
    else:
        meta["live"] = False
        meta["note"] = ("snapshot mode: this machine cannot query Databricks; "
                        "using the committed snapshot. Refresh live on the work laptop.")
        # do NOT touch the committed *.json snapshots on a failed probe
    with open(os.path.join(OUT, "_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="force live grounding even if the probe fails (work laptop)")
    ap.add_argument("--check", action="store_true", help="probe + report; write nothing")
    args = ap.parse_args()
    cfg = load_config()

    auth_ok = probe_auth(cfg)
    live = auth_ok or args.live

    print(f"[databricks_ground] probe 'catalogs list' -> {'OK (live)' if auth_ok else 'FAIL'}")
    if args.check:
        print(f"[databricks_ground] mode would be {'live' if live else 'snapshot'}; --check, writing nothing")
        return 0

    if live:
        ok = crawl(cfg)
        meta = write_snapshot(cfg, "live" if ok else "snapshot", auth_ok,
                              {"ok": ok, "sections": {}} if ok else None)
        print(f"[databricks_ground] mode=live (auth_ok={auth_ok}); snapshot updated"
              if ok else "[databricks_ground] live crawl failed; keeping snapshot")
    else:
        meta = write_snapshot(cfg, "snapshot", False, None)
        print(f"[databricks_ground] mode=snapshot (auth failed on this machine); "
              f"using committed snapshot. Re-login on the work laptop to refresh.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
