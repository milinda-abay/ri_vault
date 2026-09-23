# Pure Bronze Pipeline

`pure_bronze` (catalog `pen_research_infrastructure_insights_prd`) re-creates, one notebook per table, the 15 Pure-derived tables that the old `ri_non_ilab` Power BI report reads from `ri_lakehouse`. The report lives at `ri_pbi_reports (old)/ri_non_ilab` — it is **not** one of the 7 [[Projects/RI PBI Production/Overview|RI PBI Production]] reports.

## Shape of the thing

Today those 15 tables are built by the PURE section of a single unversioned SQL notebook, `/Workspace/Users/milinda.abayawardana@monash.edu/ri_lakehouse_prod`, lines 13–868 plus `fact_journal_metrics` around line 1091. It rebuilds everything with `CREATE OR REPLACE TABLE`, run as task `ri_lakehouse_prod` in job `Daily run - serverless` (`234277055527586`), cron `2 0 1 * * ?` — daily 01:02 Australia/Sydney. `ri_lakehouse_prod` is left untouched and keeps serving the report; `pure_bronze` is a parallel, native re-implementation, not a cutover.

**Scope decisions (2026-09-17):**

- Bronze holds the *modelled* tables the report reads, not raw PSA copies.
- Each build is a current-rows snapshot, not SCD2.
- Pure data only — the report's Monday Google Sheet (CDCO jobs) and its MFP Excel workbook are out of scope.
- No scheduled job yet; notebooks are run by hand as one-off runs.
- No Power BI changes.

### Sources

