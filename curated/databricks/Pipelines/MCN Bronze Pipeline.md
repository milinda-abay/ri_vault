# MCN Bronze Pipeline

`mcn_bronze` (catalog `pen_research_infrastructure_insights_prd`) holds the Melbourne Centre for Nanofabrication's booking-system usage data, built **2026-09-23**. The source is not a system MCN exposes to us. It is their KPI workbook, `MCN_User hours_KPI template_Cumulative_<FY>_rev<n>.xlsx`, which carries the raw export from their booking system (**ACLS**) and is dropped by hand into the volume `mcn_bronze.input_data`. The first file loaded was `…_Cumulative_2027_rev1.xlsx` (FY 2025/26 plus July 2026).

## Tables

| Table | Source | Load | Key |
|---|---|---|---|
| `fact_user_hours` | `Data` columns A–K + N | snapshot overwrite | none; `_SOURCE_ROW_NUMBER` traces each row to its Excel row |
| `dim_facility` | `Legacy Facility Names` A–H | SCD2 | `FACILITY` |
| `dim_platform` · `dim_resource_class` · `dim_equipment_tier` · `dim_capability_category` | `Legacy Facility Names` column J, one table per section | SCD2 | the single value column |

Notebooks live in `/Users/milinda.abayawardana@monash.edu/ri_mcn/`, with local source in `C:\Users\maba0001\projects\ri_mcn\notebooks\`:
- `dim_facility_bronze` writes all five dims, the same multi-table shape as `remap_tables_bronze`
- `dim_facility_bronze_validate`
- `fact_user_hours_bronze`
- `fact_user_hours_bronze_validate`

Job **`mcn_bronze_tables`** (`533981642041852`) runs them in that order on serverless. It is **unscheduled**, because the file arrives by hand. Drop the new file in the volume, then set the `source_file` widget/parameter, or overwrite the default path.

## Why bronze keeps only A–N of `Data`, not A–X

The request was framed as "the ACLS output is columns A–K and P–X". Profiling showed that **only A–N are values; O–X are Excel formulas.** Loading P–X would have put Excel's cached derivations into bronze as if they were source data. So bronze keeps the ACLS columns A–K plus `Month` (N), which is the only date and which FY is computed from. The formulas below are the **silver spec**, reproducing what the workbook does:

| Column | Formula (paraphrased) |
|---|---|
| O `Adj` | `LEFT(Resource, 11)`, a pivot helper with no business meaning |
| P `FY` | `Month` before July → `(Y-1)/Y`, otherwise `Y/(Y+1)` |
| Q `Legacy Facility Name 2` | `VLOOKUP(Resource, Legacy!A:H, 2)`, falling back to `Resource` when not found → `dim_facility.FACILITY_LEGACY_NAME` |
| R `Platform` | `VLOOKUP(Legacy Facility Name 2, Legacy!B:H, 3)`. Note: keyed on **col B**, not A, so the first B match wins, and there's **no fallback**, hence `#N/A` |
| S / T / V / W | Resource Class / Core / Equipment Tier / Capability Category = `VLOOKUP(Resource, Legacy!A:H, 5/6/7/8)`, falling back to `Resource` when not found (hence rows with Resource Class = `CH3 Potentiostat`) |
| U `TA` | `"TA"` if `Account` contains `Ambass` (Tech-Ambassador accounts), else `"Other"` |
| X `Activity Type` | User `Scheduled Service`/`Unscheduled Service` → `Service (>2wks)` if Booked Hours > 80, otherwise `Service`. Else `Account = "MCN Staff"` → `MCN Staff Acct`. Else `Usage` |

L `User definition` (Academic/Industry) and M `Facility and Service Type` are values, but they were left out. L is a hand classification that silver can derive from `Charge Category`. M is a concatenation whose cached values are stale in places (the last row's M names a different resource and user than its own A/B).

## Why the fact is a snapshot, not SCD2

There is no natural key. Even the full A–N row repeats: the 2027 rev1 file has 8 exact duplicates, which are legitimate repeat monthly aggregates. Resource × user × account × month × training still has 105 duplicate keys. The file is also cumulative and re-issued whole, so each run replaces the table. That is the snapshot exception in [[Databricks Conventions]]. Consequence: bronze keeps **no history of the fact**. If ACLS silently restates a past month, the previous figure is gone. If that ever matters, the fallback is to append each load under a `_LOAD_ID`.

## Known data-quality flags (surfaced as WARN, not fixed)

- **Resources missing from the mapping:** `CH3 Potentiostat`, `PICO DEVELOP STATION`. This is the `#N/A` Platform in the workbook.
- **`Staff Assisstance`** (a typo in mapping col H) vs **`Staff Assistance`** (the col-J list).
- **`Fumehood for HF etch`** is an exact duplicate row in the mapping. Bronze collapses it, and a *conflicting* duplicate would fail the load.
- **`Training Booking` = `24`** on one row (`Evaporator E-beam Angstrom Engineering`, Oct 2025), where it should be `Training` or blank.
- **Mixed cell types** in one column: `Account Discount (%)` holds `0` and `'0.00'`, `Facility Charge/Hour` has text `'0'`. Bronze types these to `decimal(12,2)` via `Decimal(str(v))`, and fails on anything with more than 2 decimal places.
- **Non-breaking spaces** in names (e.g. `3D Scanner Artec Spider\u00a0`). They're stripped before the trim, otherwise joins would miss silently.

## Validation

- `dim_facility_bronze_validate` runs the standard SCD2 structural checks (copied from `remap_tables_bronze_validate`). It also checks each `dim_facility` attribute against its column-J vocabulary, as WARN.
- `fact_user_hours_bronze_validate` checks **parity with the source**: it re-reads the workbook's raw cells independently, and row count, Σ booked hours and Σ charges must match exactly. It also checks that `_SOURCE_ROW_NUMBER` is unique, required columns are not null, and `MONTH` is the 1st. WARNs cover unmapped resources, odd training values, and `CHARGES ≠ rate × hours × (1 − discount%)`.

## See also

- [[Databricks Conventions]] — the rules this follows
- [[Standalone Remap Tables Reference]] — the SCD2 load this reuses verbatim
- [[Pure Bronze Pipeline]] — the other snapshot-exception bronze
