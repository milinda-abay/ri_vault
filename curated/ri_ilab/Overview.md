# RI iLab

`ri_ilab` (repo name: **RI Insights**) is a Python data pipeline for Monash University's research infrastructure reporting, maintained by the Office of the Pro Vice-Chancellor (Research Infrastructure). It feeds the [[iLab Utilisation]] and other reports in [[Projects/RI PBI Production/Overview|RI PBI Production]], uploading into the catalog documented in [[Projects/Databricks/Overview|Databricks]].

Fetches data from iLab (SFTP), Databricks, and external APIs (Elsevier), processes it, and writes output for Power BI dashboards. Python 3.12+.

## Pipeline architecture

Every domain module follows the same 3-stage pattern:

1. `fetch.py` — download from source (SFTP or API)
2. `preprocess.py` — clean, transform, validate
3. `process.py` — write final output to Databricks

`main.py` exposes `run_*()` per pipeline plus a `main()` that runs them all.

## Domains

| Module | Purpose |
|---|---|
| `ilab/` | charges, labs, members, member_funds, services, charge_ack, pi_fund |
| `facility/` | Facility data |
| `external_institutes/` | External institute data |
| `research_income/` | Research income |
| `research_output/` | Research output metrics (Elsevier API) |
| `pipeline/` | Post-processing transforms (charges/awards, facility cost centres, lab staff) |
| `core/` | `ConnectSFTP` base class |
| `pen/` | Databricks table name constants and SQL schemas |
| `utils/` | Shared DataFrame helpers |
| `settings/` | Environment variable loading (`__init__.py`), folder path constants (`folders.py`) |
| `ilab/config.py` | Remapping dicts normalising facility names, institutes and labs |

## Subsystems

One note per module of the `ri_ilab` Python codebase. Synthesis notes — what each subsystem does, what it depends on, and the *why* behind it (design rationale from code comments, docstrings, and docs — the intent a graph traversal alone won't surface). Each links out to the generated per-node graph notes in `graphify/ri_ilab/` for structural detail (call graphs, edge confidence, connections).

| Note | Covers |
|---|---|
| [[Core SFTP Connector]] | `core/base_connector.py` — `ConnectSFTP`, the #1 god node; every `ilab/*` fetch depends on it |
| [[Shared DataFrame Utilities]] | `utils/utility_functions.py` — `fix_df()`/`csv_to_parquet()` and the rest of the cleanup layer; 2 open TODOs |
| [[iLab Domain Pipelines]] | The 7 `ilab/*` domains — **8 of 11 pipelines run automatically in `main()`** (`run_research_income()`, `run_research_output()`, `run_facility()` are commented out as of commit `2b2419e`; a 2026-08-29 working-tree change had briefly enabled all three, but that change was never committed and has since been reverted), plus institutional remap dicts and per-domain rationale (histology-node splitting, an email-driven business rule, a 3-year-stale HACK) |
| [[External Institutes & Facility Pipeline]] | `facility/`, `external_institutes/` — the "plain" baseline pipeline shape |
| [[Research Income & Research Output Pipelines]] | `research_income/` (manual CSV drop, SAP-prefix ID normalisation), `research_output/` (Elsevier API) |
| [[Post-Processing & Orchestration]] | `main.py` orchestration + `pipeline/` — the charges/award merge, and 3 undiscovered-by-the-graph manual scratch scripts |
| [[pen Databricks Upload Package]] | `pen/` — table schema registry + Databricks upload script; resolves both AMBIGUOUS edges from `GRAPH_REPORT.md` |
| [[Test Suite & Approval Testing]] | `tests/` — approval-test baselines as the actual test oracle, and what structure-only verification does/doesn't catch |

## Initiatives

| Note | Status |
|---|---|
| [[iLab Silver Layer Migration]] | Open, planning-stage as of 2026-09-09 — a Databricks-native silver layer to replace the pandas cleaning logic above. Prompt written and regression-checked; no plan written yet. |
| [[RI iLab Vault Reconciliation]] | Superseded 2026-09-11 — the 2026-09-02 plan that fixed the pipeline-automation regression in these notes and added the `ri_external_institutes`/remap-table references. Nine of fourteen tasks done; the rest cannot be resumed as written. |

## Reference

- [[Local Development]] — interpreter, commands, the 12 environment variables, data folders and version pins for the `ri_ilab` repo. Absorbed from the repo's `CLAUDE.md` 2026-09-08.
- [[Projects/Databricks/Overview|Databricks]] — the catalog this repo writes into. Everything platform-side now lives in that project rather than here: [[Projects/Databricks/Reference/Databricks Conventions|Databricks Conventions]] (the standing rules this repo's uploads follow), [[Projects/Databricks/Reference/Databricks Migration State|Databricks Migration State]] (how much of this repo now exists natively, and which of the two actually feeds Power BI), the three standalone table references, and [[Projects/Databricks/Pipelines/Historical Services Bronze Pipeline|Historical Services Bronze Pipeline]].
- `graphify/ri_ilab/` — graphify-generated knowledge graph vault (one note per code/doc entity, community pages, `graph.canvas`). Browse from any [[Core SFTP Connector|subsystem note]] above via its "See also" links, or open `graph.canvas` for the visual map — 506 nodes grouped into 39 communities, which makes it the fastest way to see *what exists*. It is capped at 200 edges against the 1,702 the notes assert, so read it for orientation and the notes' own `## Connections` lists for anything that turns on what depends on what.
- `graphify-out/GRAPH_REPORT.md` (in the repo itself) — god nodes, community list, ambiguous edges, suggested questions

## Data storage and integrations

- **Databricks** — primary warehouse. **Azure Blob Storage** — intermediate storage (`azure-identity` / `azure-storage-blob`). **Local** — `data/input/`, `data/preprocess/`, `data/output/` for development runs.
- **iLab SFTP** — source of the charge report exports (SSH key auth). **Elsevier API** — publication and citation metrics. **GRC** — institutional data system.

## See also

- **Derived layer** (`graphify/`, never hand-edited): [[_COMMUNITY_Project Metadata]], `RI Insights README` *(no node since export `1ac3015`; the README's node is now [[RI Insights]])*, [[main.py]], [[main.py run_() Orchestrator]], [[_COMMUNITY_Main Orchestration]], `_COMMUNITY_iLab Pipeline Architecture` *(no community since export `1ac3015`)*, [[ri_ilab Databricks Asset Bundle]]

## Contact

milinda.abayawardana@monash.edu
