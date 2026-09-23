# Pure Silver Pipeline

`pure_silver` (catalog `pen_research_infrastructure_insights_prd`) is the cleaned, conformed layer built from [[Pure Bronze Pipeline|pure_bronze]] — 15 tables, porting the Power Query (M) logic of the old `ri_non_ilab` report (`ri_pbi_reports (old)/ri_non_ilab`): the `ri_non_ilab_pure\fetch` → `ri_non_ilab_pure\preprocess` query groups in `ri_non_ilab.SemanticModel/definition/expressions.tmdl`, plus the production-partition steps in `tables/*.tmdl`. It is the second rung of the Pure re-implementation, not a cutover — the report still reads `ri_lakehouse`.

The table set is the report's, not bronze's: 12 silver tables have a same-name bronze table; 3 are derived in silver (`dim_researcher`, `dim_research_group`, `dim_org_type`); and 3 bronze tables have no silver counterpart because the report never reads them directly — `classification` (consumed inside bronze by `dim_applicant_role`), and `dim_person` / `dim_externalperson` (consumed here only through `dim_researcher`).

## Shape of the thing

**Scope decisions (2026-09-18):**

1. All 15 tables come across: 8 with ported preprocess logic, 7 pass-throughs (7 ported + 8 pass-throughs since `dim_upm_award` became a pass-through on 2026-09-23) — one schema the report can cut over to as a whole, not a partial rebuild.
2. `facility_id` is dropped from the application dimension. The report built it in M from three sources — MMIC (title contains "MMIC"), MFP (an Excel workbook on the M: Google Shared Drive, `PQMS4-MFP-eFRM-0032_MFP_budget_invoices_records.xlsx`, via `combined_years`), and CDCO (a Monday Google Sheet, `cdco_jobs`) — and only MMIC is derivable from Databricks data today; MFP and CDCO have no bronze tables. `facility_id` returns once those exist. M quirk carried in the note rather than the code: tags concatenate with no delimiter, e.g. `"MMICMFP"`.
3. Naming follows bronze where a bronze table already exists (`dim_upm_application`, not the report's `dim_application`); tables newly derived in silver take the report's own names (`dim_researcher`, `dim_research_group`, `dim_org_type`). This keeps "same name across layers" true going forward from wherever a name first appears.
4. Silver conventions win over M fidelity where they conflict: every non-`_` string column is trimmed and uppercased (the report only uppercased external-organisation columns), ids keep bronze's types (M casts `EXTERNAL_ORGANISATION_ID` to text; bronze is already `STRING`), and columns are `UPPER_SNAKE_CASE`. Some report visuals will change appearance at cutover — names rendering uppercase, for one — and that's accepted rather than patched around.

Other defaults: `fact_journal_metrics` passes through **without** the report's `Custom = coalesce(double_value, integer_value)` keep-null filter — it looks inverted; see [[Pure Bronze Pipeline#Legacy bugs carried over]]. `calendar` and `dim_application_status`, both report-generated static tables, are out of scope — they have no upstream table to port. `_`-prefixed bronze lineage columns are carried through unchanged, never value-transformed, with two exceptions: `dim_researcher` carries none (it unions two differently-shaped sources with no single lineage story), and `dim_org_type` / `dim_research_group` carry none (both are silver-derived, not read from bronze).

Notebooks live under `/Workspace/Users/milinda.abayawardana@monash.edu/ri_pure/`, alongside the bronze notebooks: `pure_silver_common` plus 15 `<table>_silver` plus 15 `<table>_silver_validate` — 31 notebooks. Run by hand as one-off serverless `databricks jobs submit` runs; no job yet. No Power BI changes.

## Table inventory

| Silver table | Source | Ports (M step) | Key |
|---|---|---|---|
| `dim_upm_application` | `pure_bronze.dim_upm_application` | `preprocess_upm_application` | `APPLICATION_ID` |
| `dim_upm_award` | `pure_bronze.dim_upm_award` | pass-through (was `preprocess_upm_award` until 2026-09-23 — bronze now comes from BIM `research_award`, see [[Pure Bronze Pipeline#dim_upm_award moved to BIM, 2026-09-23]]) | `AWARD_ID` |
| `dim_research_organisation` | `pure_bronze.dim_research_organisation` | `preprocess_research_organisation` | `RESEARCH_ORGANISATION_ID` |
| `dim_external_organisation` | `pure_bronze.dim_external_organisation` | `preprocess_external_organisation` | `EXTERNAL_ORGANISATION_ID` (string) |
| `dim_org_type` | `pure_silver.dim_external_organisation` | `preprocess_org_type` | `EXTERNAL_ORGANISATION_TYPE` |
| `fact_application` | `pure_bronze.fact_application` | `preprocess_fact_application` + production partition | none — duplicates kept |
| `dim_research_group` | `pure_silver.fact_application` | `preprocess_dim_research_group` | `RESEARCHER_ID` |
| `dim_researcher` | `pure_bronze.dim_person` ∪ `dim_externalperson` | `preprocess_person` + `preprocess_externalperson` + `dim_researcher` partition (`Table.Combine`) | `RESEARCHER_ID` |
| `dim_applicant_role` | `pure_bronze.dim_applicant_role` | pass-through | `PERSON_ROLE_ID` |
| `dim_equipment` | `pure_bronze.dim_equipment` | pass-through | `EQUIPMENT_ID` |
| `dim_journal` | `pure_bronze.dim_journal` | pass-through | `JOURNAL_ID` |
| `dim_publication` | `pure_bronze.dim_publication` | pass-through | `PUBLICATION_ID` |
| `dim_country` | `pure_bronze.dim_country` | pass-through | `(_SURROGATE_KEY, CLASSIFICATION_ID)` |
| `fact_publication` | `pure_bronze.fact_publication` | pass-through | none — duplicates kept |
| `fact_journal_metrics` | `pure_bronze.fact_journal_metrics` | pass-through | `(JOURNAL_ID, JM_LIST_INDEX, ID, NAME, LIST_INDEX)` |

## Build order

Two waves:

1. The 13 tables read directly from `pure_bronze`.
2. `dim_org_type` (needs `pure_silver.dim_external_organisation`) and `dim_research_group` (needs `pure_silver.fact_application`).

## The shared helper

Every `ri_pure/<table>_silver` and `<table>_silver_validate` notebook pulls in `pure_silver_common` with `%run ./pure_silver_common` — the **first shared-helper pattern in the catalog**; every bronze notebook to date repeats its own build/validate code. It defines:

- `uppercase_columns(df)` — renames every column upper case, raising if that would collide.
- `normalise_strings(df)` — trims and uppercases every non-`_` string column, run last in every build.
- `write_silver(df, table, key=None)` — guards the key as unique and not-null (or, with no key, reports an exact-duplicate count) before `overwrite` with `overwriteSchema`, and returns the row count.
- `check_structure(df, table, key=None)` — the validate-side structural checks: non-empty, columns uppercase, key unique/not-null, and every non-`_` string column already trimmed-upper.
- `check_multiset_parity(silver, expected, table)` — `exceptAll` both ways, raising with a five-row sample on mismatch.

The point of sharing it: validates prove parity by applying the *same* normalisation to bronze that the build applied, so a validate can never pass against a rule the build has quietly stopped following.

## Validation

- **Pass-through tables** validate every column: schema equality by name/type/position, plus `check_multiset_parity` against `normalise_strings(bronze)` in both directions.
- **Transforming 1:1 tables** (`dim_upm_application`, `dim_research_organisation`, `dim_external_organisation`; `dim_upm_award` until 2026-09-23, now a pass-through) validate row count plus key-set parity against bronze, plus per-table rule assertions (see Gotchas below).
- **`fact_application`** has no key, so it validates exact multiset parity against an expected frame the validate recomputes independently from bronze (same two derivations, same normalisation).
- **Derived tables** validate set equality against what they derive from: `dim_org_type` against the distinct types of silver `dim_external_organisation` plus `MONASH UNIVERSITY`; `dim_research_group` against the PCI projection of silver `fact_application`; `dim_researcher` by key uniqueness and row count = `dim_person` + `dim_externalperson`.

This follows [[Databricks Conventions]]'s silver-validate rule: a pass-through silver validates every column; a transforming silver validates surrogate/key parity, because whole-row equality with bronze cannot hold once columns are ported.

## Deviations from the report

| Deviation | Why |
|---|---|
| All non-`_` string values trimmed + uppercased | The report only uppercased external-organisation columns; silver's blanket rule beats M fidelity per the scope decision above. |
| Ids keep bronze's types, not the M casts | M casts `EXTERNAL_ORGANISATION_ID` to text; bronze is already `STRING`, so the cast is a no-op here. |
| `facility_id` dropped from the application dimension | MFP and CDCO, two of its three M sources, have no bronze table yet. |
| `fact_journal_metrics`'s `Custom = coalesce(...)` keep-null filter not applied | The filter looks inverted against its own stated intent — see [[Pure Bronze Pipeline#Legacy bugs carried over]]. |
| ANZSIC code split by tokenising the raw code, not the M's "before second space, then split" | Algebraically identical result without the throwaway intermediate column — confirmed against all 56,637 non-null codes. |
| `calendar`, `dim_application_status` out of scope | Both are report-generated static tables with no upstream source to port. |

## Gotchas

- **`AWARD_TYPE_CLASSIFICATION` changed meaning (2026-09-23):** it now carries BIM `AWARD_TYPE` (GRANT, CONTRACT RESEARCH, FELLOWSHIP, …) instead of the constant `AWARD`, so report visuals on it will show real types. `fact_application`'s award rows now come from an `application_id` join — see [[Pure Bronze Pipeline#dim_upm_award moved to BIM, 2026-09-23]].

- **`FULL_NAME` (dim_researcher):** normalising each name part and then concatenating is not the same as concatenating raw parts and then trimming/uppercasing the whole string, whenever a part carries leading/trailing whitespace next to the join point — the second form leaves a doubled or ragged space. The two definitions disagree on 3 `dim_person` rows and 11,601 `dim_externalperson` rows at probe time (11,558 against the built table, per the validate). Silver normalises parts first, then joins with exactly one space, and is null if either part is null — matching M's `&` operator. The validate checks this and reports the alternative definition's mismatch count.
- **ANZSIC split (dim_external_organisation):** `EXTERNAL_ORGANISATION_PRIMARY_ANZSIC2006_CODE` (e.g. `"M 69 Professional, Scientific and Technical Services …"`) splits on space into `EXTERNAL_ORGANISATION_ANZSIC2006_DIVISION_CODE` (string, token 1, e.g. `"M"`) and `EXTERNAL_ORGANISATION_ANZSIC2006_SUBDIVISION_CODE` (`BIGINT` via `try_cast`, token 2, e.g. `69`) — replacing the report's unused `" - Copy.1"` / `" - Copy.2"` columns (no visual referenced them). 157 of 56,794 rows have a null code and both derived columns are null for those; 0 of the 56,637 non-null codes fail the integer parse on token 2.
- **dim_country full-join shape:** carried over from bronze — `(_SURROGATE_KEY, CLASSIFICATION_ID)` is unique and never both null, asserted explicitly in the validate rather than assumed.
- **Duplicate rows kept, not deduped:** `fact_application` (7,806 exact duplicates out of 711,676) and `fact_publication` (359 exact duplicates out of 2,580,757) both write with no key, because the legacy source data genuinely fans out this way — see [[Pure Bronze Pipeline#Legacy bugs carried over]]. `write_silver` reports the duplicate count rather than raising.
- **dim_research_organisation's PVCRI code:** `PRIMARY_ORGANISATION_UNIT_PVCRI_CODE` is derived by 10 chained substring replacements on the *original-case* unit name (MNHS, ARTS, ADA, BUSECO, IT, ENG, SCI, PHARM, COO, DVCRE) before the column is uppercased; 11 other units (Faculty of Education, Faculty of Law, Office of the VC & President, Other, etc.) fall through as their own uppercased name, matching the report. Used in 12 visual fields.

## First run, 2026-09-18

> [!note] Point-in-time snapshot — first manual run of all 15 build + 15 validate notebooks, 2026-09-18. All passed first run.
>
> | Silver table | Rows | Validate result |
> |---|---:|---|
> | dim_upm_application | 96,726 | key set = bronze |
> | dim_upm_award | 40,884 | key set = bronze |
> | dim_research_organisation | 1,323 | key set = bronze; 10 PVCRI mappings verified; 21 distinct (unit, code) pairs |
> | dim_external_organisation | 56,794 | key set = bronze; ANZSIC split verified |
> | dim_org_type | 9 | set equality |
> | fact_application | 711,676 | exact multiset parity vs independently recomputed expected |
> | dim_research_group | 16,887 | set equality with silver fact projection |
> | dim_researcher | 680,193 (121,426 + 558,767) | key unique; count = sum of sources |
> | dim_applicant_role | 7 | exact parity with normalised bronze |
> | dim_equipment | 44 | exact |
> | dim_journal | 22,239 | exact |
> | dim_publication | 390,270 | exact |
> | dim_country | 353 | exact |
> | fact_publication | 2,580,757 | exact multiset |
> | fact_journal_metrics | 10,432,538 | exact |

## Cutting the report over

Done as a **new report** on 2026-09-18, not by editing `ri_non_ilab`: `ri_pbi_production/ri_pbi_non_ilab_utilisation` reads `pure_silver` directly, with only the legacy visible pages and only silver tables. See [[Projects/RI PBI Production/Repos/Non-iLab Utilisation/Non-iLab Utilisation|Non-iLab Utilisation]] for what it carries and what it dropped. The legacy report is untouched and still reads `ri_lakehouse`.

The checklist below is what that build followed. It still applies as written if the legacy report itself is ever repointed:

- Change `Databricks_MACE[database]` in `expressions.tmdl` (read by `get_table_from_mace`) from `ri_lakehouse` to `pure_silver`.
- Delete the preprocess steps silver now does for the 8 ported tables — they'd otherwise run twice.
- Fix column-name case in any remaining M or DAX: silver is `UPPER_SNAKE_CASE`; the report currently uses lowercase for most tables.
- Rename the report table `dim_application`'s source to `dim_upm_application`.
- `facility_id` visuals (3 fields) will break until MFP and CDCO have bronze tables of their own.
- Check type alignment on `EXTERNAL_ORGANISATION_ID` relationships from facts — funder-side columns like `FUNDER_ID` are `BIGINT`, but the dimension's key is `STRING`.
- `calendar` and `dim_application_status` stay in the report; they're out of scope here.

## Scheduling it

Not done. When it happens: a job ordered by the [[#Build order]] waves above, each build followed by its matching validate, scheduled to run after the `pure_bronze` job.

## Open items

- The `ri_pure/` silver notebooks are not in any git repo, same risk as the bronze notebooks — they exist only in the workspace, with no version history or review trail.
- No scheduled job yet — notebooks are run by hand.
- The legacy `ri_non_ilab` report has not been cut over and still reads `ri_lakehouse` (via `ri_lakehouse_prod`). Its replacement, [[Projects/RI PBI Production/Repos/Non-iLab Utilisation/Non-iLab Utilisation|Non-iLab Utilisation]], reads `pure_silver` but is not yet published.
- `facility_id` is missing from `dim_upm_application` until MFP and CDCO land in Databricks.
- On 2026-09-18 the user's identity briefly lost `USE CATALOG` on `pen_research_infrastructure_insights_prd` (`INSUFFICIENT_PERMISSIONS … USE CATALOG`, seen from the SQL warehouse, notebook runs, and `databricks grants get-effective`); it was restored within the same session, via group `Lakehouse-PEN-Research-Infrastructure-Insights-users` (`BROWSE`, `CREATE_SCHEMA`, `USE_CATALOG`). Distinct from the VPN-down error. The SQL Statement API against warehouse `5cc645cded66580f` didn't work while access was out, so notebooks were used for all probes during the incident.

## See also

- [[Overview|Databricks]]
- [[Databricks Conventions]]
- [[Databricks Migration State]]
- [[Pure Bronze Pipeline]] — the layer this reads from, and the `ri_non_ilab` scope this ports
- [[Projects/RI PBI Production/Overview|RI PBI Production]] — the seven reports this catalog also serves; `ri_non_ilab` sits outside that set
