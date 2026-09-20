# iLab Silver Layer Migration

Build a Databricks-native silver layer — `ilab_charges_silver`, `ilab_labs_silver`, `ilab_members_silver`, `ilab_services_silver` — that reproduces, in Spark against `ilab_bronze`, the cleaning logic today living in the `ri_ilab` repo's pandas `preprocess.py`/`process.py` modules (see [[iLab Domain Pipelines]]). As of **2026-09-14**, this is still planning-stage only: a detailed prompt exists, but no spec or plan has been written and no notebook has been built. Checked live that day, no `ilab_*_silver` table exists. `standalone_silver` then held only `ri_external_institutes`; since the 2026-09-14 cutover it also holds `ri_master_list` and the three `remap_*` tables (see the precedent row below). `Ledger/` holds no migration-asset notes yet.

The full prompt — goal, scope rule, every decision and trap below with its supporting reasoning, and the exact deliverable checklist — is `docs/superpowers/prompts/2026-09-06-ilab-silver-layer-prompt.md` in the `ri_ilab` repo, meant to be pasted into a future `/brainstorming` → `/writing-plans` session. This note is the durable summary; read the prompt itself before starting that work.

The prompt carries its own regression check, dated **2026-09-09**: every code claim it makes (transform order, `fix_customer_cols()` semantics, the labs/members two-stage dedup, `identify_latest_data_rows()`'s positional flag, the services `KEEP_COLS`/remap/dedup/`service_rls` chain, the `REMAP_*_DICT` row counts) was re-verified against the repo at that date. Three commits had landed since it was written (`3529364`, `c533ab2`, `5e0ef32`); none touched code the prompt depends on. Its one stale reference — `docs/databricks-conventions.md`, deleted 2026-09-08 — now points at [[Projects/Databricks/Reference/Databricks Conventions|Databricks Conventions]] here instead.

> [!warning] The bronze tables are not named `ilab_*_bronze`
> The prompt's bronze-inputs table uses the names that actually exist as of 2026-09-09 — `ilab_bronze.ilab_charges` (52 columns), `ilab_bronze.ilab_labs` (11), `ilab_bronze.ilab_members` (12), `ilab_bronze.ilab_services` (21) — **without** a `_bronze` suffix, even though the notebooks that write them are still named `ilab_*_bronze`. Its decision 1 still quotes the suffixed `ilab_bronze.ilab_charges_bronze` from an earlier draft; read the inputs table, not the decision text, for the real names. See [[Projects/Databricks/Pipelines/Historical Services Bronze Pipeline|Historical Services Bronze Pipeline]].

## Scope

**In**: row-level transforms, the `REMAP_*` value mappings, dedup/latest-row selection (including within-table window functions) — one bronze table in, one silver table out, per table.

**Out, explicitly**: any join — not to the other three silver tables, not to reference/dimension tables, not to anything in `lakehouse_bim_prd`/`ri_lakehouse`; the gold/serving layer; and everything the two `/ilab/dev/` notebooks do (`ilab_post_ingestion`'s staff/researcher-ID join, `dim_services`'s three-way join) — those stay downstream, unaddressed by this initiative.

## Decisions still open

Not yet answered — a future plan needs to surface a recommendation and trade-off for each, per the source prompt:

| Decision | The tension |
|---|---|
| Table/schema naming | `standalone_*` convention keeps the same name across layers ([[Projects/Databricks/Reference/Databricks Conventions|Databricks Conventions]]); iLab bronze is schema-qualified (`ilab_bronze.ilab_charges`, no suffix — see the callout above) while the requested silver names are suffixed (`ilab_charges_silver`), so the two halves of the iLab line already disagree with each other as well as with the precedent |
| Column naming | Conventions demand `UPPER_SNAKE_CASE`; bronze is lower_snake_case, matching the repo's own `fix_df()` |
| SCD2 passthrough | Conventions say silver carries bronze's 5 SCD2 columns through; `ilab_bronze` has none — it's a plain deduplicated union |
| Remap application | The `REMAP_*_DICT` dicts also exist as governed SCD2 tables in `standalone_bronze` ([[Projects/Databricks/Tables/Standalone Remap Tables Reference|Standalone Remap Tables Reference]]) — reading them would be a join, which the scope rule forbids, so the default is inlining, which drifts from the governed tables |
| Parity oracle | How to prove silver matches today's pandas output, given the comparison tables (`ri_ilab.ilab_charges` etc.) were last written from a different input window than bronze covers |

## What changed since the prompt (as of 2026-09-14)

The prompt was last regression-checked on 2026-09-09. Since then the bronze inputs and the platform around them have moved. None of these changes answers an open decision, but several change what a plan has to account for:

| Change | Date | Why it matters here |
|---|---|---|
| **Bronze is orchestrated.** Job `ilab_bronze_tables` (`916154989512260`) rebuilds all four `ilab_bronze` tables after every successful `ingest_pipeline` run (monthly, on the 5th). | 2026-09-12 | Silver can hang off bronze in a job instead of being run by hand. Each bronze notebook does `DROP TABLE IF EXISTS` then `saveAsTable`, so a failed rebuild leaves **no table**; a silver task must depend on bronze succeeding, not run on its own schedule. |
| **Charges bronze rebuilt** after the missing `multiLine` CSV option was fixed. It went from 1,492,840 to 1,441,141 rows across 10 source files; null `charge_id` and `creation_date` both fell to 0; and 105 hidden charges were recovered. | 2026-09-12 | Any parity baseline or row count for charges taken before this date is void. That bears on the **Parity oracle** decision. |
| **Bronze shapes re-verified live:** `ilab_charges` 52 columns / 1,441,141 rows; `ilab_labs` 11 / 6,758; `ilab_members` 12 / 149,330; `ilab_services` 21 / 242,589. | 2026-09-14 | The column counts match the prompt's inputs table; the prompt's row counts should not be trusted. `ilab_services` still has no `created_at`, so the blocker below stands. |
| **Month coverage checked.** Every month from 2022-11 to 2026-09 is in bronze for services, labs and members, except **2025-12 and 2026-02**, which were never delivered and are permanently absent. July 2026 reached bronze only through the historical Parquet volume. The ingest readers skip `.csv.gz` files deliberately. | 2026-09-14 | Snapshot-based silver logic (latest row, month-over-month) will see those two holes; they are data, not a bug to fix in silver. The monthly landing check is recorded in Historical Services Bronze Pipeline (linked below). |
| **`members_funds` is excluded from the pipeline for now.** It has no bronze table, no historical volume, and is missing 2026-07. | 2026-09-14 | Already outside this initiative's four tables; stated so a plan does not add a fifth. |
| **A standalone silver precedent now exists, for all four standalone tables.** `standalone_silver.ri_external_institutes` (since 2026-09-12), `ri_master_list` and the three `remap_*` tables (since 2026-09-14) are rebuilt nightly inside `01_standalone_tables`. In each chain a serverless silver task runs after bronze validate succeeds, then a `*_silver_validate` notebook, and the job emails on failure. Every validate is a **parity check against bronze**, in two shapes: `ri_external_institutes`, whose silver transforms columns, checks row count and surrogate-key set in both directions plus non-empty and lossless-cast checks; the pass-through tables compare every column with `exceptAll`. `ri_master_list` also has a **publish gate**: `ri_master_list_publish` writes `ri_lakehouse.ri_master_list` only after its silver validate passes. | 2026-09-12, extended 2026-09-14 | The closest worked template for job shape, validation, and gating what Power BI reads. It does **not** settle the Parity oracle decision: it proves silver matches *bronze*, while this initiative must prove silver matches the *pandas output*. It also relies on bronze's SCD2 `_SURROGATE_KEY`, which `ilab_bronze` lacks (see **SCD2 passthrough** above). See ri_external_institutes SCD2 Migration and Databricks Conventions (linked below). |

Sources for the table: [[Projects/Databricks/Pipelines/Historical Services Bronze Pipeline|Historical Services Bronze Pipeline]] (bronze orchestration, the charges rebuild, month coverage and `members_funds`), [[Projects/Databricks/Tables/ri_external_institutes SCD2 Migration|ri_external_institutes SCD2 Migration]] and [[Projects/Databricks/Reference/Databricks Conventions|Databricks Conventions]] (the standalone silver precedent).

## Known traps

Verified against the current repo by the prompt's own regression check (2026-09-09) — all still accurate:

- **`created_at` doesn't exist in `ilab_bronze.ilab_services`** — renamed to `startdate` during the historical-volume build (see [[Projects/Databricks/Pipelines/Historical Services Bronze Pipeline|Historical Services Bronze Pipeline]]), conflated with the SFTP files' own `startdate`. Recoverable only by splitting on the historical rows' synthetic `00000000_` `file_name` prefix.
- **`identify_latest_data_rows()` is positional, not semantic** — flags `file_name == df["file_name"][0]` after a descending sort. A Spark port must express the *intent* (most recent `file_name`) as a window/`max()` expression, not transliterate the indexing.
- **`fix_customer_cols()` has no direct Spark analogue** — an order-dependent `df.update()` against a self-derived lookup, called twice in sequence (institute, then department) with a null-fill in between.
- **Charges' transform order is load-bearing**: dedup → cancellation rule → histology nodes → remap → `fix_customer_cols` (institute) → external-customer fill → `fix_customer_cols` (department) → faculty split.
- **The same decimal-string cast failure shows up twice, independently**: labs' `pre_approval_amount` on the Databricks side ([[Projects/Databricks/Pipelines/Historical Services Bronze Pipeline|Historical Services Bronze Pipeline]], found 2026-08-17) and again here for the pandas repo's equivalent column — same fix both times, route through `DoubleType`/`float` before the integer cast.
- **`to_timestamp` throws under this workspace's ANSI settings** — use `try_to_timestamp(col, lit(format))`, with the format wrapped in `lit(...)`. Already hit once building `ilab_charges_bronze` ([[Projects/Databricks/Pipelines/Historical Services Bronze Pipeline|Historical Services Bronze Pipeline]]); will recur here for services' string `startdate`/`enddate`.
- **`service_rls` must be built after the core-name remap** — get the order wrong and Power BI's iLab Utilisation RLS silently breaks.

## See also

- `docs/superpowers/prompts/2026-09-06-ilab-silver-layer-prompt.md` (in `ri_ilab`) — the full prompt this note summarises; paste it into a planning session to start the actual plan
- [[iLab Domain Pipelines]] — the pandas pipeline this migration ports from
- [[Shared DataFrame Utilities]] — `fix_df()`/`identify_latest_data_rows()` and the rest of the cleanup layer being ported
- [[Projects/Databricks/Pipelines/Historical Services Bronze Pipeline|Historical Services Bronze Pipeline]] — the existing Databricks-native bronze layer this silver layer would sit on top of, and where the decimal-cast/ANSI-timestamp gotchas were first found
- [[Projects/Databricks/Reference/Databricks Conventions|Databricks Conventions]] — the medallion/naming/SCD2 rules the open decisions above are testing against
- [[Projects/Databricks/Tables/Standalone Remap Tables Reference|Standalone Remap Tables Reference]] — the governed remap tables the inlining decision would drift from
- [[Overview|RI iLab]]
- **Derived layer** (`graphify/`, never hand-edited): [[iLab Silver Layer]], [[One Bronze In, One Silver Out (No Joins)]], [[Parity Oracle for Silver vs Current Output]], [[SCD2 Passthrough Cannot Apply to ilab_bronze]], [[Silver Column Naming UPPER_SNAKE_CASE vs Repo Names]], [[Inline REMAP_ Literals vs Governed Remap Tables]], [[Missing created_at in ilab_services_bronze (Blocker)]], [[Load-Bearing Transform Order in Charges]], [[ilab_charges_silver]], [[ilab_labs_silver]], [[ilab_members_silver]], [[ilab_services_silver]], [[ilab_bronze Input Tables]], [[fix_customer_cols()]], [[identify_latest_data_rows()]], [[_COMMUNITY_Silver Naming Questions]], `_COMMUNITY_Cross-System Data Governance` *(no community since export `1ac3015`)*
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[fix_df()]]
