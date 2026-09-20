# Standalone Remap Tables Reference

Three new SCD Type 2 Delta tables in `pen_research_infrastructure_insights_prd.standalone_bronze` — `remap_core_name`, `remap_customer_institute`, `remap_customer_lab` — built from one Google Sheet's three tabs, same convention as [[ri_master_list SCD2 Reference|ri_master_list]] / [[ri_external_institutes SCD2 Migration|ri_external_institutes]].

This note is the single source of truth for this table. It absorbed `docs/2026-08-29-ri-standalone-remap-tables.md` from the `ri_ilab` repo on **2026-09-08**; that file has been deleted.

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: the absorbed repo doc has no graphify nodes, consistent with its deletion, and the derived links in See also resolve. The `REMAP_CORE_NAME_DICT` overlap is still in the graph, as [[REMAP_CORE_NAME_DICT (ilabconfig.py)]] linked to [[Standalone Remap Tables (remap_core_name, remap_customer_institute, remap_customer_lab)]]. Everything else is live Databricks state from the dated checks in this note, which the export doesn't carry.

## Introduction

Each table is a manually curated old-name → new-name lookup used to normalise names elsewhere in the RI Insights estate:

| Sheet tab | Target table | Columns | Rows (2026-08-29) |
|---|---|---|---|
| `REMAP_CORE_NAME` | `remap_core_name` | `OLD_CORE_NAME` → `NEW_CORE_NAME` | 31 |
| `REMAP_CUSTOMER_INSTITUTE` | `remap_customer_institute` | `OLD_NAME` → `NEW_NAME` | 10 |
| `REMAP_CUSTOMER_LAB` | `remap_customer_lab` | `OLD_LAB_NAME` → `NEW_LAB_NAME` | 27 |

Each row is a mapping: an obsolete/duplicate/misspelled value (`OLD_*`) to the value that should be used instead (`NEW_*`). All three tabs were verified free of duplicate or blank `OLD_*` keys at migration time, so `OLD_*` is a safe SCD2 identity column in each case.

## The overlap worth flagging explicitly

`REMAP_CORE_NAME` duplicates data already hardcoded in the `ri_ilab` repo's `ilab/config.py` — see [[Projects/RI iLab/Subsystems/iLab Domain Pipelines|iLab Domain Pipelines]]'s `REMAP_CORE_NAME_DICT` (e.g. `MICROMON` → `MONASH GENOMICS & BIOINFORMATICS PLATFORM (MICROMON GENOMICS)` appears in both places). **This migration does not reconcile the two or wire them together** — that's a separate, undecided piece of work, not an oversight here.

## Source of truth and rebuild pipeline

Google Sheet ("Standalone remap tables", 3 tabs) → one build notebook, one shared `run_scd2_load(...)` function called once per tab → the three target tables.

- **Build notebook**: `remap_tables_bronze` (renamed 2026-09-02 from `remap_tables`, matching the `<table>_bronze`/`<table>_bronze_validate` convention — see [[Databricks Conventions]]). The sheet's own header row already matches the target column names (uppercase, e.g. `OLD_CORE_NAME`), so unlike `ri_master_list`/`ri_external_institutes` there's no lowercase-to-uppercase rename step needed.
- **Schedule, corrected 2026-09-09**: this note previously said the build notebook wasn't wired into any job — that's now wrong. Sometime between 2026-09-02 and 2026-09-04 it was added to [[Job 01_standalone_tables (id 163544004016522)|"01_standalone_tables"]] as `remap_tables_bronze`, running on the same classic job cluster as `ri_master_list_bronze`/`ri_external_institutes_bronze` (`Standard_D4ds_v5`, cluster policy `001F54073034F458`) — the same `ConnectionResetError`-on-serverless caveat applies to ad hoc runs. Its validate notebook (`remap_tables_bronze_validate`) is wired in too, as a dependent task that runs after the build task succeeds. See [[ri_master_list SCD2 Reference]] for how this was discovered (a live job-config check for an unrelated regression) — nothing in either the sheet or the source doc announced the change.

