---
description: Documented-vs-live (work) / documented-vs-snapshot (home) diff — freshness = reality where possible.
---

Run: `python scripts/reconcile.py`

This is the inversion of the old SHA-vs-SHA `stale-check.sh`. It reads
`derived/databricks/_meta.json` for the mode:
- **live** (work laptop): documented claims vs the live catalog — a *reality* check.
- **snapshot** (home): documented vs last-known — reports the gap, **never claims the facts
  are current**.

On the home machine this always reports `mode=snapshot` (the CLI auth is stale). To make it a
real reality check, refresh live on the work laptop first (`/refresh --live`), which updates the
committed snapshot this machine then consumes.
