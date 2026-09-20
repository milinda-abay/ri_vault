# Delivery Matrix

A single self-contained page, `RI_Delivery_Matrix.html` at the `ri_pbi_production` workspace root, showing every research platform (`CAPABILITY_CODE`) against ten delivery milestones — from the raw source feed through to a published Power BI report and sign-off. Built **2026-08-28**; see `tools/delivery-matrix/README.md` for the full mechanics.

## Purpose

Answers "how far has platform X actually gotten through the pipeline" at a glance, across all 7 reports in [[Overview|RI PBI Production]] plus the upstream `ri_ilab`/`ri_master_list` stages the sub-repos don't show on their own. Complements rather than duplicates [[QA Test Plan]] (page-level look/feel/behaviour) and [[RLS Alignment Audit]] (RLS correctness) — this tracks *delivery progress per platform*, not correctness of what's already delivered.

## How it's built

`tools/delivery-matrix/build_matrix.py` (run via the `ri_ilab` venv — see [[Shared Conventions]] for why there's no interpreter on `PATH`) reads everything from files already on disk — nothing queries Databricks live:

- `docs/rls-role-naming/data/master-list-values.csv` — the platform list, nodes, iLab IDs
- `ri_ilab/data/output/ilab_charges.parquet` / `services.parquet` — per-platform ingest row counts
- `ri_ilab/ilab/config.py` (`REMAP_CORE_NAME_DICT`) and `ri_ilab/pipeline/process_facility_cc.py` (`CC_TO_ID`) — name normalisation
- every `ri_pbi_*/*.SemanticModel/definition/**/*.tmdl` — RLS roles and semantic-model membership

`core_name` → `CAPABILITY_CODE` resolution is deterministic (exact match → `REMAP_CORE_NAME_DICT` → `CC_TO_ID` → a hand-verified alias list in `derive.py`), never fuzzy — anything left over is reported as unresolved and excluded, not guessed. Four of the ten milestones (curated gold table, published to Service, manual QA, sign-off) can't be evidenced from local files, so they render blank/striped rather than being guessed at.

11 non-platform capability codes (governance-only, e.g. `ENG`, `MNHS`, `SCI`) are excluded from the default view behind a toggle, leaving 50 tracked platforms.

## Editing and rebuilding

Cell statuses are editable directly in the browser and stored in `localStorage` (`ri-delivery-matrix-overrides-v1`) as *overrides only* — rebuilding with fresh derived data doesn't clobber manual edits, and clearing an override falls back to the derived value. `--data-only` writes just `matrix_data.json` for a quick check of a derivation change without regenerating the full page.

## See also

- `tools/delivery-matrix/README.md` — full rebuild command, decisions baked into the derivation logic, file-by-file breakdown
- [[Overview|RI PBI Production]]
- [[Shared Conventions]] — the `ri_ilab` venv path and `PYTHONIOENCODING` gotcha this tool's rebuild command depends on
- [[QA Test Plan]], [[RLS Alignment Audit]] — sibling initiatives this one doesn't duplicate
- **Derived layer**: none. As of the `f170c9d8` export, `graphify/ri_pbi_production/` has no node for `tools/delivery-matrix/` or `RI_Delivery_Matrix.html` — the generator did not index them — so this is the one note in the project with nothing in the derived layer to point at.
