---
description: Rebuild the unified graph + (live) re-query Databricks + diff + report. Environment-aware, read-only.
---

Run the environment-aware refresh: `python scripts/refresh.py $ARGUMENTS`

It probes Databricks auth with a **real authenticated query** (`databricks catalogs list`,
NOT `current-user` — that returns 0 without authenticating), then branches:
- **live** (work laptop): builds the graph + queries the live catalog + updates the snapshot.
- **snapshot** (home): builds the code-only graph + uses the committed snapshot.

Then writes `derived/databricks/_meta.json` `{mode, auth_ok, captured_at, workspace}` and
prints a report. A stale snapshot is never presented as live. Read-only against Databricks.

Flags: `--check` (probe + report, write nothing), `--code-only` (graph via AST only; the default
on the home machine), `--live` (force live grounding — use on the work laptop).

If the probe fails here, that is expected on the home machine — it degrades to snapshot mode.
To refresh live grounding, run this on the work laptop after `databricks auth login`.