| Source | What it is |
|---|---|
| `lakehouse_psa_prd.pure.*` | The central Lakehouse PSA — a 1:1 copy of the Pure database, with SCD2 history (`_INGESTION_TIMESTAMP`, `_EXPIRATION_TIMESTAMP`, `_ROW_ACTIVE_FLAG`). Owned by the Lakehouse core team; no API or secrets needed to read it. |
| `lakehouse_bim_prd.research_organisation.simplified_research_organisation` | BIM reference |
| `lakehouse_bim_prd.external_organisation.external_organisation` | BIM reference — refreshes on a different cycle than `ri_lakehouse`, see [[#Validation and the explained-drift rule]] |
| `lakehouse_bim_prd.country.country` | BIM reference |
| `lakehouse_bim_prd.research_award.research_award` (+ `research_award_funding`) | BIM curated award entity — the source of `dim_upm_award` since 2026-09-23, see [[#dim_upm_award moved to BIM, 2026-09-23]] |

## Table inventory

`<table>` in a notebook name is the **logical name**; the table it writes keeps the `ri_lakehouse` name. The only case where they differ is `dim_application_bronze`, which writes `dim_upm_application` (`dim_application` is the report's own model table name). Every other notebook is `<table>_bronze`.

| Table (`ri_lakehouse` name) | Notebook | Key |
|---|---|---|
| `classification` | `classification_bronze` | `CLASSIFICATION_ID` |
| `dim_research_organisation` | `dim_research_organisation_bronze` | `RESEARCH_ORGANISATION_ID` |
| `dim_upm_application` | `dim_application_bronze` | `APPLICATION_ID` |
| `dim_upm_award` | `dim_upm_award_bronze` | `AWARD_ID` (legacy PK `upm_award_pk`) — built from BIM `research_award`, not ported |
| `dim_external_organisation` | `dim_external_organisation_bronze` | `EXTERNAL_ORGANISATION_ID` (legacy PK) |
| `dim_country` | `dim_country_bronze` | `(_SURROGATE_KEY, CLASSIFICATION_ID)` — either can be null from the FULL JOIN, never both |
| `dim_equipment` | `dim_equipment_bronze` | `EQUIPMENT_ID` |
| `dim_person` | `dim_person_bronze` | `ID` |
| `dim_externalperson` | `dim_externalperson_bronze` | `ID` |
| `dim_journal` | `dim_journal_bronze` | `JOURNAL_ID` |
| `dim_publication` | `dim_publication_bronze` | `PUBLICATION_ID` |
| `fact_journal_metrics` | `fact_journal_metrics_bronze` | `(JOURNAL_ID, JM_LIST_INDEX, ID, NAME, LIST_INDEX)` |
| `fact_application` | `fact_application_bronze` | `APPLICATION_ID` not null only — fans out, see [[#Deviations from the conventions]] |
| `fact_publication` | `fact_publication_bronze` | none — no legacy PK, see [[#Deviations from the conventions]] |
| `dim_applicant_role` | `dim_applicant_role_bronze` | `PERSON_ROLE_ID` |

## Build order

Four dependency waves:

1. `classification`, `dim_research_organisation`, `dim_upm_award` (BIM-only, no in-layer dependency since 2026-09-23)
2. `dim_upm_application`, `dim_external_organisation`, `dim_country`, `dim_equipment`, `dim_person`, `dim_externalperson`, `dim_journal`, `dim_publication`, `fact_journal_metrics`
3. `fact_application` (needs `dim_external_organisation`, `dim_upm_award`); `fact_publication` (needs `dim_equipment`, `dim_publication`)
4. `dim_applicant_role` (needs `fact_application`, `classification`)

## The shared build pattern

Every `ri_pure/<logical name>_bronze` notebook:

- Starts with a markdown "why" header explaining the table's key choices and oddities.
- Uses widgets `catalog_name`, `target_schema_name`, `target_table_name`, and `psa_catalog` / `bim_catalog` where needed — no fully-qualified names are hardcoded.
- Filters sources to `_ROW_ACTIVE_FLAG='Y'` in temp views. The legacy permanent views (`localized_string_text_v1`, `publisher`, `journal_association`, `metrics`, `organisation_association`) become **temporary** views here, so `pure_bronze` holds tables only.
- Ports the legacy SQL logic unchanged, with every `ri_lakehouse` dependency repointed to `pure_bronze`.
- Guards against duplicate names when uppercasing columns, then uppercases them.
- Checks key uniqueness before writing.
- Writes with `mode("overwrite").option("overwriteSchema","true")`. The option matters: without it, Delta kept the old lowercase column names — the first manual version of the notebook hit exactly this.
- Ends with `dbutils.notebook.exit("success: <table> rows=N")`.

Notebooks live under `ri_pure/`, mirroring the `pure_*` schemas — not under `ri_standalone/` (contrast [[Databricks Conventions]]).

## Validation and the explained-drift rule

Each build has a matching `<logical name>_bronze_validate` notebook, parameterised with `TABLES_TO_VALIDATE`. It checks:

- the table is not empty;
- all column names are uppercase;
- the key is unique and not null;
- parity with `ri_lakehouse.<same table>` — row count plus `exceptAll` in both directions over the shared columns, matched case-insensitively and cast to the reference types.

**The mismatch this exists for:** the BIM external organisation table refreshes at about 06:00 Sydney time (`_START_TIMESTAMP` 20:00 UTC), but `ri_lakehouse` builds at 01:02. So `ri_lakehouse` always holds the *previous* BIM refresh, and a bronze build run after 06:00 holds the newer one. Exact parity is only possible for a bronze build run between 01:02 and 06:00.

- **`dim_external_organisation_bronze_validate`** passes a mismatch only when every differing row is explained. The cutoff is `max(_START_TIMESTAMP)` in the reference table: a row only in bronze must have started after the cutoff; a row only in the reference must be expired in BIM (`_ROW_ACTIVE_FLAG='N'`) with an expiry after the cutoff.
- **`fact_application_bronze_validate`** passes a mismatch only when every differing row's `FUNDER_ID` is among the external-org ids that differ between the two layers. Since 2026-09-23 its parity is a **set** comparison over the non-award columns only, plus a separate award-link check — see below.
- **`dim_upm_award_bronze_validate`** no longer checks parity with `ri_lakehouse`; it recomputes the table from BIM and fails on any difference, printing the `ri_lakehouse` delta for information only.
- `dim_applicant_role` reaches exact parity despite sitting downstream of this drift, because the drift only touches funder-side columns.

## Deviations from the conventions

Deliberate departures from [[Databricks Conventions]], and why each one holds here:

| Deviation | Why |
|---|---|
| Snapshot instead of SCD2 | The PSA already keeps the history — a second SCD2 layer on top would be redundant. |
| String values are not uppercased | Pure titles and names are left as-is (unlike the standalone convention of uppercasing string values on write). |
| Source SCD2 columns are kept | Wherever the port selects them from the PSA. |
| Serverless compute | No Google Sheets egress is needed, unlike the standalone bronze builds. |
| Location: `ri_pure/`, not `ri_standalone/` | Mirrors the `pure_*` schemas. |
| `fact_application` and `fact_publication` guards report duplicate counts instead of raising | Both fact tables legitimately contain duplicate rows — see below. |

## Legacy bugs carried over

Ported unfixed, because scope is a re-implementation, not a rewrite:

- **`fact_journal_metrics`:** the `metrics` view's `metric_value` sub-select lists both `` `ID` `` and `id` in its `EXCEPT`, so `metric_value`'s own id is dropped. `metric_value` fans out per `metrics_id` (21,995,105 rows over 12,456,274 ids), so rows are distinguished only by `name` + `list_index`. Separately, the Power BI report's `fact_journal_metrics` query adds `Custom = coalesce(double_value, integer_value)` and then keeps only rows where `Custom = null` — it looks inverted.
- **`fact_application`:** the legacy `fact_application_pk` on `application_id` is informational and false. The table fans out through the funding, applicant and award joins, and has 7,806 exact duplicate rows.
- **`fact_publication`:** `equipment_researchoutput_assoc` is joined without the `_ROW_ACTIVE_FLAG='Y'` filter, so expired links can leak in. The legacy comment "Double check if list_index should be used like this?" is kept.
- **`classification`:** assumes each `localized_string` has exactly one active text row. Holds today; a second language would fan the table out.
- **`dim_country`:** the source cell is titled "(WIP)". Pure country codes are not fully mapped to ABS codes. The table is a FULL JOIN, which is why PBI treats it as many-to-many.
- **`dim_equipment`:** has a commented-out category join ("Not required all NULL").
- **`dim_journal`:** has a commented-out `journal_metrics` join.
- **Also in `ri_lakehouse_prod`, outside this port:** `fact_award`'s `expected_start_date` is taken from `expected_start_end_dat_end_dat`; the legacy views are permanent views in `ri_lakehouse`; the DEV section runs ad-hoc queries on every scheduled run.

## First run, 2026-09-17

> [!note] Point-in-time snapshot — first manual run of all 15 notebooks, 2026-09-17
>
> | Table | Notebook | Rows | Parity |
> |---|---|---:|---|
> | classification | classification_bronze | 10,646 | exact |
> | dim_research_organisation | dim_research_organisation_bronze | 1,323 | exact |
> | dim_upm_application | dim_application_bronze | 96,726 | exact (bronze has extra column `APPLICATION_TITLE`) |
> | dim_upm_award | dim_upm_award_bronze | 40,884 | exact |
> | dim_external_organisation | dim_external_organisation_bronze | 56,794 | explained drift: 454 only in bronze, 445 only in reference |
> | dim_country | dim_country_bronze | 353 | exact |
> | dim_equipment | dim_equipment_bronze | 44 | exact |
> | dim_person | dim_person_bronze | 121,426 | exact |
> | dim_externalperson | dim_externalperson_bronze | 558,767 | exact |
> | dim_journal | dim_journal_bronze | 22,239 | exact |
> | dim_publication | dim_publication_bronze | 390,270 | exact |
> | fact_journal_metrics | fact_journal_metrics_bronze | 10,432,538 | exact |
> | fact_application | fact_application_bronze | 711,676 | explained drift: 4 rows each way, all with `FUNDER_ID` among the 466 changed external-org ids; 96,726 distinct `APPLICATION_ID`, 7,806 exact duplicate rows |
> | fact_publication | fact_publication_bronze | 2,580,757 | exact (multiset); 359 exact duplicate rows |
> | dim_applicant_role | dim_applicant_role_bronze | 7 | exact |
>
> All 899 differing rows in `dim_external_organisation` were explained by the cutoff rule above. `dim_applicant_role` reached exact parity despite the upstream funder drift, because that drift only touches funder-side columns.

## dim_upm_award moved to BIM, 2026-09-23

`dim_upm_award` is no longer a port of the `ri_lakehouse_prod` award cell (PSA `upm_award` → `upm_awardcluster` → `upm_project` + BIM org + `classification`). It is built from `lakehouse_bim_prd.research_award.research_award` (active rows) — the curated award entity — keeping the table name so `ri_pbi_non_ilab_utilisation` binds unchanged.

**Why it's safe (probe, 2026-09-23):** every one of the 40,903 PSA-built `AWARD_ID`s is an active BIM award (BIM has 10 more); `AWARDED_DATE` equals `AWARD_DATE` on all of them; `AWARD_STATUS` differs on 4 (BIM newer); `SUM(research_award_funding.AWARDED_AMOUNT_IN_AUD)` equals the legacy `TOTAL_AWARDED_AMOUNT` on 40,899.

| Report-bound column | Now |
|---|---|
| `AWARD_ID`, `APPLICATION_ID` | BIM strings cast to `BIGINT` (the build refuses a non-numeric id) |
| `AWARD_DATE` | BIM `AWARDED_DATE` |
| `AWARD_STATUS` | BIM `AWARD_STATUS` |
| `AWARD_TYPE_CLASSIFICATION` | BIM `AWARD_TYPE` — was the constant `Award`; now Grant / Contract Research / Fellowship / … (visible change in the report) |
| `TOTAL_AWARDED_AMOUNT` | `SUM(AWARDED_AMOUNT_IN_AUD)` over active `research_award_funding`, `DECIMAL(32,4)` |

Every other BIM column is carried under its own name, with BIM lineage (`_START_TIMESTAMP`, `_EXPIRATION_TIMESTAMP`, `_ROW_ACTIVE_FLAG`, `_SURROGATE_KEY`). **Dropped:** `PROJECT_ID`, `AWARD_OWNER_ID`/`AWARD_OWNER`, the PSA `*_STA_DAT`/`*_END_DAT` ranges, `TOTAL_ACADEMIC_OWNERSHIP` — none were read by the report.

**Knock-on in `fact_application`:** BIM has no award→project link, so the award join moved from `project_id` to `application_id` (40,858 applications match vs 40,531 by project). `AWARD_TOTAL_ACADEMIC_OWNERSHIP` was dropped. The award fan-out, and so the row count, now differs from `ri_lakehouse` by design — which is why the validate compares non-award columns as a set and checks `(APPLICATION_ID, AWARD_ID)` pairs against `dim_upm_application ⋈ dim_upm_award` separately.

Before the change: bronze `fact_application` 713,078 rows, 305,382 with an award (39,649 distinct awards).

## Cutting the report over

Not done. To point the report at `pure_bronze`:

- The report's `get_table_from_mace` in `expressions.tmdl` points at `Database = ri_lakehouse` — cutting over means pointing it at `pure_bronze`.
- Every Power Query step that references lowercase column names (for example `application_id` in `preprocess_upm_application`) needs its case changed to match `pure_bronze`'s uppercase columns.
- The report already has a DirectQuery table `dim_upm_application` bound to `pure_bronze`, but no visuals use it yet.
- `dim_org_type`, which the report uses, is derived by the report itself and is not built here.
- `ri_lakehouse_prod` also builds tables this report doesn't use, so cutover doesn't touch them: `fact_award`, `dim_funding_category`, `fact_pure_publication`, `research_award_funding_equipment`, SAP `gl_code`, `ri_finance`.
- The cutover target is now `pure_silver`, not `pure_bronze` directly — silver applies the report's own preprocess logic, so the report reads a schema it can bind to without re-doing that work in M. See [[Pure Silver Pipeline#Cutting the report over]].

## Scheduling it

Not done yet. When it happens:

- A job in the style of `01_standalone_tables`, with each build followed by its matching validate (`ALL_SUCCESS`), ordered by the [[#Build order]] waves above.
- Serverless compute throughout.
- Run after 06:00 Sydney time, so the BIM external-organisation data is fresh. Parity against `ri_lakehouse` will then show explained drift as the normal case, until the report is cut over.

## Open items

- **The `ri_pure/` notebooks are not in any git repo** — they exist only in the Databricks workspace, under `/Workspace/Users/milinda.abayawardana@monash.edu/ri_pure/`. This is a risk: no version history, no review trail, no recovery path outside the workspace itself.
- No scheduled job yet — notebooks are run by hand.
- The report has not been cut over to `pure_bronze`; `ri_lakehouse_prod` still serves it.

## See also

- [[Overview|Databricks]]
- [[Databricks Conventions]]
- [[Databricks Migration State]]
- [[Pure Silver Pipeline]] — the cleaned layer built from this one, and the current cutover target
- [[Historical Services Bronze Pipeline]] — the closest other worked example of a from-scratch bronze build with its own dedup and casting gotchas
- [[Projects/RI PBI Production/Overview|RI PBI Production]] — the seven reports this catalog also serves; `ri_non_ilab` sits outside that set
