---
description: Staleness dashboard — mode, last-refresh, graph size, drift. Read-only.
---

Report the current state of the control plane:
- **mode** (live|snapshot), **auth_ok**, **captured_at** from `derived/databricks/_meta.json`.
- **last live refresh** from `derived/databricks/last_refresh.json` (if absent, the work
  laptop has not refreshed yet — this machine is on a committed snapshot).
- **unified graph size** — node count of `graphify-out/graph.json`.
- **curated vs derived** — how many curated notes exist, and whether any link into a
  now-absent node.

Run the probe and read the artifacts:
- `python scripts/refresh.py --check`   (auth probe + mode, writes nothing)
- read `derived/databricks/_meta.json` and `graphify-out/graph.json`.

Never report `mode=live` when `_meta.json` says `snapshot`.
