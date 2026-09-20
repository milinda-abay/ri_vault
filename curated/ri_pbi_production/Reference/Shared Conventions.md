# Shared Conventions

Conventions that hold across all 7 repos in [[Overview|RI PBI Production]]. Repo-specific detail lives in each repo's own note and its `CLAUDE.md` — check those before assuming a convention below carries over exactly.

## PBIP layout

Each repo has:
- a `<name>.pbip` manifest
- a `<name>.SemanticModel/definition/` folder (TMDL): `expressions.tmdl` (M/Power Query), `relationships.tmdl`, `tables/*.tmdl`, `roles/*.tmdl` (RLS), `model.tmdl`, `database.tmdl`, `cultures/*.tmdl`
- a `<name>.Report/definition/` folder (PBIR): `pages/<pageId>/page.json` + `visuals/`

The semantic-model folder is **not** reliably named after the repo. [[Awards]] is the only repo whose model folder keeps the `pbi_` infix (`ri_pbi_awards.SemanticModel`); the other six drop it (`ri_asset`, `ri_finance`, `ri_ilab_utilisation`, `ri_publication`, `ri_risk`, `ri_survey`). Glob for `*.SemanticModel` rather than deriving the name from the repo.

## No build, lint or test tooling

There is nothing to compile or run. Projects are edited via Power BI Desktop and/or `pbi-cli`. Prefer the `pbi-cli` skills (power-bi-modeling, power-bi-dax, power-bi-deployment, power-bi-security, power-bi-partitions, power-bi-visuals, power-bi-docs, power-bi-diagnostics) over hand-editing TMDL/JSON — most require an active `pbi connect` session against the live model.

## Databricks as source system

Data is sourced from Databricks, catalog `pen_research_infrastructure_insights_prd`, via a `Databricks_MACE` connection record and a `get_table_from_mace` helper defined in each model's `expressions.tmdl`. As of the 2026-09-15 export, all seven repos' live master-list path shares SQL warehouse `5cc645cded66580f` — [[Survey]] joined the other six then; see below.

The helper's signature is not uniform:

- **Two arguments** — `get_table_from_mace(table, schema)` — in [[Asset]], [[Awards]], [[Finance]], [[Publication]] and [[iLab Utilisation]], joined by [[Survey]] as of 2026-09-15 (so far only confirmed for its `DIM_FACILITY` path). The schema is passed per call, so one model can read `ri_lakehouse`, `ri_ilab`, `ilab_3y` and `ri_research_dashboard` side by side.
- **One argument** — `get_table_from_mace(table)` — in [[Risk]], which takes the schema from `Databricks_MACE[database]` (`ri_lakehouse`) instead.

Several repos keep the other variant commented out above the live one, so read past the comment block before assuming an arity. [[Survey]] used to have no helper at all — it hardcoded `Databricks.Catalogs(...)` inline, against a different warehouse (`1fb6bc7e83d60086`) — but as of the 2026-09-15 export its `DIM_FACILITY` table was repointed onto the shared `Databricks_MACE`/`get_table_from_mace` pattern too, on the same warehouse as the other six. The old inline path still exists in the model as unloaded expressions; see [[Survey]].

## Shared reference table

