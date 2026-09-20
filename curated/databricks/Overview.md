# Databricks

The Monash research-infrastructure Databricks estate: workspace `adb-3993465269917932.12.azuredatabricks.net`, catalog **`pen_research_infrastructure_insights_prd`**. This project holds the standing conventions, the table-level references, and the survey of what is actually wired up — the knowledge that belongs to the *platform*, not to any one thing that reads or writes it.

Two projects sit either side of it: [[Projects/RI iLab/Overview|RI iLab]] is the local pandas ETL that still produces most of the fact data by hand, and [[Projects/RI PBI Production/Overview|RI PBI Production]] is the seven Power BI reports on the consuming end.

> [!warning] Point-in-time figures live in one note
> Row counts, freshness, job status and schedules are verified snapshots, not standing facts. They live in [[Databricks Migration State]] (last verified live in full **2026-09-06**) rather than being restated here. On **2026-09-11** a partial live re-check covered the three job schedules below, the `preprocess_ilab` pipeline, the nine iLab historical/bronze tables and both `ri_master_list` tables — see [[Historical Services Bronze Pipeline]] and [[ri_master_list SCD2 Reference]]. Re-verify against the workspace before relying on anything else.

## The three planes

Work has landed in the catalog in three places, built at different times, **not yet connected to each other**:

| Plane | Schemas | Scheduled? | Feeds Power BI? |
|---|---|---|---|
| **Ingest + bronze** — the intended replacement for the `ri_ilab` repo | `new_test`, `ilab_bronze` | ingest monthly; bronze **no** | **No** |
| **Standalone** — Google-Sheet reference data | `standalone_bronze`, `standalone_silver`, `standalone_gold` | yes, nightly | Yes, via `ri_lakehouse.ri_master_list` |
| **Serving** — what the reports actually query | `ri_ilab`, `ilab_3y`, `ri_lakehouse`, `survey`, `ri_research_dashboard`, `dim_env` | derived tables yes; base tables **no** | Yes — all of it |
| **Pure bronze/silver** — re-implementation of the `ri_non_ilab` report's Pure tables | `pure_bronze`, `pure_silver` (`pure_gold` reserved) | no, run by hand | **Not yet in the Service**: `pure_silver` feeds the unpublished [[Projects/RI PBI Production/Repos/Non-iLab Utilisation/Non-iLab Utilisation|Non-iLab Utilisation]]; the live legacy report is still served by `ri_lakehouse_prod` |

The standalone plane is the only one wired end to end. The serving plane's base tables have no scheduled writer — they come from the `ri_ilab` repo, run by hand. See [[Databricks Migration State]] for the full survey and its five named gaps.

## Standing conventions

[[Databricks Conventions]] is the single source of truth for how tables and notebooks in this catalog are built: medallion layout (one schema per layer, same table name across layers), `UPPER_SNAKE_CASE` columns everywhere, the five-column SCD Type 2 convention for bronze, one build notebook plus one matching validate notebook per table, and where reference data does and doesn't get inlined.

## Tables

| Note | Covers | Source of truth |
|---|---|---|
| [[ri_master_list SCD2 Reference]] | `standalone_bronze.ri_master_list_bronze` (full history) → `standalone_silver.ri_master_list` → `ri_lakehouse.ri_master_list` (active rows, published only after silver validates) | Google Sheet |
| [[ri_external_institutes SCD2 Migration]] | `standalone_bronze.ri_external_institutes` — the SAP client-number join key | Google Sheet |
| [[Standalone Remap Tables Reference]] | `standalone_bronze.remap_core_name` / `remap_customer_institute` / `remap_customer_lab`, and their `standalone_silver` copies | Google Sheet (three tabs) |

`ri_master_list` is the master dimensional table underpinning **all 7** Power BI reports, which makes it the most load-bearing table in the catalog and the one whose single-owner ownership gap matters most.

## Pipelines

[[Historical Services Bronze Pipeline]] — the Databricks-native ingestion of historical iLab exports back to Nov 2022, unioned with the live SFTP feed and deduplicated into `ilab_bronze.ilab_services` / `ilab_labs` / `ilab_members` / `ilab_charges` (the tables carry no `_bronze` suffix; the notebooks do). Documented, correct, rebuilt by hand, and currently unconsumed.

