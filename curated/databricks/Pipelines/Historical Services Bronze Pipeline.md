# Historical Services Bronze Pipeline

**Not `ri_ilab` Python code** — this is a set of Databricks notebooks under `/Workspace/Users/milinda.abayawardana@monash.edu/ilab/dev/{services,labs,members,charges}/`, never committed as code in that repo. It is a parallel, Databricks-native ingestion of the historical iLab exports (services, labs, members, charges, back to 2022-11) that sits *alongside* — not inside — the `ilab/*` Python pipelines in [[Projects/RI iLab/Overview|RI iLab]]. The `ri_ilab` repo documents it in `docs/2026-09-09-ilab-historical-bronze-tables.md`, a current-state snapshot verified against the notebooks and live Unity Catalog row counts on **2026-09-09**; that doc replaced the 2026-08-13 session notes this note was first written from (`aed1522`). Graphify indexed the older doc until the `ri_ilab` export at `1ac3015` (2026-09-19). Since then the table links in "See also" below resolve to the new doc's nodes, which name the tables by schema (`ilab_bronze.ilab_services`) without the suffix.

> [!warning] Table names and notebook names differ
> The bronze notebooks are still named `ilab_*_bronze`, but the tables they write are named **without** the suffix: `ilab_bronze.ilab_services`, `ilab_bronze.ilab_labs`, `ilab_bronze.ilab_members`, `ilab_bronze.ilab_charges`. Earlier versions of this note and [[Databricks Migration State]] used the suffixed names for the tables, as did the graphify export until `1ac3015`. Verified 2026-09-09.

> [!warning] Point-in-time snapshot
> The services, labs and members figures below are as of **2026-09-09**, re-checked live on **2026-09-11** and again on **2026-09-12** (profile `DEFAULT`, read-only) — unchanged. The **charges figures changed on 2026-09-12**, when the CSV reader defect below was fixed and `ilab_bronze.ilab_charges` was rebuilt; the charges counts in this note are the post-rebuild ones. Bronze now rebuilds automatically after every successful `ingest_pipeline` run, so the counts move with the monthly ingest rather than only when someone reruns them by hand. Re-verify before relying on a figure.

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: the doc this note draws on, `docs/2026-09-09-ilab-historical-bronze-tables.md`, is indexed (14 nodes), and the 2026-08-13 session notes are not (0). The derived links in See also resolve to the new doc's nodes. Two sentences that described the old node names are corrected. Everything else is live Databricks state from the dated checks in this note, which the export doesn't carry.

## Shape of the thing

Four domains — **services**, **labs**, **members**, **charges** — each follow the same two-stage pattern:

1. A `historical_*` notebook unions the historical exports sitting in a Volume into a plain (non-Lakeflow) Delta table in `new_test`.
2. An `ilab_*_bronze` notebook unions that historical table with the raw SFTP-ingested table (and, for services only, a third `pre_download_service` table), de-duplicates, and writes the bronze table in `ilab_bronze`.

