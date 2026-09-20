# ri_vault — a live-grounded, queryable knowledge control plane for RI

This replaces `obsidian_life`. It unifies `ri_ilab`, `ri_pbi_production` (8 sub-repos)
and the Databricks layer into **one queryable graph + a small curated "why" layer +
a read-only orchestration surface**, and it is driven from this folder.

## The one inversion

The old system **mirrored** the code/data layer into notes at fixed git SHAs and
**reconciled by hand** (its git log was ~90% "Reconcile …@ SHA" / "Repair links broken
by export" / "Bump sub-repo SHAs"). It "provably couldn't check itself" — it trusted an
export's `_meta.md` and could not tell if the export was current.

This system instead **reads the sources and derives the graph from them**; it keeps only
the non-derivable *why* hand-curated. Freshness is **reality, or last-known snapshot —
not SHA-agreement**. The one thing kept from the old system is its good axiom:
**if a fact is derivable from code, it is linked, not duplicated.**

## The 3 layers

| Layer | Where | Written by | Rule |
|---|---|---|---|
| **Derived (committed)** | `graphify-out/`, `derived/databricks/` | `refresh` (never by hand) | The unified graph + Databricks snapshots. **Committed + synced**: work produces, home consumes; regenerated on refresh. |
| **Local intermediates** | `derived/sources/` (git-ignored) | `build_graph` | Per-source extracts — regenerated, disposable, never committed. |
| **Curated** | `curated/` | You | Intent, decisions, gotchas, RLS rationale, migration ladders — the *why* the code can't tell you. Links into the graph; never duplicates it. |
| **Join** | `contracts/` | Derived | Producer→consumer schema bindings, *computed* from the catalog + graph edges — never empty. |

There is no `manifest.sha256`, no sync-block frontmatter, no "never `git add -A`" rule.
The derived layer regenerates, so there is nothing to guard against drift.

## The load-bearing constraint: two environments

| | Can query Databricks | `refresh` does |
|---|---|---|
| **Home** (this machine) | **No** — CLI auth is stale (`databricks catalogs list` fails) | consumes the **committed graph + committed snapshot** (or rebuilds the code-only graph locally); `mode: snapshot` |
| **Work laptop** | **Yes** | live catalog + jobs + pipelines → update the committed snapshot; `mode: live` |

The auth probe is a **real authenticated query** (`databricks catalogs list`), **not**
`current-user` (that returns 0 without authenticating). The Databricks snapshot is a
**committed artifact**: the work laptop refreshes it live; the home machine consumes it.
Every grounding write stamps `derived/databricks/_meta.json`
`{mode, auth_ok, captured_at, workspace}` so a stale snapshot is never presented as live.
Read-only against Databricks (no triggering / no monitoring writes) — the scope decision.

## How to use it

| Command | Does |
|---|---|
| `/refresh` | Probe auth → build the unified graph → (live) query Databricks or (snapshot) use the committed one → write `_meta.json` → report. Flags `--check`, `--code-only` (default), `--live`. |
| `/query "…"` | `graphify query/path/explain/god-nodes` on `graphify-out/graph.json`. **Query the graph, never free-search notes.** |
| `/reconcile` | Documented-vs-live (work) / documented-vs-snapshot (home) diff — the inversion of the old SHA-vs-SHA check. |
| `/status` | mode + last-refresh + graph size + drift. |
| `/file` | Drain `Inbox/` → curated *why*. Derivables become graph nodes, not duplicated notes. |

## Running the commands (uv venv)

The scripts need only one third-party import, **PyYAML** (for `config/sources.yaml`);
everything else is stdlib. `graphify` and `databricks` are external CLIs the scripts
call as subprocesses, so they resolve via **PATH, not the venv**.

Recreate the environment on any machine (home or work) with:
    uv sync                 # creates .venv + installs PyYAML, deterministic via uv.lock
then run the commands through it:
    .venv/bin/python scripts/refresh.py       # or:  source .venv/bin/activate

`pyproject.toml` + `uv.lock` are committed; `.venv/` is git-ignored (recreated by `uv sync`).
If a bare `graphify`/`databricks` call fails, the CLI isn't on PATH (not a venv issue):
`graphify` is a uv tool (`uv tool install graphifyy`); `databricks` is the Databricks CLI
(work laptop only).

## What's on this machine right now (home)

- Unified graph: `graphify-out/graph.json` (473 nodes, 886 edges, built `--code-only`
  across `ri_ilab` + `ri_pbi_production`). Queryable now. The PBI side is thin because
  `--code-only` is AST-based and the PBI repos are mostly TMDL/PBIR — a `--deep` pass
  (needs an LLM backend) enriches it; the code-only graph is sufficient for query/path/explain.
- `derived/databricks/_meta.json` = `{mode: snapshot, auth_ok: false}` — the work laptop
  has not refreshed live here yet.
- Databricks live grounding happens on the work laptop: `databricks auth login` then
  `/refresh --live`.

## Layout

```
config/            sources.yaml (the single input point) + databricks.env (profile, no secrets)
scripts/           refresh.py (orchestrator) · build_graph.py · databricks_ground.py · reconcile.py
.claude/commands/  refresh · query · reconcile · status · file
graphify-out/      the unified graph (derived) — graph.json, GRAPH_REPORT.md, graph.html
derived/databricks/ committed snapshots (catalog/jobs/pipelines/_meta) — refreshed live on the work laptop
curated/           the migrated "why" notes (ri_ilab, ri_pbi_production, databricks, computing)
contracts/         producer→consumer schema bindings (the join layer, now derived)
Inbox/             raw capture, drained by /file
```

## Retiring obsidian_life

`ri_vault` replaces it in place. When this is in use, disable the `ri_ilab`/`ri_pbi_production`
post-commit export hooks that wrote into `obsidian_life/graphify/`, re-point their `CLAUDE.md`
graphify section at `ri_vault/graphify-out/`, and **archive** (do not hard-delete) the
`obsidian_life` repo — its `git log` is the historical record of the tax this replaces.