## How to update it

1. Edit the relevant tab of the Google Sheet directly — add or change a mapping row.
2. Leave blank cells alone — they become `NULL` automatically.
3. Re-run the `remap_tables_bronze` notebook (classic cluster — see the caveat above); it processes all three tabs/tables in one run.
4. Downstream consumers must filter `WHERE _ROW_ACTIVE_FLAG = 'Y'` to get current state — there is no compatibility view, the same simplification as `ri_external_institutes`.

## How a rebuild changes history

The generic mechanism is in [[Databricks Conventions]]; what is specific to these three tables:

- `_BUSINESS_KEY` hashes the **sole** identity column (`OLD_CORE_NAME`, `OLD_NAME`, or `OLD_LAB_NAME` respectively). Changing an `OLD_*` value is therefore treated as a *new mapping* — the old version closes and a new one opens under a fresh `_BUSINESS_KEY` — not as an edit of the existing one.
- Closing a row covers both "mapping removed from the sheet" and "mapping's target (`NEW_*`) changed", since the old version has no exact match either way.
- Each of the three tables is compared independently, in one notebook run.
- **Verified idempotent**: a second consecutive run against unchanged sheet data produced 0 opened / 0 closed across all three tables.

Every value a name has resolved to over time:

```sql
SELECT * FROM pen_research_infrastructure_insights_prd.standalone_bronze.remap_core_name
WHERE OLD_CORE_NAME = 'MICROMON'
ORDER BY _START_TIMESTAMP;
```

Current state only:

```sql
SELECT * FROM pen_research_infrastructure_insights_prd.standalone_bronze.remap_core_name
WHERE _ROW_ACTIVE_FLAG = 'Y';
```

## Column reference

All three tables share the same shape: two business columns plus the five SCD2 metadata columns.

| Column | Type | Description |
|---|---|---|
| `OLD_*` (`OLD_CORE_NAME` / `OLD_NAME` / `OLD_LAB_NAME`) | string | Identity column / SCD2 business key source. The obsolete/duplicate/misspelled value being remapped. Unique per table in the source sheet. |
| `NEW_*` (`NEW_CORE_NAME` / `NEW_NAME` / `NEW_LAB_NAME`) | string | The canonical value to use instead. Versioned attribute — a change here opens a new row-version under the same `_BUSINESS_KEY`. |
| `_BUSINESS_KEY` | string | SCD2 identity hash — a deterministic hash of the sole identity column per table. |
| `_SURROGATE_KEY` | bigint | SCD2 per-version surrogate key. |
| `_START_TIMESTAMP` | timestamp | When this row-version became active. |
| `_EXPIRATION_TIMESTAMP` | timestamp | When this row-version stopped being active. `9999-12-31 23:59:59.999` sentinel while still active. |
| `_ROW_ACTIVE_FLAG` | string | `Y`/`N` — current version vs. historical. |

No separate history table or compatibility view — same simplification as `ri_external_institutes`; downstream consumers filter `WHERE _ROW_ACTIVE_FLAG = 'Y'` themselves.

## Validation

The same table-family pattern as `ri_external_institutes`: originally covered by the combined `validate_standalone_bronze` notebook (2026-08-31), split back apart 2026-09-02 into a dedicated `remap_tables_bronze_validate` notebook covering just these three tables (see [[ri_external_institutes SCD2 Migration]] for the full checks list and the reasoning behind the split — a combined notebook was judged a single point of failure). It's read-only (no Google Sheets access), so it runs on serverless — but as of the 2026-09-09 correction above, it **is** wired into the job, as the task dependent on `remap_tables_bronze`.