Six repos carry `dim_ri_master_list` under that model-side name as of 2026-09-15 (iLab Utilisation's copy was renamed from `dim_facility_master_list` that day); [[Survey]] alone still carries a derived variant, `DIM_FACILITY`. See [[dim_ri_master_list Reference|dim_ri_master_list]] — it covers the column groups, the per-repo join keys, and why the join key still doesn't carry between repos even where the table name now does.

## Row-level security

Six of the seven repos define RLS roles under `roles/*.tmdl` — 280 role files, 325 filters; [[Asset]] has none. **Do not assume one role means one filter on one column.** See [[RLS Patterns]] for the shapes, the per-repo filter columns and counts, and how to add a role safely.

## Centralized measures

Measures live in a table named `key_measures` / `KeyMeasures` / `Key Measures` (naming varies by repo), often paired with a separate `Time intelligence` / `Time Intelligence` table for date-comparison helpers. Add new measures there rather than attaching them to dimension/fact tables.

## Editing TMDL and PBIR files

**Never use `sed -i`, or any line-rewriting tool, on TMDL or PBIR files.** They are CRLF, and `sed -i` rewrites the whole file to LF.

The damage is invisible in review: these repos set `core.autocrlf=true`, so git normalizes to LF in the index and still shows a clean `1 insertion, 1 deletion` diff while every line ending on disk has changed. Edit by exact string match, or read → replace → write in Node without touching line endings. Verify with a byte-level check — count `\r\n` pairs before and after, and confirm the byte delta equals the expected text-length change — rather than trusting `git diff`.

Node is on `PATH` and is the better choice for ad-hoc PBIR/JSON inspection; no JSON tooling (`jq`) is installed.

## Python interpreter

There is no interpreter on `PATH` — bare `python` / `python3` resolve to the Windows Store stub and fail. Use the venv from the neighbouring `ri_ilab` project:

```
C:\Users\maba0001\projects\ri_ilab\.venv\Scripts\python.exe
```

Python 3.12 with `openpyxl` installed, used for the `.xlsx` deliverables at the workspace root. From a Bash shell, call it as `/c/Users/maba0001/projects/ri_ilab/.venv/Scripts/python.exe`, and set `PYTHONIOENCODING=utf-8` whenever the script prints non-ASCII — the default console codec is cp1252 and raises `UnicodeEncodeError` on the ✅/❌/— characters these documents use.

## Known gotcha: hardcoded local file paths

Three repos bake an absolute local path into an M expression. Verified 2026-09-01:

| Repo | Path baked in | Status |
|---|---|---|
| [[Publication]] | `C:\Users\maba0001\projects\ri_pbi_publication\ref\journal_list.csv` | ❌ Does not resolve — the file now lives under `...\ri_pbi_production\ri_pbi_publication\ref\` |
| [[Risk]] | `C:\Users\maba0001\projects\ri_pbi_risk\Key Risks.xlsx` | ❌ Does not resolve — same prior-layout mismatch |
| [[Survey]] | `C:\Users\maba0001\projects\ri_insights\data` (a `data_path` parameter feeding `output\facility.parquet`) | ⚠️ Resolves, but dormant — no table loads through it |

Publication and Risk carry the same prior-working-directory mismatch: the paths assume `projects\<repo>\...` rather than the current `projects\ri_pbi_production\<repo>\...`.

Survey's is different in kind and easy to misread. The `data_path` parameter points at a sibling project entirely outside this workspace, and it does resolve on this machine — but the chain it feeds (`fetch_base_facility` → `fetch_base_facility (2)` → `Merge1`) sits in the `DEV` query group and **no table partition resolves through it**. `DIM_FACILITY` now loads from the Databricks master list instead. The parquet dependency is left-over scaffolding rather than a live source, which is why it should not be read as an active refresh risk — but it is also why the parameter survives untouched.

If a table refresh fails with a file-not-found error, check for this mismatch first via `pbi-cli` partitions tooling. Any live local-file dependency also breaks scheduled refresh in the Service unless a gateway is configured — relevant to the `DATA-01`/`DATA-03` checks in [[QA Test Plan]].

## See also

- [[dim_ri_master_list Reference|dim_ri_master_list]] — the shared identity table and its per-repo join keys
- [[RLS Patterns]] — how row-level security is built across the suite
- [[Projects/Databricks/Overview|Databricks]] — the catalog these repos read from, and the standing rules it is built to: [[Projects/Databricks/Reference/Databricks Conventions|Databricks Conventions]] covers the medallion layout, column naming and SCD2 rules governing the `pen_research_infrastructure_insights_prd` tables
- [[Projects/Databricks/Reference/Databricks Migration State|Databricks Migration State]] — which of those tables are actually fresh, and which reports read stale ones
- [[Overview|RI PBI Production]]
- **Derived layer** (`graphify/`, never hand-edited): `CLAUDE.md Workspace Guidance` *(no node since export `0c73b0cf`)*, [[Power BI Project PBIP Format]], [[_COMMUNITY_MACE Source Tables]], [[Databricks MACE Configuration]], [[get_table_from_mace_8]], [[Publication journal_list.csv Dependency]], [[Risk Key Risks.xlsx Dependency]], [[Survey External facility.parquet Dependency]], [[_COMMUNITY_Power Query Environment]]
- **Derived layer — each repo's copy of the shared M helpers** (`graphify/`, never hand-edited): [[Databricks_MACE_1]], [[Databricks_MACE_2]], [[Databricks_MACE_3]], [[Databricks_MACE_4]], [[Databricks_MACE_6]], [[Databricks_MACE_7]], [[get_table_from_mace_1]], [[get_table_from_mace_2]], [[get_table_from_mace_3]], [[get_table_from_mace_4]], [[get_table_from_mace_5]], [[get_table_from_mace_7]], [[data_path]], [[data_path_1]], [[data_path_2]], [[data_path_3]], [[data_path_4]]
