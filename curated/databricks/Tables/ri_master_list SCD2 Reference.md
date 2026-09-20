# ri_master_list SCD2 Reference

**Not `ri_ilab` Python code** — `ri_ilab/docs/2026-08-19-ri-master-list-reference.md` documents `pen_research_infrastructure_insights_prd.ri_lakehouse.ri_master_list`, an active-rows-only Delta table (plain overwrite, no history of its own) backed by `pen_research_infrastructure_insights_prd.standalone_bronze.ri_master_list_bronze` (the true SCD2 table, full history), maintained by its own separate notebook pipeline, source-of-truth in a Google Sheet. It is the master dimensional table underpinning **all 8** Power BI reports in [[Projects/RI PBI Production/Overview|RI PBI Production]] (eight since [[Projects/RI PBI Production/Repos/Non-iLab Utilisation/Non-iLab Utilisation|Non-iLab Utilisation]] was built on 2026-09-18; the shared `dim_ri_master_list` tables, and Survey's `DIM_FACILITY`, referenced in that vault's [[Projects/RI PBI Production/Reference/Shared Conventions|Shared Conventions]] note are downstream copies of this same table).

As of **2026-08-28** the reference doc was reviewed and prepared as a handover document for Data Engineering — see [[#Handover to Data Engineering]] below. **2026-09-02, two changes same day**: first the `ri_master_list_history` table + `ri_master_list` view were collapsed into a single `ri_master_list` table (view dropped, history table renamed in place); then that table was split again — full history moved to the new `standalone_bronze.ri_master_list_bronze`, and `ri_lakehouse.ri_master_list` became a plain overwrite of bronze's active rows. Net result: the 7 Power BI reports keep reading an active-rows-only `ri_master_list` (as before 2026-09-02) with **no filter needed**, but it's now a physical overwrite rather than a live view, and follows the `standalone_bronze`/consumption-schema split pattern from [[Databricks Conventions]] rather than a bespoke history-table-plus-view design.

> [!note] Verified live 2026-09-11 (profile `DEFAULT`, read-only)
> `ri_lakehouse.ri_master_list`: MANAGED table, 117 rows, 101 distinct `NODE_ID`, 24 columns. `standalone_bronze.ri_master_list_bronze`: 207 rows, 117 active; newest active `_START_TIMESTAMP` is 2026-08-21 07:58, so no version has been opened since. Every per-column null count below matches the 2026-08-25 snapshot exactly. Job `01_standalone_tables` (`163544004016522`): cron `5 23 0 * * ?` Australia/Sydney, unpaused, `Standard_D4ds_v5`, runs as the individual owner, six tasks in three build/validate pairs under `ri_standalone/`. The 2026-09-11 00:23 run **failed** — see the handover section.

> [!note] Job grew to 8 tasks on 2026-09-12 — the "six tasks" above is a snapshot, not current
> The job definition showed **8 tasks** live on 2026-09-12, and the scheduled runs on 2026-09-13 and 2026-09-14 both executed all 8 — `ri_external_institutes_silver` and `ri_external_institutes_silver_validate` were added that day (see [[ri_external_institutes SCD2 Migration]]), and `ri_master_list_bronze`/`ri_external_institutes_bronze` both picked up retry policies the same day (see the "Diagnosed 2026-09-11" section below). Everything else in the callout above — row/column counts, `INDEX` state, unpaused status — is still only as fresh as 2026-09-11 and has not been re-checked.

> [!note] 13 tasks since 2026-09-14, and `ri_lakehouse.ri_master_list` is published from silver
> The cutover on 2026-09-14 added silver, silver validate and a gated publish for this table, plus silver for the three remap tables. The bronze notebook no longer writes `ri_lakehouse`. Verified live 2026-09-15: 117 rows and 24 columns on `ri_lakehouse.ri_master_list`, matching silver on every column. See [[#Publish flow (since 2026-09-14)]].

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: the reference doc is still indexed (28 nodes), so it stays in the repo as See also says. The opening paragraph's graph-degree claim, report count and model-side table names were out of date and are corrected. Everything else is live Databricks state from the dated checks in this note, which the export doesn't carry.

## What it does

Serves three purposes at once for the Power BI estate: platform/capability filtering, cross-system ID mapping (Pure/iLab/survey/SAP cost-centre), and Row-Level Security group source. Grain is **(capability, node, cost centre)**, not one-row-per-platform — both `node` and `cost centre` are optional, so a row can be capability-only (an umbrella row, e.g. for a platform with no finer tracking), capability+node (one row per sub-location, e.g. `FLOW` has 3: `FLOW-ARA`/`FLOW-CLAYTON`/`FLOW-MHTP`), or repeated once per cost centre when a node draws funding from more than one (`MARP-ARL` appears twice, against `M56007` and `W56007`; `MERC` has 11 cost-centre-only rows so each of eResearch's SAP cost centres rolls up under one capability). This is why the current 117 active rows resolve to only 101 distinct `NODE_ID` values (verified live against Databricks 2026-08-28; the 121-row/98-`NODE_ID` figures in earlier notes are stale — row count dropped via sheet edits between 2026-08-21 and 2026-08-25).

## How to update it

1. Edit the **`Master record`** tab of the Google Sheet directly. Column headers must exactly match the 20-column list the notebook expects (`NEW_COLUMNS`) — adding a sheet column without updating the notebook silently drops it.
2. Leave blank cells alone — they become `NULL` automatically. The sheet's own `index` column is a QA sorting aid only; it's dropped on import and never reaches either table.
3. Trigger a rebuild: wait for the nightly job, or run it on demand (`databricks jobs run-now 163544004016522`). To test outside the job, run the whole chain in order: bronze, bronze validate, silver, silver validate, publish. The bronze build needs the classic cluster (see below). Running publish on its own is guarded: it refuses to write from a missing or empty silver.
4. A `ri_master_list_bronze_validate` failure means the edit broke one of six business-rule/SCD2 invariants (1:1 `NODE_ID`↔`NODE_NAME` and `CAPABILITY_CODE`↔`CAPABILITY_NAME` mappings, controlled vocabularies, `NODE_ID` prefix, exactly one active version per `_BUSINESS_KEY`, valid expiration windows — full list in the source doc) — fix the sheet row, not the notebook, unless it's a genuinely new controlled-vocabulary value. Since 2026-09-14 the business rules run on bronze's active rows before anything is published, so a failure here keeps the edit out of Power BI.
5. No manual publish step. `ri_master_list_publish` writes `ri_lakehouse.ri_master_list` at the end of the job, and only if silver validation passed — see [[#Publish flow (since 2026-09-14)]].

## Publish flow (since 2026-09-14)

Until 2026-09-14 the bronze notebook overwrote `ri_lakehouse.ri_master_list` itself, as its last step, before any validation ran. Since the cutover that day, the write sits at the end of a gated chain in job `01_standalone_tables`:

| Step | Task | What it does |
|---|---|---|
| 1 | `ri_master_list_bronze` | SCD2 merge from the sheet into `standalone_bronze.ri_master_list_bronze`, and nothing else. Classic cluster, 2 retries. |
| 2 | `ri_master_list_bronze_validate` | Business rules on bronze's active rows, plus the SCD2 history invariants |
| 3 | `ri_master_list_silver` | Overwrites `standalone_silver.ri_master_list` with bronze's active rows, every column unchanged and in bronze's order. Serverless. |
| 4 | `ri_master_list_silver_validate` | 11 parity checks against bronze's active rows (listed below) |
| 5 | `ri_master_list_publish` | Overwrites `ri_lakehouse.ri_master_list` from silver, then checks the target against the source |

Each step runs only if the one before it succeeded. A failure anywhere leaves `ri_lakehouse.ri_master_list` holding its last validated copy: stale, never partial or unvalidated.

The 11 silver checks: both tables exist; the schema matches by name, type and position; silver is not empty; every row is active; every expiration is the sentinel; `_SURROGATE_KEY` and `_BUSINESS_KEY` are unique; no row has all 8 identity columns null (a WARN, not a FAIL, because bronze still hashes such a row to a valid key); the row count equals bronze active; and every column matches via `exceptAll` in both directions.

Publish's own check after writing compares schema, row count and every row. It does not roll back on a mismatch, because a mismatch straight after an atomic overwrite needs a person to look. Its error names the pre-publish Delta version, and recovery is `RESTORE TABLE pen_research_infrastructure_insights_prd.ri_lakehouse.ri_master_list TO VERSION AS OF <n>`.

Verified on the first two runs after the cutover:

| Run | Trigger | Tasks | Silver validate | Published | `ri_lakehouse` version |
|---|---|---|---|---|---|
| `750702859638640` | manual, 2026-09-14 16:09 | 13/13 SUCCESS | 11 passed | 117 rows | 17 |
| `1048366854596689` | scheduled, 2026-09-15 00:23 | 13/13 SUCCESS | 11 passed | 117 rows | 18 |

In both runs publish started after silver validate ended, and each run added exactly one Delta version. Checked 2026-09-15: bronze active, silver and `ri_lakehouse` each hold 117 rows, silver and `ri_lakehouse` match on every column in both directions, and the schema is unchanged at 24 columns with `INDEX` (`LONG`) first. The Power BI refreshes after the cutover were confirmed successful by the table owner on 2026-09-15.

Before the job changed, the new notebooks were tested outside it: run `742853312545443` ran all five new tasks with publish pointed at a scratch table, and run `279356053570772` ran two tasks built to fail (a schema mismatch and a missing publish source), which both failed as intended.

## Column reference

All 18 business columns, present on both `ri_master_list` (active rows) and `ri_master_list_bronze` (full history). Both tables also carry the 5 `_`-prefixed SCD2 metadata columns (on `ri_master_list` they're all `Y`/sentinel-expiration, since only active rows are present) **and a physical `INDEX` column (`LONG`, first in column order) that the pipeline stopped maintaining on 2026-08-25 but never dropped from the Delta schema** — 24 columns in total on both tables, verified live 2026-09-11. Every current row still carries its pre-2026-08-25 value (`0`–`116` on the 117 active rows, `0`–`120` across all 207 bronze rows), because no row-version has been opened since 2026-08-21. Treat `INDEX` as a dead column: present, populated with stale values, excluded from the change-comparison, and `NULL` on any row written from now on. Reproduced in full from the source doc (`docs/2026-08-19-ri-master-list-reference.md`) — the prose above summarises the grain and join-key story; this table is the row-level detail that summary doesn't repeat. The null counts are the source doc's 2026-08-25 snapshot and have not been re-run since; `PURE_ORGANISATION_ID` was null on every row:

| Column | Type | Nulls (of 117, as of 2026-08-25) | Description |
|---|---|---|---|
| `CAPABILITY_CODE` | string | 0 | Short code for the platform/capability, e.g. `FLOW`, `MARP`, `MERC`. Forms a validated 1:1 pair with `CAPABILITY_NAME`. Always the prefix of `NODE_ID` where `NODE_ID` is populated. |
| `CAPABILITY_NAME` | string | 0 | Full display name of the capability, e.g. `FLOWCORE`. |
| `NODE_ID` | string | 0 | Sub-location code within a capability, e.g. `FLOW-ARA`. Forms a validated 1:1 pair with `NODE_NAME` (where populated). Not unique per row — repeats when a node has multiple cost centres. |
| `NODE_NAME` | string | 1 | Full display name of the node, e.g. `FLOWCORE - ARA`. |
| `COST_CENTRE_NAME` | string | 55 | SAP cost centre display name. |
| `COST_CENTRE` | string | 52 | SAP cost centre code, e.g. `M50011`. Can repeat across rows for the same node (multi-funded node) or, rarely, be shared unexpectedly by two different capability codes (`P04001` appears under both `MPMP` and `MRNA`). |
| `FUND_ID` | string | 113 | Semicolon-delimited SAP fund ID(s). Multi-value example: `3275208;3275209`. |
| `CAPABILITY_ISO` | string | 0 | `YES`/`NO` — whether the capability is ISO-accredited. Value set enforced by the test notebook. |
| `CAPABILITY_TYPE` | string | 0 | `PLATFORM`/`NON-PLATFORM`. Value set enforced by the test notebook. `NON-PLATFORM` rows are faculties/schools/institutes and other groupings used for filtering/RLS, not run as billable research infrastructure. |
| `CAPABILITY_GOVERNANCE` | string | 0 | Owning faculty/division code, e.g. `MNHS`, `CENTRAL`, `ENG`. Restricted to a fixed 14-value approved list enforced by the test notebook — a genuinely new faculty/division requires updating the notebook's `APPROVED_GOVERNANCE_VALUES` set, not just the sheet. |
| `SURVEY_CAPABILITY_ID` | string | 28 | ID used to match this capability/node in the university's research infrastructure survey tool. |
| `PURE_ORGANISATION_ID` | string | 117 (100%) | Reserved for a Pure organisation-unit ID. Always null in current data — either not yet populated for any row, or superseded by `PURE_FACILITY_ID`. |
| `PURE_FACILITY_NAME` | string | 50 | Matching facility name in Pure (Monash's research information system). |
| `PURE_FACILITY_ID` | int | 41 | Matching facility ID in Pure. Tied to the capability, not the node — all nodes under one capability typically share the same `PURE_FACILITY_ID` (e.g. all 3 `FLOW-*` rows share `7526788`). |
| `ILAB_CAPABILITY_ID` | string | 44 | Matching capability/core ID in iLab. Also capability-level, not node-level (all `MARP-*` rows share `ILAB_CAPABILITY_ID = MARP`) — iLab charges/services/labs data joins to this table at the capability grain, not the node/cost-centre grain. |
| `ILAB_CORE_NAME` | string | 43 | Matching core name in iLab — can differ from `CAPABILITY_NAME`/`NODE_NAME` (e.g. capability `FLOWCORE`, node `FLOWCORE - ARA`, but `ILAB_CORE_NAME = FLOWCORE ALFRED RESEARCH ALLIANCE`). |
| `RLS_FACILITY_GROUP` | string | 23 | Azure AD group name gating fine-grained (facility/node-level) Power BI report access. Pattern: `eSol-PowerBI-{CAPABILITY_GOVERNANCE}-{CAPABILITY_CODE}`, occasionally overridden per-node (e.g. `MERC-HELIX`'s row uses `eSol-PowerBI-CENTRAL-HELIX` instead of the parent `eSol-PowerBI-CENTRAL-MERC`). Blank for some `NON-PLATFORM` rows that don't yet have a dedicated group. |
| `RLS_FACULTY_GROUP` | string | 23 | Azure AD group name gating broader (faculty/division-admin) Power BI report access. Always exactly `eSol-PowerBI-{CAPABILITY_GOVERNANCE}-ADMIN` — one group per governance value. |

## Why it's documented as SCD Type 2 (migrated 2026-08-20)

Before this migration, edits/deletions made in the source Google Sheet were silently lost on every nightly rebuild — a straight overwrite pattern. [[SCD Type 2 Convention (Monash house style)|The SCD2 migration]] (explicitly noted as "the same pattern as `lakehouse_bim_prd.external_organisation.external_organisation`" — i.e. following an existing Monash convention, not inventing a new one) fixes that: the bronze table now retains every version, and `_BUSINESS_KEY` (a SHA-256 hash of 8 identity columns) determines whether an incoming row is a genuine identity change vs. an in-place update.

The physical table holding that history has been renamed twice on the way to its current shape:

1. **2026-08-20 – 2026-08-31**: `ri_master_list_history` (full history) + `ri_master_list` as a thin compatibility view (`WHERE _ROW_ACTIVE_FLAG = 'Y'`) — all 7 downstream reports needed **zero changes** to keep working.
2. **2026-09-02, first pass**: collapsed into a single `ri_master_list` table (view dropped, history table renamed in place), matching the single-table convention used for `ri_external_institutes` — but this meant reports would need to add their own `_ROW_ACTIVE_FLAG = 'Y'` filter.
3. **2026-09-02, same day, second pass**: split again — full history moved to `standalone_bronze.ri_master_list_bronze` (seeded from the (2) table's 207 rows via `CREATE TABLE ... AS SELECT *`, no history lost), and `ri_lakehouse.ri_master_list` became a plain overwrite of bronze's active rows. This restores the "reports see only active rows, no filter needed" property from (1), but as a physical overwrite rather than a live view, and puts the true history table in the standard `standalone_bronze` schema per [[Databricks Conventions]] rather than a bespoke `ri_lakehouse`-schema history table.

## Deliberate simplifications, documented as such (not oversights)

- **`INDEX` was a deliberate simplification until it was removed.** Before 2026-08-25 `INDEX` was regenerated every rebuild by re-sorting the whole sheet and was *not* excluded from the SCD2 change-comparison — so adding or removing any row could shift `INDEX` for many unrelated rows, closing and reopening their versions purely because their `INDEX` value moved. The source doc called this "a deliberate simplification, not an oversight". As of 2026-08-25 `INDEX` is dropped on import (a QA sorting aid in the sheet only) and is no longer part of the change-comparison, so the spurious churn no longer occurs. The source doc says the column "no longer appears" in the table; live on 2026-09-11 it still does, on both tables, with every existing row carrying its old value (see [[#Column reference]]) — dropping a column from the import does not drop it from a Delta table. Rows written from now on will carry `NULL` there.
- **Ad hoc runs must use the classic job cluster, not serverless** — a bare serverless one-off submission "has been observed to fail reliably on `ConnectionResetError`" reaching the Google Sheets API from this workspace. A specific, tested operational constraint, not a style preference.

## Known validation gaps, self-documented in the source

The doc lists these explicitly rather than leaving them implicit:
- Several `ri_master_list_bronze_validate` cells (renamed from `test_ri_master_list`) are wrapped in `%skip` — leftover ad hoc scratch queries, not active validation logic.
- Nothing validates `COST_CENTRE` format or cross-checks it against SAP; a `RLS_FACILITY_GROUP`/`RLS_FACULTY_GROUP` naming typo would silently break row-level security for that platform without failing the nightly job.
- Nothing validates that `_BUSINESS_KEY`'s 8 identity columns stay collectively unique — two genuinely different rows sharing all 8 would silently merge into one `_BUSINESS_KEY` and be treated as the same entity across every future rebuild.
- `COST_CENTRE` `P04001` is shared by two different capability codes (`MPMP` and `MRNA`) — flagged in the doc as "worth double-checking if you encounter this" rather than resolved.

## Handover to Data Engineering (added 2026-08-28)

The reference doc now opens with a **Handover to Data Engineering** section, added after connecting to the workspace and cross-checking the doc against the live `ri_master_list`/`ri_master_list_history` notebooks, job config, and Unity Catalog grants directly — everything in it was verified live, not just read off the doc:

- **Ownership and access gap** — the job (`163544004016522`, renamed "01_standalone_tables" 2026-09-02, was "Daily run - ri_master_list"), both notebooks (moved out of their own `ri_master_list/` folder into `ri_standalone/` and renamed `ri_master_list_bronze`/`ri_master_list_bronze_validate` the same day), and `ALL_PRIVILEGES` on the `ri_lakehouse` schema all sit on one individual (`milinda.abayawardana@monash.edu`), not a service principal or team group. The workspace `admins` group only has inherited `CAN_MANAGE` on the job; the `Lakehouse-PEN-Research-Infrastructure-Insights-users` group only has catalog-level `BROWSE`/`CREATE_SCHEMA`/`USE_CATALOG` (discovery, not write). This is a real single-point-of-failure risk for the handover, not a documentation gap — flagged with a concrete recommendation (move to a shared workspace path + service principal/group ownership, or explicitly grant DE the needed job/schema permissions) before the current owner is unavailable.
- **Credentials** — Google Sheets read auth is a service account (`pen-rii-gsheet-ingestion-gcpsa@moonlit-creek-488704-t6.iam.gserviceaccount.com`), credentials in secret scope `pen-rii-gsheet-credentials` / key `service-account`. Nothing else needs a personal credential, but the job itself runs *as* the individual owner (`run_as_user_name`), which is part of the same ownership gap.
- **Runbook** — where to look when the nightly job fails: job logs + `dbfs:/cluster-logs/job/Research-Infrastructure-Insights-Interactive-Cluster`; a `ri_master_list_bronze_validate` failure (renamed from `test_ri_master_list` 2026-09-02 — **the task key was renamed to match too**, correcting what this note originally said) almost always means fix the sheet row, not the notebook (unless it's a new, approved controlled-vocabulary value); a `ConnectionResetError` means someone ran the build notebook on serverless instead of the classic cluster spec — a known, reproducible failure mode, not an outage.
- **Resolved by 2026-09-03** — the stale-path issue above did fail the job as predicted (the 2026-09-02 15:05/14:32 runs both failed with `Unable to access the notebook`); corrected the same day, and every scheduled run since has found valid paths. Task keys were renamed to match at the same time (`ri_master_list_bronze`/`ri_master_list_bronze_validate`, `ri_external_institutes_bronze`/`ri_external_institutes_bronze_validate` — not `validate_ri_external_institutes` as this note previously had it). A third, undocumented task pair, `remap_tables_bronze`/`remap_tables_bronze_validate` (see [[Standalone Remap Tables Reference]]), was also added to [[Job 01_standalone_tables (id 163544004016522)|this job]] sometime between 2026-09-02 and 2026-09-04. All confirmed live 2026-09-09.
- **Diagnosed 2026-09-11 — the intermittent `Workload failed, see run output for details` failures are all the Google Sheets read.** Task run output pulled for every failed scheduled run since 2026-09-02; each one dies in `GoogleSheetReader._read_sheets()` before any table is touched, on one of two errors:

  | Scheduled run (00:23 Sydney) | Failed task(s) | Error |
  |---|---|---|
  | 2026-09-04 | `ri_master_list_bronze`, `ri_external_institutes_bronze`, `remap_tables_bronze` — all three | `OSError: [Errno 101] Network is unreachable` |
  | 2026-09-08 | `ri_master_list_bronze` | `HttpError 503` from `sheets.googleapis.com/v4/spreadsheets/17EdIr…` |
  | 2026-09-09 | `ri_external_institutes_bronze` | `HttpError 503` from `sheets.googleapis.com/v4/spreadsheets/1G3ALz…` |
  | 2026-09-11 (run `963844459954913`) | `ri_master_list_bronze`, `ri_external_institutes_bronze` (`remap_tables_bronze` succeeded) | `OSError: [Errno 101] Network is unreachable` |

  So this is the same failure family as the serverless `ConnectionResetError` above — egress from this workspace to the Google Sheets API is unreliable, on the classic cluster too — not a data or notebook fault. This is true **only for a failure during the Sheets read itself** — every failure diagnosed above died in `GoogleSheetReader._read_sheets()`, before the merge, so those runs leave both tables exactly as the previous successful run left them; the risk is staleness, not corruption. A failure **between** the close-`MERGE` and the `append` is a different case: it would leave the just-closed row-versions with no active replacement inserted yet, until the next successful run re-inserts them — with no duplicates created, since the insert step is an exact-match anti-join against currently-active rows. Every failure before 2026-09-11 was manually rerun the same day and succeeded.

  **Retries added 2026-09-12** — the fix this note called "the obvious fix to propose to Data Engineering" is now in place: `ri_master_list_bronze` carries `max_retries: 2` / `min_retry_interval_millis: 300000` in job `163544004016522` (`ri_external_institutes_bronze` got the same policy the same day — see [[ri_external_institutes SCD2 Migration]]). Two scheduled runs since have gone 8/8 `TERMINATED SUCCESS` on attempt 0 — `87035366018550` (2026-09-13 00:23) and `859940067644810` (2026-09-14 00:23) — so the job has kept succeeding, but neither run needed a retry: the policy has **not yet been exercised** against a real `Network is unreachable` failure, and whether it actually recovers one when the next occurs is still open. The two runs after the 2026-09-14 cutover (`750702859638640`, `1048366854596689`) also ran every task on attempt 0, so no production run has needed a retry as of 2026-09-15. The egress-failure diagnosis above is unchanged by this — the retries address the symptom the job now handles automatically, not the underlying network instability.

  **Retry mechanism tested 2026-09-15, outside production.** A temporary job (`369224192338585`, since deleted) copied the production cluster spec and this task's retry policy exactly. Its task raised the same `OSError: [Errno 101] Network is unreachable` on its first two attempts and succeeded on the third; a second task depended on it. No production table was touched.

  | Probe run | Attempt | Start (AEST) | Cluster setup | Result |
  |---|---|---|---|---|
  | `1051081341665788` | 0 | 11:55:55 | 111s | FAILED (simulated `Errno 101`) |
  | | 1 | 12:00:57 | 1s | FAILED (simulated `Errno 101`) |
  | | 2 | 12:05:58 | 1s | SUCCESS |

  The dependent task then ran and succeeded, and the run ended `TERMINATED SUCCESS`: a task that recovers on a retry does not block the tasks after it. Three things this established:

  - **The 5-minute interval runs from the start of the failed attempt, not its end, and cluster start-up counts toward it.** In the table above attempt 1 started 302s after attempt 0 started, but only 167s after it ended. In an earlier probe run (`993057479229065`) the cluster took 412s to start, so attempt 1 began 1 second after attempt 0 ended. On a cold nightly run, then, the **first retry fires almost immediately** after a Sheets failure, and only the second retry waits a real 5 minutes. The whole policy buys roughly 5 minutes of recovery time, not 10.
  - **Every attempt reuses the same job cluster.** Setup on attempts 1 and 2 was 1 second.
  - **What it does not prove:** whether a real egress outage clears within that window. The 2026-09-04 and 2026-09-11 failures were never timed, so that stays open until a real failure is retried.

  UC volumes reject append mode on an existing file (`OSError: [Errno 29] Illegal seek`): the first probe run failed its retries on that, before the marker write was changed to rewrite the whole file.

  > [!note] Partly resolved 2026-09-15
  > `ri_lakehouse.ri_master_list` reflects run `1048366854596689` (2026-09-15 00:23): Delta version 18, confirmed live that day to equal `standalone_silver.ri_master_list` on every column. That makes the 2026-09-11 failure irrelevant to this table's current state.

> [!note] The 2026-09-11 failure was never rerun, and cost nothing (checked 2026-09-15)
> No run of job `163544004016522` and no one-off submitted run started between the failure (`963844459954913`, 2026-09-11 00:23) and the next scheduled run, `349115274460646` at 2026-09-12 00:23, which succeeded on every task. That run was the recovery, about 24 hours later. It is the only failure in the diagnosis table above that was not rerun the same day.
>
> No data was lost:
> - **Bronze was unchanged.** Neither `standalone_bronze.ri_master_list_bronze` nor `standalone_bronze.ri_external_institutes` has had a Delta commit since 2026-09-02: the first is still at version 0, the second at version 8. The sheets changed nothing in that time, so the missed run had nothing to merge.
> - **The published copy was a day stale.** `ri_lakehouse.ri_master_list` went from version 12 (the 2026-09-10 run) to version 13 (the 2026-09-12 run), with no version from 2026-09-11. For that one day it held the previous run's copy, and that copy was identical to what the failed run would have written.
> - **`ri_lakehouse.ri_external_institutes` was not involved.** Its last write is still 2026-08-29 (version 27), because it has no scheduled writer (see [[Databricks Migration State]]).

## See also

- [[Databricks Conventions]] — the SCD2 pattern here generalised into a standing convention for `standalone_bronze`/`standalone_silver` (2026-08-31)
- `ri_ilab/docs/2026-08-19-ri-master-list-reference.md` — the full reference doc this note summarises, kept in the repo because graphify indexes it. Since 2026-09-11 it opens with a callout naming **this note** as the maintained copy and warning that its notebook, job and task names predate the 2026-09-02 renames — so it is the historical record, and this note is where the current names live
- [[SCD Type 2 Convention (Monash house style)]], [[_BUSINESS_KEY SHA-256 of 8 identity columns]]
- [[ri_master_list build notebook]], [[Job 01_standalone_tables (id 163544004016522)]], [[Google Sheet 'Master record' Tab]], [[standalone_bronze.ri_master_list_bronze]], `ri_master_list Master Dimensional Table` *(no node since export `1ac3015`)*, [[test_ri_master_list Validation Rules (6 invariants)]]
- [[Single-Owner Ownership and Access Gap]], [[pen-rii-gsheet-credentials Service Account]]
- `_COMMUNITY_RI Master Bronze Architecture` *(no community since export `1ac3015`)*
- The `RI PBI Production` vault's [[Projects/RI PBI Production/Reference/Shared Conventions|Shared Conventions]] and [[Projects/RI PBI Production/Repos/iLab Utilisation/iLab Utilisation|iLab Utilisation]] notes — the downstream Power BI side of this same table
- [[Overview|Databricks]] — the catalog this table lives in
- **Derived layer — the consuming side in `ri_pbi_production`** (`graphify/`, never hand-edited): [[dim_ri_master_list]], [[dim_ri_master_list_1]], [[dim_ri_master_list_2]], [[dim_ri_master_list_3]], [[dim_ri_master_list_4]], [[dim_facility_master_list]], [[DIM_FACILITY_2]], [[Capability Master List]], [[ri_master_list_bronze_validate Notebook]]
- **Derived layer — the Power BI M queries that read this table** (`graphify/`, never hand-edited): [[pen_research_infrastructure_insights_prd.ri_lakehouse.ri_master_list]], [[ri_master_list]], [[ri_master_list_1]], [[ri_master_list_2]], [[ri_lakehouse_ri_master_list]], [[ri_lakehouse_ri_master_list_1]], [[ri_lakehouse_ri_master_list_2]], [[ri_lakehouse_ri_master_list_3]]
