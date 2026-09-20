# iLab Utilisation Gotchas

Known defects, dead code and open questions in [[iLab Utilisation]]. Everything here is **recorded, not repaired** — listed so it isn't rediscovered, mistaken for a convention, or "corrected" by accident.

> [!warning] Point-in-time snapshot
> Verified against TMDL on **2026-09-01**; dead-code table re-checked against the [[ri_pbi_ilab_utilisation semantic model|2026-09-15 export]] (the `dim_facility_master_list` → `dim_ri_master_list` rename noted above). Re-check before acting on any specific item.

> [!note] Reconciled against [[ri_pbi_ilab_utilisation semantic model]] on 2026-09-19 (`ri_pbi_ilab_utilisation` @ `f8c4a836`)
> Checked against the export: the orphaned-chain table and both disconnected parameters exactly match the expressions no table reaches. The measure-level items are in the DAX: `_visible_names`, `__visible_quaters`, the 500-hour capacity and `Industry Partners (D)` on `dim_ilab_lab`. Function bodies (the `File.Contents` calls), parameter metadata, roles and hidden flags aren't in the export and rest on the TMDL reads.

## The `model.tmdl` rename trap

**This is the live trap in this repo.** Roles are not discovered from the filesystem: `model.tmdl` carries an explicit `ref role <Name>` line for each one. Renaming a role file without updating its `ref role` line leaves a **dangling reference**, and adding a role file without adding a line leaves the role inert.

It has already happened once here. The `HMST` → `MMIC-HMST` rename needed a follow-up commit (`10070ce`) purely to repair the reference it left behind.

Currently clean: **58 `ref role` lines, 58 role files, no dangling references and none unreferenced** (verified 2026-09-01). Any role work in this repo should re-check that pairing before committing — the model does not complain, it just silently loses a role.

## No hardcoded local-file path

Worth stating explicitly rather than leaving as an absence, because three repos in the suite *do* have this problem and it is the first thing to suspect on a refresh failure.

**This repo does not.** Two M functions call `File.Contents` — `process_iLab` and `preprocess_grc_equipment` — but both take the path as a **function parameter** rather than embedding an absolute path, and **neither is wired into a live table partition.** So neither the [[Publication]]/[[Risk]] stale-path failure nor [[Survey]]'s dormant-parameter case applies here. See [[Shared Conventions]] for the suite-wide picture.

## Dead code

Nothing here carries a `queryGroup: decomissioned` label — unlike [[Asset]] and [[Risk]] — so these read as live until you trace them to a table that doesn't exist.

> [!note] Four entries removed in the 2026-09-14 export
> `base_facility`, `base_labs`, `base_external_institutes_adb` and `source_external_organisation` were deleted from `expressions.tmdl` at `ri_pbi_ilab_utilisation` @ `1f015320` — they no longer appear in [[ri_pbi_ilab_utilisation semantic model]]'s expression inventory. Their upstream `source_facility_adb`, `source_labs` and `source_external_institutes_adb` queries were **not** removed and remain in the table below, now feeding nothing at all rather than feeding an already-dead `base_*` step.

**Orphaned M chains**, defined in `expressions.tmdl` but consumed by no live table:

| Chain | Note |
|---|---|
| `source_facility_adb` | Reads `dim_ilab_facility` from `ilab_3y`. Previously fed `base_facility` (removed 2026-09-14); superseded by `dim_ri_master_list` (renamed from `dim_facility_master_list` on 2026-09-15). |
| `source_labs` | Reads `labs` from `ilab_3y`. Previously fed `base_labs`, removed 2026-09-14. |
| `source_external_institutes_adb` | Reads `external_institutes` from `ilab_3y`. Previously fed `base_external_institutes_adb`, removed 2026-09-14. |
| ~~`source_external_organisation`~~ **(removed 2026-09-14)** | Hand-rolled its own `Databricks.Catalogs(...)` call against `ri_lakehouse.dim_external_organisation`, hardcoding host and warehouse IDs instead of reusing `Databricks_MACE`/`get_table_from_mace`. Was unused **and** inconsistent with the shared-connection convention. |
| `preprocess_grc_equipment` (`DEV\grc_equipment`) | Reads a "Cryo Equipment Register" Excel workbook. Looks like a prepared-but-unshipped feature for tracking physical cryo equipment. |
| `process_iLab` (`Functions`) | A CSV parser shaped like the pre-Databricks manual iLab export. Superseded by the Databricks path. |
| `get_random_table`, `lowercase_col_names` (`Functions`) | Generic utilities, never called. |

**Disconnected parameters**, both leftovers from that pre-Databricks CSV workflow and consumed by no live query:

- `data_path` — default `null`, and its meta record contains a literal `DefaultValue=...` (three dots, not a value). A stale placeholder rather than an intended default.
- `file_type` — `List={"ilab_master.csv","ilab_sample.csv"}`, default `"ilab_sample.csv"`.

**Dead code inside live definitions:**