All of these are **standalone notebooks run as one-off serverless jobs**, not Lakeflow pipelines — Lakeflow-managed tables block direct external `INSERT`/`MERGE`, so plain Delta tables are used throughout. To upload a changed notebook: `databricks workspace import`. As of **2026-09-12**, job **`ilab_bronze_tables`** (`916154989512260`) runs all four `ilab_*_bronze` notebooks in parallel, and is triggered by a `trigger_bronze` task in the ingest job (`93376113759500`) that fires on `ALL_SUCCESS` of the pipeline task — so bronze now rebuilds after every successful ingest, scheduled or manual. The `historical_*` notebooks stay manual, wrapped in job **`ilab_historical_tables`** (`957557695632880`), whose final task chains into the bronze job once all five have succeeded. It exists for the manual volume-upload path, and rerunning it monthly would re-read ~4.8M rows of unchanged Parquet for nothing. See [[#First run of `ilab_historical_tables` (2026-09-15)]] for its first run. Neither new job carries a schedule of its own. (`01_standalone_tables` remains unrelated — it covers the `ri_standalone/` notebooks, see [[ri_master_list SCD2 Reference]].) Until then this was the "dead-ended bronze plane" gap recorded in [[Databricks Migration State]]; the orchestration half of that gap is now closed, the consumer half is not.

> [!warning] What automating the rebuild changed, and what it did not
> Three consequences of the 2026-09-12 wiring, none of them blocking but all of them now unattended:
>
> - **A failed rebuild leaves no table.** Each `ilab_*_bronze` notebook does `DROP TABLE IF EXISTS` and then `saveAsTable`. Run by hand that was fine — someone was watching. On a monthly trigger, a drop followed by a failed write leaves the bronze table *absent* until someone reruns it, and the only signal is the failure email. The drop exists to allow schema changes; `mode("overwrite")` alone would otherwise do.
> - **The human checkpoint is gone.** The `multiLine` defect below was caught because a person looked at the row counts. Nothing now compares a rebuild against the previous one, so a bad ingest propagates into bronze automatically. Because the readers skip `.csv.gz` files by design (see the callout under [[#The multiLine ingest defect and the 2026-09-12 rebuild]]), a month whose file was compressed before the 5th-of-month ingest never arrives, and nothing errors. That is the realistic failure path, and it is why the monthly landing check below exists. It was left out of the 2026-09-12 orchestration work, and is now run by hand — first on 2026-09-14.
> - **Overlapping runs queue rather than skip.** Replacing the ingest job's settings made the Jobs API apply its default `queue.enabled: true`, which the job had not carried before. With `max_concurrent_runs: 1` a second run now waits instead of being dropped, and `trigger_bronze` has `timeout_seconds: 0` — no timeout. A monthly cron cannot realistically collide with itself, but a manual `ilab_historical_tables` cascade running at the same moment would make the ingest run wait rather than fail.

### Table inventory

Catalog is `pen_research_infrastructure_insights_prd` throughout. "Source files" = distinct `file_name` values in the table.

| Notebook | Table | Type | Rows | Source files |
|---|---|---|---|---|
| `services/historical_services` | `new_test.historical_services` | MANAGED | 2,106,794 | 44 |
| `services/pre_monthly_download_services` | `new_test.pre_download_service` | MANAGED | 37,796 | 3 |
| `services/ilab_services_bronze` | `ilab_bronze.ilab_services` | MANAGED | 242,589 | 52 |
| `labs/historical_labs` | `new_test.historical_labs` | MANAGED | 86,738 | 44 |
| `labs/ilab_labs_bronze` | `ilab_bronze.ilab_labs` | MANAGED | 6,758 | 49 |
| `members/historical_members` | `new_test.historical_members` | MANAGED | 356,655 | 44 |
| `members/ilab_members_bronze` | `ilab_bronze.ilab_members` | MANAGED | 149,330 | 49 |
| `charges/historical_charges` | `new_test.historical_charges` | MANAGED | 2,242,261 | 9 |
| `charges/ilab_charges_bronze` | `ilab_bronze.ilab_charges` | MANAGED | 1,441,141 | 10 |

Raw SFTP tables feeding the bronze layer (all `STREAMING_TABLE` in `new_test`, written by `ingest_pipeline`). Services, labs and members hold 5 monthly extracts as of 2026-09-09; **charges holds only the September extract** since its 2026-09-12 full refresh (see below):

| Raw table | Rows |
|---|---|
| `new_test.services` | 282,676 |
| `new_test.labs` | 10,566 |
| `new_test.members` | 44,811 |
| `new_test.charges` | 157,666 |

The bronze row counts differ from those recorded when the tables were first built on 2026-08-17/18 (`ilab_services` 243,391 → 242,589; `ilab_labs` 6,720 → 6,758; `ilab_members` 146,141 → 149,330; `ilab_charges` 1,467,512 → 1,492,840; `pre_download_service` 25,603 → 37,796), so the tables have been rebuilt at least once since — the 2026-09-06 survey in [[Databricks Migration State]] still carried the original figures. `ilab_charges` was then rebuilt again on **2026-09-12** (1,492,840 to 1,441,141) after the ingest fix described below.

### Source volume

`/Volumes/pen_research_infrastructure_insights_prd/ilab_bronze/historical_data/` with one subfolder per domain: `services/` (47 files — 44 monthly snapshots plus 3 `pre_download` files), `labs/` (44), `members/` (44), `charges/` (9).

> [!warning] Two monthly snapshots are permanently missing: 2025-12 and 2026-02
> Services, labs and members hold **44** monthly files each, but 2022-11 → 2026-08 spans **46** months. There is no `20251202_…` and no `20260202_…` file for any of the three domains — absent from the volume *and* from the raw SFTP tables. Verified 2026-09-12 by checking every month in the range against both sources.
>
> **Nothing can be done about this.** The files were never delivered, and the SFTP server keeps only recent months (older ones are compressed, then dropped), so there is nowhere left to fetch them from. Treat the two months as permanently absent: a month-over-month comparison spanning 2025-12 or 2026-02 will show a hole, and that hole is the data, not a bug to chase. Re-deriving them from adjacent months is not possible either — these are point-in-time snapshots of services, labs and members as they stood, not transactional records that can be replayed.
>
> Charges is unaffected: its exports are overlapping rolling 12-month windows rather than monthly snapshots, so both months are still covered.

Every notebook takes the volume location as widgets — `volume_catalog_name`/`volume_schema_name`/`volume_name`, defaulting to `pen_research_infrastructure_insights_prd`/`ilab_bronze`/`historical_data` — so nothing hardcodes the path. Unity Catalog managed volumes cannot be renamed or moved across schemas in place (`databricks volumes update` only touches name/owner/comment): moving this volume into `ilab_bronze` on 2026-08-17 meant creating a new volume, copying every file, verifying the count, then deleting the old one.

## The shared build pattern

### `historical_*` notebooks

- Widgets: `catalog_name`/`schema_name`/`table_name` (defaults `pen_research_infrastructure_insights_prd`/`new_test`/`historical_<domain>`) plus the three volume widgets above.
- A module-level `HISTORICAL_<DOMAIN>_TYPES` dict defines the target schema (column name → Spark type).
- **Files are read one at a time**, each with its own naturally-inferred schema, then cast to the shared schema as a post-read `select` projection — missing columns filled with `lit(None).cast(type)`. Combined with `functools.reduce(lambda l, r: l.unionByName(r), file_dataframes)`.
- Each row is tagged with an uppercased `file_name` from its source file.
- Written with `DROP TABLE IF EXISTS` + `mode("overwrite")` + `option("delta.columnMapping.mode", "name")` + `saveAsTable`, then `dbutils.notebook.exit(f"Created … with N rows")`.

**Why file-by-file rather than one batch read** — [[File-by-file parquet read then cast|the load-bearing pattern]], reusable for any heterogeneous-parquet ingestion here. The services files span 3 schema shapes (17/18/19 columns, as `servicecategory`/`version` were added over time). Two more obvious approaches failed first:

| Approach | Failure |
|---|---|
| `mergeSchema=true` on a combined read | `[CANNOT_MERGE_SCHEMAS]` — a column inferred `DOUBLE` in all-null files vs `BIGINT` elsewhere |
| Explicit unified `StructType` on the read | `[FAILED_READ_FILE.PARQUET_COLUMN_DATA_TYPE_MISMATCH]` — a Photon-specific rejection of implicit int64→double widening at decode time; Photon cannot be disabled in a serverless notebook session (`[CONFIG_NOT_AVAILABLE.WITHOUT_SUGGESTION]`) |

Reading each file with its natural schema and casting afterwards never asks Photon's reader to widen at decode time.

### `ilab_*_bronze` notebooks

- Widgets: `source_catalog_name`/`source_schema_name` (default `…`/`new_test`), one table-name widget per source, and `target_catalog_name`/`target_schema_name`/`target_table_name` (default `…`/`ilab_bronze`/`ilab_<domain>`).
- The `historical_*` table already matches the shared bronze schema (`ILAB_<DOMAIN>_BRONZE_TYPES` = the historical columns + `file_name`) and is read as-is. The raw SFTP table is all-`STRING` and is cast column-by-column to the shared types, with string values upper-cased to match.
- The raw table is read **batch-only** — these notebooks never write to, drop, or otherwise mutate the ingested tables.
- Combined with `unionByName`, de-duplicated (below), then the same `DROP TABLE IF EXISTS` + overwrite `saveAsTable` + `dbutils.notebook.exit`.

### De-duplication (all four bronze tables)

[[De-dup on all columns except file_name, latest file_name wins|The dedup step]]: sort by `file_name`, then drop full-row duplicates comparing **every column except `file_name`**, keeping the row with the most recent (highest-sorting) `file_name` — a `row_number()` window partitioned on all non-`file_name` columns, ordered by `file_name` descending, filtered to `_row_number == 1`.

Applied to the in-memory DataFrame *before* the write, not as a post-write pass: overwriting a table while reading from it in the same query isn't allowed.

**The row-count drop is large and is expected.** The historical and raw sources legitimately overlap for months both cover, but the bigger effect is that these are monthly *snapshots* — most rows repeat unchanged for many consecutive months. With `file_name` out of the dedup key, every unchanged repeat collapses into one group, so the result keeps the most recent occurrence of each distinct row across the entire history, not just within overlapping months. This is normal snapshot behaviour (services/prices/labs are added and dropped over time; identical rows across months are genuine repeats, not distinct facts) — **confirmed correct by the user**, not data loss. The first build saw `ilab_services` collapse from 2,356,353 unioned rows to 243,391.

Charges is the exception in degree, not in kind — see below.

### Verification cell

Every bronze notebook ends with a `display(...)` cell grouping the written table by `file_name` and a derived `source_table`, giving row counts per source file. `source_table` is not a real column — it is inferred from the shape of `file_name` (`00000000_` prefix → `pre_download_service`; `.CSV` suffix → the raw SFTP table; otherwise → the `historical_*` table).

This cell sits **after** `dbutils.notebook.exit(...)`, so it only runs when the notebook is executed interactively; an automated job run stops before it. A convention worth keeping: ad hoc row-count checks stay in the notebook without costing anything on a scheduled run.

## Per-domain specifics

### Services

Schema `HISTORICAL_SERVICES_TYPES`, 20 columns (+ `file_name` in bronze = 21): `type`, `coreid`, `core_name`, `serviceorequipmentid`, `serviceorequipmentname`, `serviceorequipmentextvisible`, `blankoreqinstanceid`, `blankoreqinstancename`, `custom_field_1..3`, `pricecustomcode`, `priceid`, `pricetype`, `priceextvisible`, `price`, `startdate`, `enddate`, `servicecategory`, `version`.

**Column-name divergence:** the source files use `corename` (no underscore). `historical_services` builds against `corename` internally, then renames to `core_name` on write — per an in-code comment, "historical_services will be migrated to core_name later". `preprocess_services` still uses `corename`, so those two tables' column names differ here.

Services is the only domain with a **three-way split**, because its volume holds 3 non-standard-named files alongside the 44 monthly ones:

- `historical_services` reads only files ending `_monash_university_all_cores_services_list.parquet` (the 44 monthly files).
- `pre_monthly_download_services` handles the other 3, writing them to a separate table `pre_download_service` (**not** merged into `historical_services`). It duplicates `HISTORICAL_SERVICES_TYPES` and the `apply_historical_services_schema` helper rather than importing from a shared module.

| Source file | Renames | Defaults filled | Rows |
|---|---|---|---|
| `au_animal_module_asset_id_charge_name.parquet` | `id`→`serviceorequipmentid`, `name`→`serviceorequipmentname` | `type`="SERVICE", `core_name`="MONASH ANIMAL RESEARCH PLATFORM" | 31,559 |
| `monash_equipment.parquet` | `id`→`serviceorequipmentid`, `name`→`serviceorequipmentname`, `core_id`→`coreid`, `created_at`→`startdate`, `deleted_at`→`enddate` | `type`="EQUIPMENT" | 3,135 |
| `monash_services.parquet` | same as `monash_equipment.parquet` | `type`="SERVICE" | 3,102 |

Each gets a synthetic `file_name` (`00000000_AU_ANIMAL_MODULE_ASSET_ID_CHARGE_NAME`, `00000000_MONASH_EQUIPMENT`, `00000000_MONASH_SERVICES` — `00000000` because these files carry no date in their name) and has its string columns upper-cased. The `created_at`→`startdate` rename is what makes `created_at` unrecoverable downstream except by that prefix — the blocker recorded in [[Projects/RI iLab/Initiatives/iLab Silver Layer Migration|iLab Silver Layer Migration]].

`ilab_services` therefore unions **three** sources. The raw `services` table is CamelCase (`CoreID`, `ServiceOrEquipmentID`, …) and is mapped via `SERVICES_COLUMN_MAP`. Post-dedup contribution: `historical_services` 177,074 (44 files) · `services` 59,277 (5 files) · `pre_download_service` 6,238 (3 files).

The volume's monthly files run 2022-11 → 2026-08 with **two** gaps: there is no `20251202_…` and no `20260202_…` file. Both are permanent, and both affect labs and members identically — see the callout under [[#Source volume]]. (An earlier version of this note recorded only the 2026-02 gap, and only for services.)

### Labs

Schema `HISTORICAL_LABS_TYPES`, 10 columns (+ `file_name` = 11 in bronze): `lab_name`, `first_name`, `last_name`, `email`, `role_type`, `pre_approval_amount`, `overage_buffer`, `departments`, `organizations`, `centers`. Consistent across all 44 files — no schema evolution to reconcile, so no defaults-dict machinery is needed.

Only two sources (no `pre_download_labs` split). The raw `labs` table already uses the same lowercase column names as `historical_labs`, so no rename map is needed — unlike services/members/charges.

**Cast gotcha — decimal-formatted strings:** `pre_approval_amount` and `overage_buffer` arrive from raw `labs` as strings like `"1000.0"`, and `CAST(… AS BIGINT)` rejects a decimal-looking string outright rather than truncating. They are routed through `DoubleType` first: `col(c).cast(DoubleType()).cast(LongType())`. Only the `labs`-sourced side needs this — the historical parquet files already store these as `int64`. The same bug class turned up independently in the pandas pipeline's own `pre_approval_amount` handling — see [[Projects/RI iLab/Initiatives/iLab Silver Layer Migration|iLab Silver Layer Migration]].

### Members

Schema `HISTORICAL_MEMBERS_TYPES`, 11 columns (+ `file_name` = 12 in bronze), all `StringType` — including `pre_approval_amount_per_member`, unlike labs' numeric equivalents: `first_name`, `last_name`, `email`, `institution_facility_or_group`, `role`, `title`, `time_zone`, `pre_approval_amount_per_member`, `account_created`, `last_account_activity`, `institution_login`. Consistent across the 44 files.

Two sources, no split table. The raw `members` table needs one rename via `MEMBERS_COLUMN_MAP`: its column is literally named `Institution, Facility or Group` (comma and spaces). All other names already match. No cast gotcha — every column is `StringType` on both sides.

### Charges

The odd one out: the source files are **not** disjoint monthly snapshots. They are overlapping rolling-window exports named `<range-start>_<range-end>_charges_report_source_data….parquet` — one full-history bulk file (`20180213_20230901…`), one mid-range bulk file (`20220402_20250402…`), and 7 monthly re-extracts of a rolling ~12-month window (`20250101_20260101…` through `20250801_20260801…`), each advancing by a month and heavily overlapping the previous. `historical_charges` filters on `.parquet` only (no name-pattern exclusion needed).

Schema `HISTORICAL_CHARGES_TYPES`, 51 columns (+ `file_name` = 52 in bronze):

| Spark type | Columns |
|---|---|
| `LongType` | `asset_id`, `charge_id`, `core_id`, `vendor`, `unspsc_code`, `unspsc_name`, `facility_catalog_number`, `central_catalog_number` |
| `DoubleType` | `quantity`, `price`, `total_without_tax`, `tax`, `total_price` |
| `TimestampType` | `creation_date`, `purchase_date`, `completion_date`, `billing_date`, `date_file_sent_to_erp`, `billing_event_end_date` |
| `StringType` | everything else |

3 distinct schema shapes across the 9 files:

| Files | Shape |
|---|---|
| the oldest bulk file | 51 columns, dates as native `TIMESTAMP` |
| the mid-range bulk file | only 48 columns (missing `central_catalog_number`, `facility_catalog_number`, `unspsc_code`, `unspsc_name`, `vendor`, filled `NULL`); also carries its own baked-in `file_name`/`file_sort` provenance columns from the source export, simply not selected since they are outside the target schema |
| the 7 rolling monthly files | 51 columns, but the 6 date columns are `'yyyy-MM-dd HH:mm:ss +1100'`-style **strings**, not native timestamps |

`historical_charges` handles the third shape by parsing with `to_timestamp(col, "yyyy-MM-dd HH:mm:ss xx")` (pattern `xx` = 4-digit UTC offset with no colon) instead of a plain `.cast()` when a date column arrives as `StringType`.

**Cast gotcha — `to_timestamp` throws under ANSI:** the raw `charges` table is all-`STRING`, so both numeric columns (decimal-formatted like `"5.0"`, or blank) and date columns (offset-style strings, the literal `"n/a"`, or occasional garbage text) need defensive parsing in `ilab_charges_bronze`:

- Numeric → `expr("try_cast(`<col>` AS DOUBLE)")`, then `.cast(LongType())` for integer targets, so malformed values become `NULL` instead of raising `[CAST_INVALID_INPUT]`.
- Dates → `try_to_timestamp(col, lit(format))`. Plain `to_timestamp` raises `[CANNOT_PARSE_TIMESTAMP]` under this workspace's ANSI settings when it hits unparseable input. **The format argument must be wrapped in `lit(...)`** — `try_to_timestamp` (unlike `to_timestamp`) resolves a bare Python string as a column reference and raises `[UNRESOLVED_COLUMN.WITH_SUGGESTION]`.

As of **2026-09-12, no rows carry a `NULL creation_date`**. The 2,523 that did (0.17% of the table, recorded 2026-09-09) were **not** unparseable source values, as this note previously claimed: they were fragments of rows split by the missing `multiLine` reader option, and they vanished when charges was re-ingested — see below. The defensive `try_*` parsing above stays, because it is what turned those malformed values into nulls instead of a failed run.

`CHARGES_COLUMN_MAP` maps the raw table's free-text/Title Case names, including two GL-account columns whose names carry a **trailing space**: `"Internal: Debit GL Account|Credit GL Account "` and `"External: Debit GL Account|Credit GL Account "`.

**`file_name` date reformatting:** raw SFTP charge file names lead with `MMDDYYYY_MMDDYYYY` (e.g. `04012025_04012026_charges_report_source_data_…csv`) while the volume files use `YYYYMMDD_YYYYMMDD`. Since dedup and verification sort and group by `file_name`, the mismatch would corrupt "most recent file_name wins" ordering. Fixed with a single `regexp_replace` on the `charges`-sourced side only, capturing `MM`/`DD`/`YYYY` and re-emitting via backreferences:

```
regexp_replace(col("file_name"),
  r"^(\d{2})(\d{2})(\d{4})_(\d{2})(\d{2})(\d{4})_(.*)$", r"$3$1$2_$6$4$5_$7")
```

Verified in the table: all 5 raw-sourced file names now read `20250401_20260401_…` etc.

Because the historical files are overlapping rolling-window exports rather than disjoint snapshots, dedup does more work here than for the other domains: a charge whose fields never changed across re-extracts collapses to one row, while a charge whose fields changed between extracts (e.g. unbilled → billed) yields one row per distinct state, each keeping its own most-recent `file_name`.

## Adjacent, not part of this pipeline

- **[[preprocess_ilab Lakeflow pipeline (adjacent)|`preprocess_ilab`]]** — Lakeflow pipeline `350e93cb-026f-4262-9d9e-03022444bb4b`, separate from `ingest_pipeline` so raw SFTP ingestion stays untouched and typing/cleanup lives downstream. Reads `new_test.services` (raw all-string `STREAMING_TABLE`), writes `new_test.preprocess_services` (223,956 rows as of 2026-09-09). Transformation file `/Workspace/Users/milinda.abayawardana@monash.edu/preprocess_ilab/transformations/preprocess.py`; casts `CoreID`/`ServiceOrEquipmentID`/`PriceID` to `int` and `Price` to `double`, lowercases column names, uppercases string values. Note it keeps `corename`, unlike `historical_services`. A different pipeline solving a different problem (typing, not historical backfill).
- **`ilab/dev/dim_services`** — a downstream dimension build against the `ilab_3y` schema (joins `ilab_award_income_researcher`, `services` and `dim_ilab_facility`, adds a MARP animal `category`, writes `ilab_3y.dim_ilab_services`). It does not read the `ilab_bronze` tables above.

## The multiLine ingest defect and the 2026-09-12 rebuild

`ingest_pipeline`'s Auto Loader readers set no `multiLine`, `quote` or `escape` options. iLab's charges CSV quotes free-text fields (`Notes` and the two justification columns) that can contain line breaks, so every such break split a record and shifted the remaining values into a new row. Roughly 1% of every charges extract arrived broken — 8,101 of 794,261 raw rows carried a blank `Charge ID`, rising steadily from 0.93% (April) to 1.13% (September).

Proven on **2026-09-12** by reading the September extract three ways:

| Reader options | Rows | Blank `Charge ID` |
|---|---:|---:|
| as shipped | 158,708 | 1,787 |
| `multiLine` | 157,666 | 2 |
| `multiLine` + `escape` set to the quote character | 157,666 | 0 |

The same extract stored as Parquet in the historical volume had **zero** blank IDs. That is what ruled out a fault in iLab's export: only the CSV path was affected. The other four feeds parse identically either way, but the options were applied to all five readers regardless, as a shared `CSV_OPTIONS` constant, so they cannot drift apart.

Sequence, all on 2026-09-12:

1. `ingest.py` fixed, uploaded, and validated (a `validate_only` update, `COMPLETED`).
2. All five raw tables copied to `pen_research_infrastructure_insights_prd.backup` as `<table>_20260912`, each verified row-for-row against its source.
3. `charges` alone re-ingested, via `full_refresh_selection` in the request body. The CLI's `--full-refresh` flag resets **every** table in the pipeline and would have destroyed `members_funds`, whose four older months exist nowhere but that backup.
4. `ilab_charges_bronze` rerun, after snapshotting bronze to `backup.ilab_charges_20260912`.

> [!warning] The SFTP server keeps only recent months, and older files become `.csv.gz`
> The readers' `*.csv` globs **explicitly skip** compressed files — a deliberate choice, not an oversight, but one that raises no error when it bites. That is why the July charges extract never reached `new_test.charges` at all. A full refresh therefore rebuilds from whatever is still uncompressed (September alone, on 2026-09-12), so raw `charges` now holds a single extract and its history lives entirely in the Parquet volume. Widening the glob to match `.csv.gz` would re-ingest already-loaded months as new files, so it was deliberately left alone.

Outcome, verified the same day: bronze charges went 1,492,840 to 1,441,141 rows and 14 to 10 source files, with null `charge_id` 2,513 to 0 and null `creation_date` 2,523 to 0. Distinct charge IDs rose from 1,149,824 to 1,149,926 — **105 real charges recovered** that the broken parsing had hidden. The only three IDs lost (`4439`, `4495`, `4548`) were fragment artifacts whose columns were shifted out of position; they were never real charges.

## First run of `ilab_historical_tables` (2026-09-15)

Run `935176870985425`, started by hand at 12:37:51 Australia/Sydney, ended `TERMINATED SUCCESS` at 12:53:06. It was the job's first run, so it was checked against a baseline and a backup taken just before it.

| Stage | Tasks | Time (Sydney) | Result |
|---|---|---|---|
| Historical builds, in parallel | `historical_services`, `pre_monthly_download_services`, `historical_labs`, `historical_members`, `historical_charges` | 12:37:51 → 12:46:35 | 5/5 SUCCESS, serverless |
| `trigger_bronze` | starts `ilab_bronze_tables` run `590247887475268` and waits for it | 12:46:35 → 12:53:06 | SUCCESS; the four bronze tasks all succeeded |

The parent run stays open until the triggered bronze run finishes, so one finished run means both jobs are done. The whole cascade takes about 15 minutes.

**What was checked.** Before the run, all 9 tables were copied to `backup.<table>_20260915` with `DEEP CLONE`, and each copy's row count matched its original. A shallow clone would not do: the job drops the originals, and a dropped managed table's files are deleted. After the run, every table:

- had a new write time;
- had the same row count, distinct `file_name` count and column count as before;
- matched its backup row for row, with `EXCEPT ALL` returning 0 in both directions.

Every table shows Delta version 0 both before and after: `DROP TABLE` followed by `saveAsTable` creates a new table, so version history does not survive a rebuild. The row counts in [[#Table inventory]] are therefore confirmed as of 2026-09-15.

**The run also tested three unrun notebook edits.** `historical_charges`, `historical_services` and `pre_monthly_download_services` had each been edited after their table was last built: 2026-08-18, 2026-09-09 and 2026-09-08 UTC. Their output is identical to the previous build, so those edits did not change the data.

The nine `backup.*_20260915` tables are still in place as of 2026-09-15, and nothing reads them. They can be dropped.

## Monthly landing check

Run by hand, read-only, after each monthly ingest (the ingest runs on the 5th, 02:00 Australia/Sydney; bronze rebuilds straight after it). It answers one question: did every month's file reach bronze for every domain? The readers skip `.csv.gz`, and nothing else would notice.

**Procedure:**

1. Confirm the latest `ingest_pipeline` run (`93376113759500`) and its `ilab_bronze_tables` run (`916154989512260`) both ended `SUCCESS`.
2. For each raw table in `new_test` — `services`, `labs`, `members`, `members_funds`, `charges` — list distinct `file_name` with row counts.
3. For each bronze table in `ilab_bronze`, list distinct `file_name`. Take the `YYYYMM` prefix of every monthly file, then compare against every month from 2022-11 to the current month.
4. Any missing month other than the two permanent gaps (2025-12, 2026-02) is a finding. Check whether the `historical_data` volume covers it before treating it as lost.
5. For charges, check that the newest rolling-window file (`<YYYYMM01>_<YYYYMM01 + 1y>_…`) is present. The windows overlap, so one missing window loses no charges.

### 2026-09-14 — first run

Both jobs last ran `SUCCESS` on 2026-09-12 (ingest run `990249552141398`, bronze run `1004217239983611`). The last scheduled ingest ran on 2026-09-05. Raw file counts: services, labs, members and members_funds hold 5 extracts each (2026-04, 05, 06, 08, 09); charges holds 1.

| Domain | Months in bronze | Expected (2022-11 → 2026-09, minus 2 permanent gaps) | Result |
|---|---:|---:|---|
| services | 45 (plus 3 `00000000_` pre-download files) | 45 | ✅ complete |
| labs | 45 | 45 | ✅ complete |
| members | 45 | 45 | ✅ complete |
| charges | latest window `20250901_20260901` (raw CSV, 157,666 rows) | latest window present | ✅ complete — 10 source files |
| members_funds | — excluded from the pipeline (see below) | 2026-04 → 2026-09 | ⏸ out of scope — 2026-07 missing |

**2026-07 never arrived through ingest for any domain.** No `20260702_*.csv` exists in any raw table. This matches the July charges extract recorded above as compressed before ingest could read it. For services, labs and members the gap is invisible, because the volume holds `20260702_*.parquet` for all three and bronze takes July from there. Charges is covered by the volume's `20250701_20260701` window.

> [!note] `members_funds` is excluded from the pipeline for now — decision recorded 2026-09-14
> `members_funds` is **deliberately out of scope** at this time. It gets no historical backfill, no bronze table and no place in the silver migration, so gaps in it are recorded but not chased. `ingest.py` still defines a `members_funds` streaming table, so raw extracts keep landing in `new_test.members_funds`; the exclusion covers everything after ingest. Revisit this callout when the domain is brought back in.

> [!warning] `members_funds` has no July 2026 extract anywhere
> With no historical volume and no bronze table, ingest is its only source. Its history starts at 2026-04, when the pipeline was created on 2026-04-22. The raw table and `backup.members_funds_20260912` both hold exactly 2026-04, 05, 06, 08 and 09. Whether the July file still sits on the SFTP server as `.csv.gz` was **not checked**: the SFTP drop cannot be listed from the CLI. The repo-written `ri_ilab.members_funds` and `ilab_3y.members_funds` (both last written 2026-09-08) were not inspected either, and they may hold only the current snapshot. Nothing reads `new_test.members_funds` today, so this is a hole in history rather than a live breakage.

## Relationship to the `ri_ilab` repo

`ilab/services/preprocess.py`'s `HISTORICAL_SOURCES` handling (see [[Projects/RI iLab/Subsystems/iLab Domain Pipelines|iLab Domain Pipelines]]) solves a similar heterogeneous-historical-source problem independently, in Python, against local CSVs — not the same code, not shared logic, just the same underlying data shape. The bronze tables here are the intended starting point for [[Projects/RI iLab/Initiatives/iLab Silver Layer Migration|iLab Silver Layer Migration]], which treats bronze as done and correct and would port the pandas cleaning logic on top of it.

## See also

- `Historical Services Pipeline Session Notes` *(no node since export `1ac3015`)* — the original 2026-08-13 session notes were deleted from the repo and replaced by the 2026-09-09 doc, whose nodes now carry this material, starting from [[iLab historical + bronze tables current state]]
- [[preprocess_ilab Lakeflow pipeline (adjacent)]], `ingest_pipeline (raw SFTP ingestion)` *(no node since export `1ac3015`)* — the separate pipelines feeding and sitting beside this one
- [[Projects/RI iLab/Initiatives/iLab Silver Layer Migration|iLab Silver Layer Migration]] — the planned Databricks-native replacement for the pandas pipeline; shares the decimal-cast and ANSI-timestamp gotchas above
- [[Databricks Migration State]] — where these tables sit in the wider catalog survey, and the unconsumed-bronze gap
- [[File-by-file parquet read then cast]], [[De-dup on all columns except file_name, latest file_name wins]]
- `historical_services Table`, `historical_labs Table`, `historical_members Table`, `historical_charges Table` *(no nodes since export `1ac3015`; the 2026-09-09 doc covers the four together as [[historical_ notebooks (Volume parquet - new_test)]])*
- [[ilab_bronze.ilab_services]], [[ilab_bronze.ilab_labs]], [[ilab_bronze.ilab_members]], [[ilab_bronze.ilab_charges]] — graphify nodes, named by schema since export `1ac3015` (the old nodes carried the `_bronze` suffix the tables no longer have)
- `_COMMUNITY_Historical Services Pipeline` *(no community since export `1ac3015`)*
- [[Projects/RI iLab/Subsystems/iLab Domain Pipelines|iLab Domain Pipelines]] — the Python-side echo of the same heterogeneous-source problem
- [[Overview|Databricks]] — the catalog this pipeline writes into
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[ilab_bronze Input Tables]], [[pre_download_service table (3 non-standard services files)]], [[Missing created_at in ilab_services_bronze (Blocker)]], [[Combine historical and SFTP services data.]]
- **Derived layer — Power BI consumers** (`graphify/`, never hand-edited): [[ilab_award_income_researcher]], [[ilab_award_income_researcher_1]]
