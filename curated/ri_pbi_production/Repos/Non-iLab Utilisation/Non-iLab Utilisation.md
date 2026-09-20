# Non-iLab Utilisation

`ri_pbi_production/ri_pbi_non_ilab_utilisation` is the **first Power BI report built on `pure_silver`**. It replaces the legacy `ri_pbi_reports (old)/ri_non_ilab` report, which reads `ri_lakehouse` and does its cleaning in Power Query. This is a new PBIP project, not an edit of the legacy one: the "Cutting the report over" steps in [[Pure Silver Pipeline]] were applied to a new report, and the legacy report is untouched.

The project started as a skeleton copied from `ri_pbi_ilab_utilisation`: four placeholder pages, `calendar`, `Time Intelligence`, 58 unfiltered RLS roles and leftover iLab M. It was built out on 2026-09-18.

## Scope decisions (2026-09-18)

1. **Only `pure_silver` tables, plus the shared master list.** The one exception is `dim_ri_master_list` (see Model). Legacy tables with no silver counterpart are not built: `cdco_jobs`, `cdco_application_id`, `Monday Data Extract`, `pure_tables` (a local Excel schema map for dev pages), and `dim_application_status`.
2. **Pages are the legacy visible set:** Summary, Users, Services and Awards Supported. The skeleton's empty Equipment page became Awards Supported. The legacy hidden dev pages (Publication, Page 1/4/5) were not carried over, so no publication facts are loaded: `fact_publication` (2.6M rows) and `fact_journal_metrics` (10.4M rows) stay out of the model.
3. **No RLS.** All 58 skeleton roles were removed. They had no filters, so every member saw everything anyway, and the legacy report had no RLS either. Facility-level RLS needs `facility_id`, which silver dropped (see [[Pure Silver Pipeline#Shape of the thing]]). Revisit when MFP and CDCO data land in Databricks.
4. **The `facility_id` split is dropped** from the Summary page's platform pivot. The pivot keeps all its measures by year.
5. **Silver column names are used as-is** (`UPPER_SNAKE_CASE`). There is no renaming layer in Power Query; DAX and visual field references were rewritten instead.
6. **External-organisation ids are text.** `dim_external_organisation[EXTERNAL_ORGANISATION_ID]` is `STRING` in silver. The fact's `APPLICANT_EXT_ORG_ID` and `FUNDER_ID` are `LONG`, so the `fact_application` partition casts both to text (`Text.From`, nulls kept) to match the dimension, rather than casting the dimension key down.

## Model

The connection is the standard `Databricks_MACE` record plus `get_table_from_mace(table, schema)`. `Databricks_MACE[database]` is `"pure_silver"`, and every partition calls `get_table_from_mace("<table>", Databricks_MACE[database])` followed by `Table.SelectColumns` to only the columns the report uses. Everything is Import mode.

| Report table | `pure_silver` source | Rows (2026-09-18) | Why it's here |
|---|---|---:|---|
| `fact_application` | `fact_application` | 711,676 | every measure |
| `dim_upm_application` | `dim_upm_application` | 96,726 | `Charge($)` summarises by it (the legacy report's `dim_application`) |
| `dim_upm_award` | `dim_upm_award` | 40,884 | `awards_supported`, the award table |
| `dim_research_organisation` | same | 1,323 | PVCRI-code breakdowns; `Monash user` |
| `dim_external_organisation` | same | 56,794 | funder breakdowns; `External user` and the researcher-type splits |
| `dim_org_type` | same | 9 | Users and Service booking by organisation type |
| `dim_applicant_role` | same | 7 | `Research group` (role 7236) |
| `dim_researcher` | same | 680,193 | top researchers by `Charge($)` |
| `calendar`, `Time Intelligence`, `key_measures` | generated in the report | — | as before |

**`dim_ri_master_list`** (added 2026-09-18, at the user's request) is the one table that isn't from `pure_silver`. It reads `ri_lakehouse.ri_master_list` (117 active rows) through the `ri_master_list` source query, the same table and pattern the other seven reports use; it was chosen over `standalone_silver.ri_master_list` because `ri_lakehouse` only gets rows that passed validation. Its 24-column definition is copied from `ri_pbi_ilab_utilisation`.

It is **loaded but not related to anything**, deliberately. `pure_silver.fact_application` carries no facility, capability or equipment column, so there is no key to join on:
- `PURE_ORGANISATION_ID` is null on every row.
- `PURE_FACILITY_ID` matches `pure_silver.dim_equipment.EQUIPMENT_ID` (41 of 117 rows), but no application references equipment. `PURE_FACILITY_ID` also repeats across nodes (20 MARP rows share `7526812`), so even that join would be many-to-many.

The table is staged for facility RLS and a platform slicer once a facility key reaches silver.

`dim_research_group` is in silver but not loaded: the legacy report related it to the fact, but no visual or measure read it.

**Relationships**, all single-direction many-to-one:
- `fact_application` joins to each dimension above on its id, and to `calendar` on `APPLICATION_DATE`.
- `FUNDER_ID` → `dim_external_organisation` is the one inactive relationship; `APPLICANT_EXT_ORG_ID` is the active one.
- The legacy `APPLICANT_INT_ORG_ID` → `dim_research_organisation` relationship was many-to-many. It is many-to-one now because `RESEARCH_ORGANISATION_ID` is unique in silver.
- Every dimension key was checked unique on 2026-09-18.

**Measures**: the 13 legacy `fact_application` measures were ported with upper-cased column names and otherwise unchanged logic:
- `Industry partners`, `Monash user`, `External user`, `Users`
- `Service booking`, `Charge($)`
- `Ext Res/Acad Researchers (D)`, `Ind/Govt Researchers (D)`, `Research group`
- `applications`, `count_fact`, `Awards (D)`, `awards_supported`

`Industry partners` now excludes `"-2"` as text: 343,076 fact rows carry the `-2` "no external organisation" sentinel. `Publication` was dropped with the publication facts. The legacy Awards Supported page's "Last completion date" card pointed at a measure that doesn't exist, so it was not carried over.

## Report

| Page | Visuals |
|---|---|
| Summary | one multi-value KPI card (Users, Research group, Industry partners, Service booking, Awards, Awards supported $) replacing six legacy single-value cards; the "Platform Summary" pivot by year |
| Users | Charge($) by external organisation; Users and Research group by year × time-intelligence item; Users by year × organisation type; Monash user by year × PVCRI code; top researchers by Charge($) |
| Services | Service booking by year × PVCRI code, by year × organisation type, and by year × time-intelligence item; top researchers by Charge($) |
| Awards Supported | Awards by year; awards_supported by year and by funder; award table (award × funder × amount) |

The visuals were copied from the legacy PBIR, with field references rewritten:
- `dim_application` → `dim_upm_application`
- `external_organisation` → `dim_external_organisation`; the legacy Users pivot referenced a table name that doesn't exist
- `Time intelligence.Name` → `Time Intelligence.Formula`
- lower-case column names → upper case

The skeleton's Monash header, footer, logo and theme were kept. The footer now reads "Data sourced from Pure (pure_silver)".

## Gotchas

- **Rows with no application date fall off every year axis.** 37,224 `fact_application` rows have a null `APPLICATION_DATE`, and the calendar runs 2000-01-01 to 2026-12-31 (`StartDate` / `EndDate` parameters). Pre-2000 applications also fall outside it. The legacy report had the same shape.
- **Names render upper case.** Silver upper-cases every string, so researcher and organisation names display in capitals. This was accepted in [[Pure Silver Pipeline#Shape of the thing]], not patched in the report.
- **`powerbi-desktop open` can't find the Store install of Power BI Desktop.** Set `PBI_DESKTOP_PATH` to `C:\Program Files\WindowsApps\Microsoft.MicrosoftPowerBIDesktop_<version>_x64__8wekyb3d8bbwe\bin\PBIDesktop.exe` first.
- **`databricks api post /api/2.0/...` from Git Bash returns `Error: Not Found`.** MSYS rewrites the leading-slash path into a Windows path. Prefix the command with `MSYS_NO_PATHCONV=1`.
- **The theme file fails `powerbi-report-author validate`** (a theme name mismatch, and unknown `outspacePane` / `filterCard` objects). It is byte-identical to the one in `ri_pbi_ilab_utilisation`, which renders fine, so the errors were left alone.

## Parity

> [!note] Point-in-time check, 2026-09-18, after the first refresh against `pure_silver`
> This compares the Summary page's Platform Summary pivot, as rendered in Desktop, with SQL run on `pure_silver.fact_application` grouped by `year(APPLICATION_DATE)`. Every value matched exactly. "Users" in the report equals Monash user + External user, so the SQL column shown is that sum.
>
> | Year | Monash user (PBI = SQL) | Users (PBI) | Monash + External (SQL) | Service booking (PBI = SQL) | Industry partners (PBI = SQL) |
> |---|---:|---:|---:|---:|---:|
> | 2023 | 3,688 | 10,397 | 3,688 + 6,709 | 1,723 | 1,797 |
> | 2024 | 4,096 | 13,196 | 4,096 + 9,100 | 1,469 | 2,355 |
> | 2025 | 4,133 | 13,387 | 4,133 + 9,254 | 1,488 | 2,355 |
> | 2026 | 3,317 | 8,924 | 3,317 + 5,607 | 642 | 1,318 |
>
> `Awards (D)` by year (Awards Supported page: 1.7K, 1.5K, 1.5K, 0.6K for 2023–2026) agrees with SQL's 1,732 / 1,471 / 1,499 / 646 at the chart's rounding.
>
> SQL used for the baseline:
>
> ```sql
> SELECT year(APPLICATION_DATE) AS yr,
>   count(DISTINCT PERSON_ID) AS monash_user,
>   count(DISTINCT EXTERNAL_PERSON_ID) AS external_user,
>   count(DISTINCT PROJECT_ID) AS service_booking,
>   count(DISTINCT AWARD_ID) AS awards,
>   count(DISTINCT CASE WHEN APPLICANT_EXT_ORG_ID <> -2 THEN APPLICANT_EXT_ORG_ID END) AS industry_partners
> FROM pen_research_infrastructure_insights_prd.pure_silver.fact_application
> GROUP BY 1 ORDER BY 1
> ```
>
> This checks the port against its own source, not against the legacy report's numbers. The legacy report was not refreshed for comparison.

## Open items

- `dim_ri_master_list` has no relationship until a facility key reaches `pure_silver.fact_application`.
- **Awards supported by Funding organisation groups by the applicant's external organisation, not the funder.** It follows the active `APPLICANT_EXT_ORG_ID` relationship; `FUNDER_ID` is the inactive one. This is carried over from the legacy report. It is why "(Blank)" is the largest bar ($3.66bn on 2026-09-18) and why the award table shows blank funder rows. Fixing it means `USERELATIONSHIP` on `FUNDER_ID` inside `awards_supported`, which changes the legacy numbers, so it's a decision for the report owner.
- The header title ("RI Non-iLab Utilisation") doesn't render; only the page-name subtitle does.
- The PBIP is uncommitted in the `ri_pbi_non_ilab_utilisation` sub-repo; only `README.md` is committed there.
- There is no RLS and no facility breakdown until `facility_id` returns to silver.
- `pure_silver` is still built by hand with no schedule, so the report is only as fresh as the last manual run.

## See also

- [[Overview|RI PBI Production]] — the report sits in that workspace as an eighth sub-repo
- [[iLab Utilisation]] — the report this one's skeleton was copied from, and the source of its `dim_ri_master_list` definition
- [[Projects/Databricks/Overview|Databricks]]
- [[Pure Silver Pipeline]] — the layer this report reads, and the cutover checklist it followed
- [[Pure Bronze Pipeline]]
- [[Databricks Conventions]]
- [[Databricks Migration State]]