[[Pure Bronze Pipeline]] — 15 notebooks re-creating the Pure-derived tables the old `ri_non_ilab` Power BI report reads from `ri_lakehouse`, ported from the `ri_lakehouse_prod` SQL notebook's PURE section into native `pure_bronze` builds. First run 2026-09-17, all 15 tables built, run by hand, not yet scheduled, report not yet cut over.

[[Pure Silver Pipeline]] — the cleaned, conformed layer built from `pure_bronze`: the same 15 tables, 8 with ported Power Query preprocess logic and 7 pass-throughs, plus a shared `%run` helper notebook (`pure_silver_common`) — the catalog's first shared-helper pattern. First run 2026-09-18, all 15 build and validate notebooks passed, run by hand, not yet scheduled.

[[Projects/RI PBI Production/Repos/Non-iLab Utilisation/Non-iLab Utilisation|Non-iLab Utilisation]] — the first Power BI report on `pure_silver`: `ri_pbi_non_ilab_utilisation`, a new build of the legacy `ri_non_ilab` report's four visible pages from 8 silver tables plus an unrelated `dim_ri_master_list`, with no RLS and no `facility_id` breakdown. Built 2026-09-18, not yet published; the legacy report still reads `ri_lakehouse`.

## Scheduled jobs

| Job | Id | Schedule | Builds |
|---|---|---|---|
| `01_standalone_tables` | `163544004016522` | nightly 00:23 Australia/Sydney | the standalone bronze/validate/silver chains, and the gated `ri_master_list` publish (13 tasks since 2026-09-14) |
| `Daily run - serverless` | `234277055527586` | daily 01:00 | `ilab_3y` and `ri_lakehouse` derived tables |
| `ingest_pipeline` job | `93376113759500` | monthly, 5th at 02:00 | the five `new_test` streaming tables (pipeline `d2391db7-2e23-48f2-8722-597db5e864b9`) |

All three schedules confirmed live 2026-09-11, all unpaused, all running as the individual owner. `Daily run - serverless` has six tasks: `ilab_post_ingestion`, `Create_dim_services`, `ri_lakehouse_prod`, `Get_and_filter_finance_forecast_budget_actuals`, `bim_env`, `dim_env`. `01_standalone_tables` fails intermittently on Google Sheets egress. Since 2026-09-12 its bronze builds retry twice. No production run through 2026-09-15 has needed a retry, but a probe job confirmed that day that the policy recovers a failed task and lets downstream tasks run. On a cold cluster the first retry fires almost immediately, because the 5-minute interval counts from the start of the failed attempt. Diagnosed in [[ri_master_list SCD2 Reference]].

## See also

- [[Projects/RI iLab/Overview|RI iLab]] — the pandas ETL upstream; its `pen/` package is the manual upload step into the serving schemas
- [[Projects/RI PBI Production/Overview|RI PBI Production]] — the seven reports downstream
- [[Projects/RI iLab/Initiatives/iLab Silver Layer Migration|iLab Silver Layer Migration]] — the open initiative to rebuild the repo's cleaning logic as a Databricks silver layer
- [[Pure Silver Pipeline]] — `pure_bronze`'s silver layer, and the catalog's first shared-`%run`-helper notebook pattern
- **Derived layer** (`graphify/`, never hand-edited): `_COMMUNITY_RI Master Bronze Architecture` *(no community since export `1ac3015`)*, `_COMMUNITY_Historical Services Pipeline` *(no community since export `1ac3015`)*, [[Job 01_standalone_tables (id 163544004016522)]], `ingest_pipeline (raw SFTP ingestion)` *(no node since export `1ac3015`)*, [[preprocess_ilab Lakeflow pipeline (adjacent)]], [[standalone_bronze.ri_master_list_bronze]], [[pen_research_infrastructure_insights_prd.ri_lakehouse.ri_master_list]], `Databricks Table Names and SQL Schemas` *(no node since export `1ac3015`)*
