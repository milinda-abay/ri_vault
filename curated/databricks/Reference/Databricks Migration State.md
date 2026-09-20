# Databricks Migration State

What the `ri_ilab` repo does, what of it now exists natively in Databricks, and — the part that neither the repo docs nor the Databricks workspace states on its own — **which of the two actually feeds Power BI today**.

> [!warning] Point-in-time snapshot
> Verified live on **2026-09-06** against workspace `adb-3993465269917932.12.azuredatabricks.net` (CLI profile `DEFAULT`): catalog/schema/table listings, job and pipeline definitions, job run history, `DESCRIBE HISTORY` last-write times, row counts, and the text of every notebook reachable from a scheduled job. Freshness figures move daily; the structural conclusions move only when someone changes a job.

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: the "In `main()`?" column below (the export's `main()` calls exactly the eight pipelines marked yes). The Plane 3 table was checked against the `ri_pbi_production` export at `f3f3b03` and corrected: it was missing [[Projects/RI PBI Production/Repos/Non-iLab Utilisation/Non-iLab Utilisation|Non-iLab Utilisation]] and three schemas. Everything else is live Databricks state from the dated checks in this note, which the export doesn't carry.

## What the repo is for

`ri_ilab` is a **local pandas ETL** that pulls Monash research-infrastructure data from iLab's SFTP drop, the Elsevier API, and manual CSV drops, normalises it, and uploads Parquet to Databricks so Power BI can read it. Every domain module is the same three files — `fetch.py` → `preprocess.py` → `process.py` — and `main.py` runs them in sequence. See [[Projects/RI iLab/Subsystems/iLab Domain Pipelines|iLab Domain Pipelines]] for the per-domain detail and [[Projects/RI iLab/Subsystems/pen Databricks Upload Package|pen Databricks Upload Package]] for the upload step.

The critical structural fact: **the repo has no scheduler**. `main.py` runs on a person's machine, and `pen/adb_mace.py` is a `__main__` script that copies `data/output/*.parquet` into a Unity Catalog volume and `CREATE OR REPLACE`s tables from it. Nothing in Databricks triggers either.

## The three planes

Work has landed in Databricks in three distinct places, built at different times for different reasons, and **they are not yet connected to each other**.

| Plane | Schemas | Built by | Scheduled? | Feeds Power BI? |
|---|---|---|---|---|
| **Ingest + bronze** (the intended replacement for the repo) | `new_test`, `ilab_bronze` | `ingest_pipeline` (Lakeflow) + one-off notebooks under `/ilab/dev/<domain>/` | Ingest yes (monthly); bronze **no** | **No** |
| **Standalone** (Google-Sheet reference data) | `standalone_bronze`, `standalone_silver` | notebooks under `/ri_standalone/` | Yes (`01_standalone_tables`, nightly) | Yes, via `ri_lakehouse.ri_master_list` |
| **Serving** (what reports actually query) | `ri_ilab`, `ilab_3y`, `ri_lakehouse` | the **repo**, run by hand, + `Daily run - serverless` | Derived tables yes; **base tables no** | Yes — all of it |

## Plane 1 — ingest and bronze

### `ingest_pipeline` replaces `fetch.py`

Lakeflow declarative pipeline `d2391db7-2e23-48f2-8722-597db5e864b9`, serverless, source `/Workspace/Users/milinda.abayawardana@monash.edu/ri_ilab_sftp_ingestion/transformations/ingest.py`. It reads the iLab SFTP drop **directly** with Auto Loader —

```python
spark.readStream.format("cloudFiles").option("cloudFiles.format", "csv")
     .option("pathGlobfilter", "*_monash_university_labs.csv")
     .load("sftp://monash@erpfiles.ilabsolutions.com:22/prod/outgoing/")
```

— which is the same SFTP host the repo's `ConnectSFTP` dials (see [[Projects/RI iLab/Subsystems/Core SFTP Connector|Core SFTP Connector]]). Five streaming tables into `new_test`, all columns left as `STRING`. Job `93376113759500`, cron `21 0 2 5 * ?` — **monthly**, on the 5th at 02:00 Australia/Sydney. Last update `COMPLETED` 2026-09-04.

### Coverage against the repo's 11 pipelines

| Repo pipeline | In `main()`? | Databricks-native equivalent | Status |
|---|---|---|---|
| `charges` | yes | `ingest_pipeline` → `new_test.charges` → `ilab_bronze.ilab_charges` | ingest live, bronze manual |
| `labs` | yes | `new_test.labs` → `ilab_bronze.ilab_labs` | ingest live, bronze manual |
| `members` | yes | `new_test.members` → `ilab_bronze.ilab_members` | ingest live, bronze manual |
| `services` | yes | `new_test.services` → `ilab_bronze.ilab_services` | ingest live, bronze manual |
| `member_funds` | yes | `new_test.members_funds` | **ingest only** — excluded from the pipeline for now (decision recorded 2026-09-14): no bronze table, no historical volume; missing 2026-07 (as of 2026-09-14, see [[Historical Services Bronze Pipeline#Monthly landing check]]) |
| `charge_ack` | yes | — | **not replicated** |
| `pi_fund` | yes | — | **not replicated** |
| `external_institutes` | yes | `standalone_bronze.ri_external_institutes` (from a Google Sheet, not SFTP) | replicated by a *different* route |
| `facility` | commented out | — | **not replicated** |
| `research_income` | commented out | — | **not replicated** |
| `research_output` | commented out | — | **not replicated** |

`pi_fund` and `charge_ack` are the two active SFTP domains with no Databricks path at all. `charge_ack` matters most — `ri_ilab.ilab_charge_ack` holds 638,890 rows and is merged into the charges/award output by `create_charges_award()` (see [[Projects/RI iLab/Subsystems/Post-Processing & Orchestration|Post-Processing & Orchestration]]).

### Historical backfill

The `historical_*` tables in `new_test` and the four `ilab_bronze.ilab_*` tables (named without the `_bronze` suffix their notebooks carry) union the pre-SFTP monthly exports sitting in a UC volume with the live ingest, then deduplicate. This is genuine, careful work — the heterogeneous-Parquet casting pattern, the Photon widening failure, the ANSI `to_timestamp` gotcha, and the "surprisingly large but correct" dedup drops are all documented in [[Historical Services Bronze Pipeline]]. It has no equivalent in the repo; the repo only ever sees the current month's SFTP files.

Every one of these notebooks was run by hand via one-off `databricks jobs submit`, and none was in a job — until **2026-09-12**, when the four `ilab_*_bronze` notebooks were wrapped in job `ilab_bronze_tables` (`916154989512260`) and triggered from `ingest_pipeline`, and the five `historical_*` notebooks in the manual job `ilab_historical_tables` (`957557695632880`). That job first ran on 2026-09-15 (run `935176870985425`), cascading into bronze. All 9 tables came out identical to their pre-run backups. See [[Historical Services Bronze Pipeline]].

## Plane 2 — standalone reference data

Job **`01_standalone_tables`** (`163544004016522`), cron `5 23 0 * * ?` — nightly 00:23 Australia/Sydney. It had six tasks on 2026-09-06, eight from 2026-09-12, and **13 since 2026-09-14**, in three chains. Each task runs only after the one before it in its chain succeeds. The three bronze builds read Google Sheets and run on the classic cluster; every other task is serverless.

| Chain | Tasks, in order | Writes |
|---|---|---|
| Master list | `ri_master_list_bronze` → `ri_master_list_bronze_validate` → `ri_master_list_silver` → `ri_master_list_silver_validate` → `ri_master_list_publish` | `standalone_bronze.ri_master_list_bronze`, `standalone_silver.ri_master_list`, `ri_lakehouse.ri_master_list` |
| External institutes | `ri_external_institutes_bronze` → `ri_external_institutes_bronze_validate` → `ri_external_institutes_silver` → `ri_external_institutes_silver_validate` | `standalone_bronze.ri_external_institutes`, `standalone_silver.ri_external_institutes` |
| Remap tables | `remap_tables_bronze` → `remap_tables_bronze_validate` → `remap_tables_silver` → `remap_tables_silver_validate` | the three `standalone_bronze.remap_*` tables and their `standalone_silver` copies |

Since 2026-09-14, `ri_lakehouse.ri_master_list` is written only by `ri_master_list_publish`, after silver validates. See [[ri_master_list SCD2 Reference]].

All three read Google Sheets through one service account and merge SCD Type 2 per [[Databricks Conventions]]. Row state on 2026-09-06:

| Table | Total | Active |
|---|---|---|
| `standalone_bronze.ri_master_list_bronze` | 207 | 117 |
| `standalone_bronze.ri_external_institutes` | 725 | 366 |
| `standalone_bronze.remap_core_name` | 31 | 31 |
| `standalone_bronze.remap_customer_institute` | 10 | 10 |
| `standalone_bronze.remap_customer_lab` | 27 | 27 |
| `standalone_silver.ri_external_institutes` | 366 | 366 |
| `standalone_silver.ri_master_list` | 117 | 117 |
| `standalone_silver.remap_core_name` | 31 | 31 |
| `standalone_silver.remap_customer_institute` | 10 | 10 |
| `standalone_silver.remap_customer_lab` | 27 | 27 |
| `ri_lakehouse.ri_master_list` | 117 | — |

The four silver rows below `ri_external_institutes` were added 2026-09-15, from the job's own outputs that night; `ri_lakehouse.ri_master_list` was re-checked the same day and still holds 117. Every other row is still the 2026-09-06 figure.

Recent runs: `SUCCESS` on 2026-09-03, 09-05 and 09-06; `RUN_EXECUTION_ERROR` on 09-02 and 09-04. After the 13-task cutover, `SUCCESS` 13/13 on 2026-09-14 (manual run `750702859638640`) and 2026-09-15 (scheduled run `1048366854596689`).

**This is the only plane that is fully wired end to end** — sheet → bronze → silver → serving → Power BI, with the serving write gated on silver validation since 2026-09-14. See [[ri_master_list SCD2 Reference]], [[ri_external_institutes SCD2 Migration]], [[Standalone Remap Tables Reference]].

## Plane 3 — what Power BI actually reads

Every report reads catalog `pen_research_infrastructure_insights_prd`, almost always through `get_table_from_mace(table, schema)` in `expressions.tmdl`. Checked against the `ri_pbi_production` export at `f3f3b03` on 2026-09-19:

| Report | Schemas it reads |
|---|---|
| [[Projects/RI PBI Production/Repos/iLab Utilisation/iLab Utilisation|iLab Utilisation]] | `ilab_3y` (fact, `dim_ilab_services`, `vw_dim_ilab_customer_lab`), `ri_lakehouse` (master list) |
| [[Projects/RI PBI Production/Repos/Awards/Awards|Awards]] | `ri_ilab`, `ri_lakehouse`, `ri_research_dashboard`, `dim_env` |
| [[Projects/RI PBI Production/Repos/Publication/Publication|Publication]] | `ri_ilab`, `ri_lakehouse`, `ri_research_dashboard` |
| [[Projects/RI PBI Production/Repos/Finance/Finance|Finance]] | `ri_lakehouse`, `bim_env`; plus four direct reads of `lakehouse_bim_prd.account`, a different catalog |
| [[Projects/RI PBI Production/Repos/Risk/Risk|Risk]] | `ri_lakehouse` (single-argument helper; the schema comes from the connection record) |
| [[Projects/RI PBI Production/Repos/Survey/Survey|Survey]] | `survey` (read inline, not through the helper), `ri_lakehouse` (master list, since 2026-09-15) |
| [[Projects/RI PBI Production/Repos/Asset/Asset|Asset]] | `ri_lakehouse`, `ri_research_dashboard` (`dim_finance_fund_centre`) |
| [[Projects/RI PBI Production/Repos/Non-iLab Utilisation/Non-iLab Utilisation|Non-iLab Utilisation]] | `pure_silver` per its note (the export can't resolve `Databricks_MACE[database]` statically), `ri_lakehouse` (master list) |

`ri_lakehouse` and `ilab_3y` are refreshed nightly by job **`Daily run - serverless`** (`234277055527586`, 01:00, `SUCCESS` every day 09-02 → 09-06): `ilab_post_ingestion` → `dim_services` build `ilab_3y`'s derived tables, and `ri_lakehouse_prod` builds `ri_lakehouse`.

But those notebooks only ever *transform within* the serving schemas. Their **base** tables — `ilab_3y.ilab_charges_award`, `ri_ilab.research_output`, and the rest — have no scheduled writer. They come from the repo, by hand.

## The load-bearing finding: freshness

`DESCRIBE HISTORY` last-write times, 2026-09-06 — the charges rows updated **2026-09-12**:

| Table | Last written | Written by |
|---|---|---|
| `ilab_3y.ilab_award_income_researcher` | **2026-09-05** | `ilab_post_ingestion`, nightly |
| `ri_lakehouse.ri_master_list` | **2026-09-15** (re-checked that day) | `ri_master_list_publish`, nightly, only after silver validates; `ri_master_list_bronze` wrote it until 2026-09-14 |
| `new_test.charges` | **2026-09-12** | `ingest_pipeline`, one-off full refresh after the CSV reader fix |
| `new_test.labs` / `members` / `services` / `members_funds` | **2026-09-04** | `ingest_pipeline`, monthly |
| `standalone_bronze.ri_master_list_bronze` | 2026-09-02 | nightly SCD2 merge (no write when nothing changed) |
| `standalone_silver.ri_external_institutes` | **2026-09-15** (re-checked that day) | `ri_external_institutes_silver`, nightly since 2026-09-12; manual before that |
| `standalone_bronze.remap_core_name` | 2026-08-29 | nightly SCD2 merge |
| `ri_lakehouse.ri_external_institutes` | 2026-08-29 | **manual** |
| `ilab_bronze.ilab_charges` | **2026-09-12** | rebuilt by hand after the CSV reader fix, then again the same day by `ilab_bronze_tables` via the new ingest trigger |
| `ri_ilab.ilab_charges_award` | **2026-08-04** | **manual (the repo)** |
| `ilab_3y.ilab_charges_award` | **2026-08-04** | **manual (the repo)** |

Read the top and bottom rows together: `ilab_award_income_researcher` is the fact table behind [[Projects/RI PBI Production/Repos/iLab Utilisation/iLab Utilisation|iLab Utilisation]], and it was rebuilt last night — **from a base table last written on 2026-08-04**. The nightly job is faithfully re-deriving month-old data. The same holds for `fact_pure_publication`, rebuilt nightly in `ri_lakehouse` from `ri_ilab.research_output` (2026-08-04).

## Five gaps

**1. The bronze plane is dead-ended.** Every notebook reachable from a scheduled job was exported and grepped: not one references `ilab_bronze`, `new_test`, or `standalone_bronze` as a source. The four `ilab_bronze` tables still hold exactly the row counts recorded when they were built (1,467,512 / 243,391 / 146,141 / 6,720) while `new_test.charges` has grown from 635,553 to 794,261 — they have not been rebuilt since 2026-08-19, and nothing would notice if they never were. The bronze layer is a **correct, well-documented, unconsumed artifact**.

(Both figures in that sentence are themselves now superseded: raw `charges` holds 157,666 rows after the 2026-09-12 full refresh, and bronze charges 1,441,141 — see the callouts below.)

**Partly closed 2026-09-12.** `ilab_bronze` is now rebuilt automatically after every successful `ingest_pipeline` run, via `ilab_bronze_tables` (`916154989512260`) called from a `trigger_bronze` task in job `93376113759500`. What remains true is the *consumer* half of this gap: nothing downstream reads `ilab_bronze` yet, so it is still an unconsumed artifact — just no longer a stale one.

> [!warning] The row-count evidence above is superseded
> `ri_ilab/docs/2026-09-09-ilab-historical-bronze-tables.md`, verified live on **2026-09-09** and re-checked live on **2026-09-11**, records the four bronze tables at 1,492,840 / 242,589 / 149,330 / 6,758 rows (charges / services / members / labs) against the 1,467,512 / 243,391 / 146,141 / 6,720 recorded at their 2026-08-17/18 build and still seen here on 2026-09-06. So they **have** been rebuilt by hand at least once since 2026-08-19. The conclusion stands — nothing scheduled reads or writes them — but "not rebuilt since 2026-08-19" no longer holds. Current figures live in [[Historical Services Bronze Pipeline]].

> [!warning] Charges superseded again on 2026-09-12
> `ingest_pipeline`'s CSV readers were missing `multiLine`, so roughly 1% of every charges extract arrived as split rows carrying a blank `Charge ID`. After the fix, a charges-only full refresh and a bronze rebuild on **2026-09-12**, `ilab_bronze.ilab_charges` holds **1,441,141** rows across 10 source files, with no null `charge_id` and no null `creation_date`, and 105 previously hidden charges were recovered. The other three bronze tables are untouched. Full account: [[Historical Services Bronze Pipeline]].

**2. The repo is still the sole feed for iLab fact data, and it is manual.** No scheduled job writes to `ri_ilab` or to `ilab_3y`'s base tables. Two Power BI reports ([[Projects/RI PBI Production/Repos/Awards/Awards|Awards]], [[Projects/RI PBI Production/Repos/Publication/Publication|Publication]]) read `ri_ilab` directly. The migration has built a parallel path but has not switched anything over, so the single-person, single-laptop dependency the [[ri_master_list SCD2 Reference|master-list handover]] flags for *that* pipeline applies with more force to the whole iLab fact chain.

**3. Two disabled pipelines still have live consumers.** `run_research_output()` and `run_facility()` are commented out in `main.py`, but `ri_lakehouse_prod` reads `ri_ilab.research_output` every night to build `fact_pure_publication`, which [[Projects/RI PBI Production/Repos/Publication/Publication|Publication]] queries. Disabling the producer did not disconnect the consumer — it froze it.

**4. Three copies of external institutes, three different row counts.** `ri_ilab.external_institutes` (366, from the repo), `standalone_silver.ri_external_institutes` (366, from the Google Sheet), `ri_lakehouse.ri_external_institutes` (**384**, last written 2026-08-29, no scheduled writer). Which one is authoritative is not recorded anywhere, and the third disagrees with the other two.

**5. `remap_core_name` duplicates `ilab/config.py`.** 31 governed, SCD2-versioned mappings in `standalone_bronze` overlap the hardcoded Python dicts the repo applies during preprocessing. [[Standalone Remap Tables Reference]] already flags this; nothing reads the table yet, so today the repo's dicts win by default.

Two smaller ones: `standalone_gold` is empty; and, on 2026-09-06, `standalone_silver` held a single table whose build notebook was in no job. That second one is closed: since 2026-09-14 `standalone_silver` holds five tables (`ri_external_institutes`, `ri_master_list` and the three `remap_*` tables), all rebuilt nightly by `01_standalone_tables`. The `ilab` schema (56 tables) and the unscheduled `Data Refresh` job that populates it are the pre-`ilab_3y` generation, last touched 2026-03-30 — legacy, not part of the current picture.

## Doc drift found while verifying

The repo's `docs/` are ahead of the vault on design but behind on the workspace. Four claims are no longer true:

| Doc claim | Live state |
|---|---|
| "⚠️ Known issue as of 2026-09-02: all four tasks point at paths that no longer exist and the job will fail on its next scheduled run" (in both the master-list and external-institutes docs) | All six task paths are correct; the job has succeeded on 09-03, 09-05 and 09-06 |
| Master-list doc: task keys left as `ri_master_list` / `test_ri_master_list` | Live keys are `ri_master_list_bronze` / `ri_master_list_bronze_validate` |
| External-institutes doc: a `validate_ri_external_institutes` task | Live key is `ri_external_institutes_bronze_validate` |
| Remap doc: "**not currently scheduled** — not yet wired into the `01_standalone_tables` job" | `remap_tables_bronze` and `remap_tables_bronze_validate` are both tasks in that job |

All four sit in files with uncommitted working-tree edits in `ri_ilab`, so the fixes may already be half-written.

## The shape of it, in one line

The migration has rebuilt the **left end** (SFTP ingest, historical backfill, bronze consolidation) and the **reference-data spine** (Google Sheets → SCD2 → `ri_master_list`), but the **middle** — the transform that turns raw iLab extracts into `ilab_charges_award` — exists only as pandas on a laptop, and everything Power BI reads still hangs off it.

## 2026-09-17 — `pure_bronze` exists

A fourth plane, distinct from the three above: `pure_bronze` re-creates, one notebook per table, the 15 Pure-derived tables the old `ri_non_ilab` Power BI report reads from `ri_lakehouse` — today built by the PURE section of `ri_lakehouse_prod`. All 15 tables were built for the first time on 2026-09-17, run by hand; no scheduled job yet, and the report has not been cut over. Row counts and parity results live in [[Pure Bronze Pipeline]], not restated here.

## 2026-09-18 — `pure_silver` exists

`pure_silver` is now built from `pure_bronze`: the same 15 tables, 8 with ported Power Query preprocess logic and 7 pass-throughs, plus a shared `%run` helper notebook (`pure_silver_common`) — the catalog's first shared-helper pattern rather than per-notebook duplication. All 15 build and validate notebooks passed on their first run, 2026-09-18, run by hand; no scheduled job yet, and the report has not been cut over. Row counts, validate results, and the scope decisions behind what did and didn't port live in [[Pure Silver Pipeline]], not restated here.

Later the same day, `pure_silver` got its first Power BI consumer: `ri_pbi_non_ilab_utilisation`, a new build of the legacy report's visible pages on 8 silver tables, not yet published. See [[Projects/RI PBI Production/Repos/Non-iLab Utilisation/Non-iLab Utilisation|Non-iLab Utilisation]].

## See also

- [[Projects/RI iLab/Overview|RI iLab]] — the repo this note measures
- [[Databricks Conventions]] — the standing rules the standalone plane follows
- [[Projects/RI iLab/Subsystems/iLab Domain Pipelines|iLab Domain Pipelines]] — what the repo's 11 pipelines each do
- [[Projects/RI iLab/Subsystems/pen Databricks Upload Package|pen Databricks Upload Package]] — the manual upload step that makes plane 3 possible
- [[Historical Services Bronze Pipeline]] — the bronze plane in detail
- [[Pure Bronze Pipeline]] — the fourth plane, the `ri_non_ilab` report's Pure tables re-implemented in `pure_bronze`
- [[Pure Silver Pipeline]] — the cleaned layer built from `pure_bronze`
- [[ri_master_list SCD2 Reference]] — the one fully-wired pipeline, and its own ownership gap
- [[ri_external_institutes SCD2 Migration]] · [[Standalone Remap Tables Reference]] — the other two standalone builds
- [[Projects/RI PBI Production/Repos/iLab Utilisation/iLab Utilisation Data Model|iLab Utilisation Data Model]] — the report whose fact table is being rebuilt nightly from month-old inputs
- [[Projects/RI PBI Production/Overview|RI PBI Production]] — the reports on the consuming end
- [[Overview|Databricks]] — the catalog this note surveys
- **Derived layer — repo side** (`graphify/`, never hand-edited): [[main.py run_() Orchestrator]], [[run_research_output()]], [[run_facility()]], [[run_research_income()]], [[create_charges_award()]], [[_COMMUNITY_Main Orchestration]], `Databricks Table Names and SQL Schemas` *(no node since export `1ac3015`)*
- **Derived layer — platform side** (`graphify/`, never hand-edited): `ingest_pipeline (raw SFTP ingestion)` *(no node since export `1ac3015`)*, [[preprocess_ilab Lakeflow pipeline (adjacent)]], [[Job 01_standalone_tables (id 163544004016522)]], [[standalone_bronze.ri_master_list_bronze]], [[ilab_bronze Input Tables]], [[ilab_bronze.ilab_charges]], [[ilab_bronze.ilab_services]], [[ilab_bronze.ilab_members]], [[ilab_bronze.ilab_labs]]
- **Derived layer — the Power BI consumers named above** (`graphify/`, never hand-edited): [[ilab_award_income_researcher]], [[ilab_award_income_researcher_1]], [[research_output]], [[pen_research_infrastructure_insights_prd.ri_lakehouse.ri_master_list]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[ConnectSFTP]], [[main.py]]