- `filter_assest` computes a `_visible_names` variable it never references.
- `Researchers (D)` keeps two commented-out alternatives inline, referencing a table alias `ilab` that no longer exists.
- The `CY` calculation item carries commented-out disabled logic.
- `get_table_from_mace` keeps its own earlier single-argument version commented out **above** the live two-argument one — the first definition you meet reading the file is the dead one.

## Stale by date

### The MARP custodianship split has passed

`CENTRAL-ADMIN` and `MNHS-ADMIN` carve MARP rows at **2026-01-01**, MNHS holding history and CENTRAL taking everything from 2026 on. That date is now in the past, so the split no longer affects new data — but the logic is still live and still hides historical rows from each role.

Worth confirming with the model owner whether the carve-out should stay. If either filter is edited, the other must still complement it. Full detail in [[iLab Utilisation RLS]].

### `DDP` filters a capability code that may not exist

`DDP` filters `CAPABILITY_CODE IN {"DDP"}`, which does not appear in the master-list extract (nearest: `MDDP`). If it is absent from live data too, the role is deny-all and reports nothing. The one flagged role in this repo that no rename pass resolved — see [[iLab Utilisation RLS]].

## RLS shape defects

Recorded in full in [[iLab Utilisation RLS]]; repeated here so they surface in a defect sweep:

- **`ENG-DMSE`** and **`MGBP-BI`** each carry only one of the two expected `tablePermission` filters, leaving `dim_ilab_services` unfiltered for those roles. Potential over-exposure — and note that [[RLS Role Naming Normalization]] describes this as fixed for `ENG-DMSE`, which it is not.
- **`ENG-DMAE`** filters `fact_ilab` directly instead of `dim_ilab_services`. Looks intentional, but it is a shape nothing else in the suite uses.

## Convention deviations

- **`Industry Partners (D)` is defined on `dim_ilab_lab`**, not in `Key Measures`, breaking this repo's own centralisation convention. A candidate for relocation; see [[iLab Utilisation Measures]].
- **`Equipment usage (%)` hardcodes a 500-hours-per-equipment-per-quarter capacity.** Not driven by any capacity data. Don't use it for capacity planning without validating the figure.
- **`source_mhp_customer_groups` is a pinned ~140-row table literal.** New labs needing Hudson/SCS grouping must be added by hand; unmatched labs silently fall through to `"NEVER_USED_MHP-MHTP"`. See [[iLab Utilisation Data Model]].

## Cosmetic

- The `calendar` M code names an intermediate step `cal_mon_yeat_int` before renaming it to `cal_mon_year_int`. No functional impact — and note the *column* here is spelled correctly, unlike [[Publication]]'s `Calendar[cal_mon_yeat_int]`, where the typo reached the column name and is now unfixable.
- `Equipment usage (%)` has a variable named `__visible_quaters`.
- Table references mix case — `'calendar'` in some measures, `'CALENDAR'` in others. DAX table names are case-insensitive, so it resolves.

## Nothing is hidden

Not a defect, but it shapes the Fields pane and is easy to misread as curation.

**No table is hidden, and exactly three columns are** — `Parameter Fields` and `Parameter Order` on the disconnected `Parameter` table, and `Ordinal` on `Time Intelligence`. All three are Power BI-generated plumbing. Every business column is exposed, including join keys and the sort-helper columns (`cal_month`, `cal_mon_year_int`, `Quarter_num`) that convention would normally hide.

[[Asset]] takes the opposite approach. Don't port hiding assumptions in either direction.

## See also

- [[iLab Utilisation]] — the repo entry note
- [[iLab Utilisation RLS]] — the role-shape defects and the `DDP` question in full
- [[iLab Utilisation Data Model]] — the dead chains in their source-flow context
- [[iLab Utilisation Measures]] — the capacity assumption and the misplaced measure
- [[Shared Conventions]] — the suite-wide hardcoded-path gotcha this repo avoids
- **Derived layer** (`graphify/`, never hand-edited): [[_COMMUNITY_GRC Equipment Preprocessing]], [[preprocess_grc_equipment]], `File.Contents` *(no iLab node; the graph's only `File.Contents` is Asset's)*, `Hardcoded Local File Dependencies` *(no node since export `0c73b0cf`; it split into per-report nodes for Publication, Risk and Survey, none for iLab)*, `base_external_institutes_adb` *(no node since export `51b1e84`)*, [[source_external_institutes_adb]], `source_external_organisation` *(no node since export `51b1e84`)*, `base_facility` *(no iLab node; the graph's `base_facility` is Survey's)*, `base_labs` *(no node since export `51b1e84`)*, [[get_random_table]], [[process_iLab]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[Databricks_MACE_4]], [[get_table_from_mace_4]], [[get_table_from_mace_4]], [[source_facility_adb]], [[source_labs]], [[source_mhp_customer_groups]], [[lowercase_col_names_2]], [[file_type]], [[data_path_3]], [[dim_ilab_lab]], [[dim_ilab_services]], [[dim_facility_master_list]]