13/13 structural checks passed for each of the three tables as of 2026-08-31 (31/10/27 active rows respectively, 0 historical — no rebuilds since bootstrap). Re-verified again 2026-09-02 via the split-out notebook, same result. **Re-verified live 2026-09-09**: still 31/10/27, all active, 0 historical — unchanged despite the notebook now running on the job's nightly schedule (see Schedule above), because no sheet edits have happened yet; a no-op rebuild is idempotent by design (see [How a rebuild changes history](#how-a-rebuild-changes-history) above) and produces no new versions. One scheduled run did fail outright — `remap_tables_bronze` on 2026-09-04 — but that failure didn't corrupt state (the table is still exactly 31/10/27 today), and the same class of intermittent failure has since hit the other two build tasks in this job too (see [[ri_master_list SCD2 Reference]]).

## Silver (since 2026-09-14)

Each table now has a `standalone_silver` copy under the same name. It holds bronze's active rows with all 7 columns unchanged and in bronze's order. Nothing reads the silver tables yet; they give a future consumer a validated current-state table that needs no `_ROW_ACTIVE_FLAG` filter.

| Task | Depends on | What it does |
|---|---|---|
| `remap_tables_silver` | `remap_tables_bronze_validate` | Overwrites all three silver tables in one run. Serverless. |
| `remap_tables_silver_validate` | `remap_tables_silver` | 11 parity checks per table against bronze's active rows, 33 in all |

The 11 checks: both tables exist; the schema matches by name, type and position; silver is not empty; every row is active; every expiration is the sentinel; `_SURROGATE_KEY` and `_BUSINESS_KEY` are unique; the `OLD_*` identity column is never null (a FAIL here, where the master list only WARNs); the row count equals bronze active; and every column matches via `exceptAll` in both directions. The cross-reference checks against `ri_master_list_bronze` and `ri_external_institutes` stay in `remap_tables_bronze_validate`, as do the SCD2 history checks, since silver holds no history.

| Silver table | Rows (2026-09-15) |
|---|---|
| `standalone_silver.remap_core_name` | 31 |
| `standalone_silver.remap_customer_institute` | 10 |
| `standalone_silver.remap_customer_lab` | 27 |

All 33 checks passed on the manual run `750702859638640` (2026-09-14) and the scheduled run `1048366854596689` (2026-09-15). The design is `docs/superpowers/specs/2026-09-14-standalone-silver-remaining-tables-design.md` in this vault.

## See also

- [[Databricks Conventions]]
- [[ri_external_institutes SCD2 Migration]]
- [[Projects/RI iLab/Subsystems/iLab Domain Pipelines|iLab Domain Pipelines]] — where `REMAP_CORE_NAME_DICT` is documented
- [[Job 01_standalone_tables (id 163544004016522)]] — the job this notebook is now wired into (as of the 2026-09-09 correction above)
- [[ri_master_list SCD2 Reference]] — the sibling note where this job's other 2026-09-09 findings (task renames, the third undocumented task pair, the new intermittent failure pattern) are documented
- [[Projects/RI iLab/Initiatives/iLab Silver Layer Migration|iLab Silver Layer Migration]] — the open decision about whether silver reads these governed tables or inlines the dicts instead
- [[Projects/RI iLab/Overview|RI iLab]]
- [[Overview|Databricks]] — the catalog these tables live in
- **Derived layer** (`graphify/`, never hand-edited): `Standalone Remap Tables Reference Note` *(no node since export `1ac3015`; nearest is [[Standalone Remap Tables (remap_core_name, remap_customer_institute, remap_customer_lab)]])*, `REMAP_CORE_NAME_DICT vs Governed Remap Table Overlap` *(no node since export `1ac3015`; nearest is [[REMAP_CORE_NAME_DICT (ilabconfig.py)]])*, [[Inline REMAP_ Literals vs Governed Remap Tables]], [[core_name Facility Dimension (post-remap values)]], [[ilabconfig.py]], `_COMMUNITY_Cross-System Data Governance` *(no community since export `1ac3015`)*
