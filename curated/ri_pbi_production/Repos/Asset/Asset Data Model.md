# Asset Data Model

The semantic model behind [[Asset]], defined in `ri_asset.SemanticModel/definition/`. A **single-fact star schema**: one row per SAP General Ledger posting against a capitalised asset, surrounded by dimensions that slice that spend by faculty, cost centre, capability, asset class, age, acquisition value and time.

Verified against TMDL on 2026-09-01.

> [!note] Reconciled against [[ri_pbi_asset semantic model]] on 2026-09-15
> All 11 tables, 9 relationships and 6 measures still match the export. `dim_ri_master_list` widened from 19 to 24 columns — the export now carries the five `_`-prefixed SCD2 metadata columns, same as [[Finance]], [[Publication]] and [[Awards]] — so the table total is 99 columns, not 94, and the dead-expression count dropped from 8 to 7: `dim_platform`, the erroring orphaned query, was removed from `expressions.tmdl` entirely (its graphify node persists only as a stale artifact of the separate graph-snapshot export, not the semantic-model one). Go there for column types, measure DAX and the full Power Query expression inventory. What the export cannot show — hidden flags, `toCardinality`, descriptions, and why any of it is so — is what this note is for; those claims, and the hidden/visible split for the five new SCD2 columns (not yet checked), still rest on the 2026-09-01 TMDL read.
>
> Re-checked against the **2026-09-16** export (`ri_pbi_asset` @ `738401ea`): `graphify/ri_pbi_production/semantic-models/ri_pbi_asset semantic model.md` is byte-identical to the 2026-09-15 version reconciled above, so nothing in this note changed.
>
> Re-checked against the **2026-09-18** export (`ri_pbi_asset` @ `be5342dc`). The sub-repo commit moved, but the exported semantic model is byte-identical to the one reconciled on 2026-09-15, so the tables, relationships, measures and columns above still stand. The graph export renumbered its `_N`-suffixed nodes, so the derived-layer links in See also were re-pointed to the `ri_pbi_asset`-sourced node for each name. Several of them had already pointed at another report's same-named node before this export.
>
> Re-checked 2026-09-19 against the 2026-09-19 export (`ri_pbi_asset` @ `9157aad7`). The sub-repo commit moved, but the export was rendered from the same source graph (`944e789f`) as the `11a98af` export this note was last reconciled against, and every file under `graphify/ri_pbi_production/` apart from `_meta.md` is byte-identical. So nothing the export shows has changed. It also means the export cannot show what that commit did change.

## Shape

| | |
|---|---|
| Tables | 11 — 1 fact, 8 dimensions, 1 date table, 1 measure container |
| Relationships | 9 — all fact→dimension, all active, none bidirectional, 1 flagged `toCardinality: many` |
| Measures | 6 in `key_measures` — 2 visible, 4 hidden |
| Columns | 99 across the 11 tables — 46+ genuinely hidden (the 5 new `dim_ri_master_list` SCD2 columns are not yet checked, see below) |
| Date table | `calendar`, marked for time intelligence, spanning `StartDate`–`EndDate` |
| Report pages | 2 — *Asset Report* (7 visuals) and *Summary* (12 visuals) |

There is no calculation group and no `Time intelligence` table here — [[Asset]] is the one repo in the suite that does its date work with plain measures and a marked date table alone.

## Table inventory

| Table | Rows are | Cols | Visible | Sourced from |
|---|---|---|---|---|
| `fact_sap_asset_gl_mapping` | one SAP GL posting against a capitalised asset | 21 | 7 | `preprocess_sap_asset_gl_mapping` |
| `calendar` | one calendar day | 14 | 1 | `List.Dates(StartDate … )` |
| `dim_gl_code` | one GL account | 2 | 2 | distinct from the fact query |
| `dim_cost_centre` | one cost-centre initial | 2 | 1 | distinct from the fact query |
| `dim_asset_class` | one SAP asset class | 1 | 1 | distinct from the fact query |
| `dim_asset` | one capitalised asset | 2 | 2 | distinct from the fact query |
| `dim_age` | one 5-year age band | 3 | 1 | distinct from the fact query |
| `dim_acquisition_value` | one $100K value band | 3 | 1 | distinct from `preprocess_sap_asset_gl_mapping` |
| `dim_ri_master_list` | one RI capability | 24 | 5+ | `ri_master_list` |
| `dim_finance_fund_centre` | one SAP fund centre | 27 | 27 | `finance_fund_centre` |
| `key_measures` | *(no data — measure container)* | 0 | — | a compressed empty table |

Six of the eight dimensions are **derived from the fact table itself** rather than loaded independently — `Table.SelectColumns` then `Table.Distinct` over a fact column. Only `dim_ri_master_list` and `dim_finance_fund_centre` are genuine external dimensions with their own source query. That is worth knowing before adding a column: a new attribute on `dim_gl_code` has to come from the fact extract or be synthesised in M, because there is no upstream GL-account table to widen.

`dim_acquisition_value` is the odd one out — it sources from `preprocess_sap_asset_gl_mapping` (the pre-fact query) rather than from `fact_sap_asset_gl_mapping` as its five siblings do. The result is the same today, since the fact table is a pass-through of the preprocess query, but the two would diverge the moment a filter were added at the fact step.

## Relationships

All nine run fact to dimension, all active, all single-direction. None is inactive and none is bidirectional, so there are no `USERELATIONSHIP` or `CROSSFILTER` subtleties to hold in mind.

| From | To | Note |
|---|---|---|
| `fact…[GLAccount]` | `dim_gl_code[GLAccount]` | |
| `fact…[cost_centre_group]` | `dim_cost_centre[cost_centre_group]` | first character of `CostCentre` |
| `fact…[AssetClass]` | `dim_asset_class[AssetClass]` | |
| `fact…[AssetNumber]` | `dim_asset[AssetNumber]` | |
| `fact…[age_5y]` | `dim_age[age_5y]` | derived in M |
| `fact…[acquisition_value_100K]` | `dim_acquisition_value[acquisition_value_100K]` | derived in M |
| `fact…[CapitalizationDate]` | `calendar[cal_date]` | the date-table join |
| `fact…[CostCentre]` | `dim_ri_master_list[COST_CENTRE]` | **`toCardinality: many`** |
| `fact…[CostCentre]` | `dim_finance_fund_centre[FUND_CENTRE_CODE]` | |

> [!warning] One fact column drives two relationships (as at 2026-09-01)
> `fact_sap_asset_gl_mapping[CostCentre]` is the `fromColumn` of **both** the master-list join and the fund-centre join. Any change to that column — a trim, a case fold, a re-derivation upstream — moves both at once, and a value that stops matching will silently drop rows out of *both* the capability hierarchy and the faculty hierarchy.

The master-list join is the only many-to-many link in the model, flagged because several cost centres can map to one capability and one cost centre can appear against several. See [[dim_ri_master_list Reference|dim_ri_master_list]] for why `COST_CENTRE` is the join key here while other repos in the suite join the same table on `CAPABILITY_CODE`, `ILAB_CORE_NAME` or `PURE_FACILITY_ID`.

## Source flow

Every live query reaches Databricks through the `Databricks_MACE` connection record and the `get_table_from_mace(table, schema)` helper — the pattern described in [[Shared Conventions]], and the repo where it is written most plainly. Five fetch queries call the helper and nothing bypasses it.

```
sap_asset_gl_mapping_vendor --> preprocess_sap_asset_gl_mapping --> fact_sap_asset_gl_mapping
                                       |                                    |
      ri_master_list ------------------+ (NODE_ID lookup)                   +--> dim_gl_code
                    \--> dim_ri_master_list                                 +--> dim_cost_centre
                                                                            +--> dim_asset_class
ripm_finance_fund_centre --> finance_fund_centre --> dim_finance_fund_centre +--> dim_asset
                                                                            \--> dim_age
```

`preprocess_sap_asset_gl_mapping` does all the derivation: it cleans and trims the text columns, sorts by `CapitalizationDate`, then adds `cost_centre_group` (the first character of `CostCentre`), `Years` (`Duration.Days(today - CapitalizationDate) / 365.25`), `age_5y` (`Years` integer-divided by 5), `acquisition_value_100K` (`PostedAmount` integer-divided by 100000, or `-1` when null), and `NODE_ID` (a left-outer join to `ri_master_list` on `CostCentre = COST_CENTRE`, defaulting to `"-1"`).

**`Years` is computed from `DateTime.LocalNow()`**, so every asset's age — and therefore its `age_5y` band and its `dim_age` membership — moves at refresh time. The age profile is a snapshot as at the last refresh, not a stored attribute; two refreshes months apart will place the same asset in different bands.

### Three schemas, one catalog

The catalog is `pen_research_infrastructure_insights_prd` throughout, but the queries reach into three different schemas:

| Schema | Queries | Live? |
|---|---|---|
| `ri_lakehouse` | `sap_asset_gl_mapping_vendor`, `ri_master_list`, `funds_centre_hierarchy` | first two yes, third no |
| `ri_research_dashboard` | `ripm_finance_fund_centre` | yes — feeds `dim_finance_fund_centre` |
| `bim_env` | `fund_management_financial_summary`, `finance_value_type_lookup` | no |

The `Databricks_MACE` record itself carries `database = "ilab"`, which is never used: `get_table_from_mace` overrides it with its own `schema` argument on every call. It is a leftover default, not the model's actual schema — the same helper-arity nuance noted in [[Shared Conventions]].

> [!note] The source documentation's data-flow section is incomplete
> `ri_asset_documentation.md` describes the core `sap_asset_gl_mapping_vendor` to `preprocess` to fact chain and the `ri_master_list` feed, but does not mention `ripm_finance_fund_centre` to `finance_fund_centre` at all — even though that chain is the live source of `dim_finance_fund_centre`, a 27-column table fully exposed in the Fields pane. The dictionary entry for the table names the expression; the data-flow section does not. Recorded, not repaired.

## What is actually hidden

**At least 46 columns carry a real `isHidden` flag (as at the 2026-09-01 TMDL read); 4 measures do; no table does.** The distribution is uneven and deliberate:

| Table | Hidden | Visible |
|---|---|---|
| `fact_sap_asset_gl_mapping` | 14 | 7 |
| `calendar` | 13 | 1 |
| `dim_ri_master_list` | 14+ | 5 (the 5 new SCD2 columns' hidden status is unverified — see the Reconciled callout above) |
| `dim_age`, `dim_acquisition_value` | 2 each | 1 each |
| `dim_cost_centre` | 1 | 1 |
| `dim_asset`, `dim_asset_class`, `dim_gl_code`, `dim_finance_fund_centre` | 0 | all |
| `key_measures` | 4 measures | 2 measures |

The logic is consistent: raw join keys and sort helpers are hidden so users browse the readable label instead, and `calendar` exposes only `cal_year` because that is the sole date attribute any visual uses. This is the **field-usage cleanup pass** [[Publication]] never had — Asset is the repo to point at when arguing that the suite's other models could be tidied.

> [!warning] `changedProperty = IsHidden` is not `isHidden` (checked 2026-09-01)
> Several objects in this model carry a `changedProperty = IsHidden` line but **no `isHidden` declaration**. That annotation records only that the property was edited at some point — an object toggled hidden and then back again keeps it. A genuinely hidden object gets a bare `isHidden` line, the way `dim_cost_centre[cost_centre_group]` and the four hidden measures do.
>
> The source documentation appears to have read the annotation as the flag, and marks six columns and two whole tables as hidden when TMDL says they are visible:
>
> | Object | Documented | Actually |
> |---|---|---|
> | `dim_gl_code` *(table)* | hidden | **visible** |
> | `dim_gl_code[GLAccount]`, `[gl_description]` | hidden | **visible** |
> | `dim_asset_class` *(table)* | hidden | **visible** |
> | `dim_asset_class[AssetClass]` | hidden | **visible** |
> | `dim_asset[AssetNumber]` | hidden | **visible** |
> | `dim_ri_master_list[CAPABILITY_CODE]`, `[NODE_ID]` | hidden | **visible** |
>
> So `dim_ri_master_list` exposes **five** columns, not the three the dictionary below claims, and neither `dim_gl_code` nor `dim_asset_class` is a hidden table. This is the same misreading found in [[Survey]], where objects carry the annotation and none carries the flag — see [[Survey Data Model]]. Worth checking in any repo whose documentation asserts that something is hidden.

`dim_gl_code` is also not unused. The report's visuals reference neither it nor `dim_asset_class` — that part of the audit holds — but `Total Cost` and `Maintenance Cost` both filter `dim_gl_code[GLAccount]` in DAX, and `Total Cost` is one of the two visible measures. Dropping the table would break the report's headline figure.

## Dead and orphaned M

Seven expressions in `expressions.tmdl` are referenced by nothing in the model, as of the 2026-09-15 export (previously eight — `dim_platform`, the erroring `queryGroup: decomissioned` query, has since been removed from the file entirely):

| Expression | What it is |
|---|---|
| `platform_cost_centre` | the compressed 2023 Google Sheets snapshot (see below) |
| `process_iLab` | a `(filepath) => …` function wrapping `Csv.Document(File.Contents(filepath))` |
| `get_random_table` | a random-row sampler |
| `lowercase_col_names` | a column-renaming helper |
| `funds_centre_hierarchy` | a `ri_lakehouse` fetch |
| `fund_management_financial_summary` | a `bim_env` fetch, hardcoded to `FUND_CENTRE_CODE = "E02004"` |
| `finance_value_type_lookup` | a `bim_env` fetch |

The last three, together with the `ripm_finance_fund_centre` chain that *is* live, look like a lift from the [[Finance]] model — `fund_management_financial_summary` and `finance_value_type_lookup` are both real tables there. Only the fund-centre part was wired up.

> [!note] `platform_cost_centre` looks used and is not
> Searching `expressions.tmdl` for `platform_cost_centre` returns four hits, but only one is the query. The other three are inside `preprocess_sap_asset_gl_mapping`, where `Table.NestedJoin` names its *output column* `"platform_cost_centre"` — a name collision with the query, not a reference to it. That join reads `ri_master_list`. The pinned Google Sheets export ("2023-Platform CC list-FiRM Verified1", base64/Deflate-compressed inline) feeds nothing at all.

None of this is safe to build on, and the compressed snapshot in particular should not be hand-edited — it is a frozen 2023 export, not a maintained table.

## Parameters

`StartDate` (1966-01-01) and `EndDate` (2026-12-31) are date parameter queries bounding the `calendar` table. **`EndDate` is a fixed literal, not a computed value** — the date table stops at the end of 2026 and will need a manual edit, exactly like the hardcoded planning-cycle labels in [[Finance]]. Nothing errors when it lapses; the calendar simply ends.

## Data dictionary

Transferred from `ri_asset_documentation.md` §4 with the entity, column and description text intact. **The `Hidden` column has been corrected against TMDL** in the eight places the source doc read `changedProperty = IsHidden` as a hidden flag; each correction is marked ⚠. Two entity headings lost a `*(table hidden — unused in current report)*` annotation for the same reason.

Legend: **Hidden** = not shown in the Fields pane (still queryable by measures/relationships). Sort-helper columns are hidden by design — they exist only to control the display order of their paired label column via `sortByColumn` and were never meant to be browsed directly.

### fact_sap_asset_gl_mapping

Fact table: one row per SAP GL posting against a capitalised asset. Source for all cost/asset-count measures in `key_measures`.

| Column | Data type | Hidden | Description |
|---|---|---|---|
| BarcodeInventoryNumber | string | Yes | Physical barcode/inventory tag number attached to the asset, used for asset stocktakes. |
| AssetNumber | string | No | SAP asset number for the capitalised asset this posting relates to; links to `dim_asset`. |
| CostCentre | string | No | SAP cost centre code the posting was charged to; join key (many-to-many) to `dim_ri_master_list[COST_CENTRE]`. |
| CostCentreName | string | Yes | Descriptive name of the cost centre the posting was charged to. |
| SightedOn | string | Yes | Date the asset was last physically sighted/verified during an asset stocktake. |
| AssetClass | string | Yes | SAP asset classification code for this posting; join key to `dim_asset_class`. |
| Location | string | No | Building/site where the asset is physically held. |
| Room | string | No | Room within the Location where the asset is physically held. |
| Description | string | No | Free-text description of the asset for this posting. |
| CapitalizationDate | dateTime | Yes | Date the asset was capitalised; join key to `calendar[cal_date]`. |
| CapitalizationYear | int64 | Yes | Calendar year the asset was capitalised, derived from CapitalizationDate. |
| GLAccount | string | Yes | GL account code this cost was posted to; join key to `dim_gl_code`, drives the GL-account filters in `key_measures`. |
| FiscalYear | string | Yes | SAP fiscal year the posting belongs to. |
| PostedAmount | double | Yes | Dollar amount posted — the core cost figure `key_measures` sums to produce `Total Cost`, `Maintenance Cost`, etc. |
| cost_centre_group | string | Yes | Cost centre grouping key (first character of CostCentre); join key to `dim_cost_centre`. |
| Years | double | Yes | Years the asset has been in service; used to derive `age_5y`. |
| age_5y | int64 | Yes | Asset age bucket in 5-year increments; join key to `dim_age`. |
| acquisition_value_100K | int64 | Yes | Acquisition value bucket in $100K increments; join key to `dim_acquisition_value`. |
| VendorID | string | Yes | SAP vendor/supplier ID the asset was purchased from. |
| VendorName | string | No | Name of the vendor/supplier the asset was purchased from. |
| NODE_ID | string | No | Organisational node identifier for the posting's cost centre; joins (via CostCentre) to the shared `dim_ri_master_list` for cross-system RI reporting. |

### calendar

Standard date table, one row per calendar day across the `StartDate`–`EndDate` range. Marked as the model's date table for time intelligence.

| Column | Data type | Hidden | Description |
|---|---|---|---|
| cal_date | dateTime | Yes (date-table key) | The calendar date for this row; join key to the fact table. |
| cal_intdate | int64 | Yes | cal_date as a whole number (date serial); alternative numeric key. |
| cal_year | int64 | **No** | Calendar year of cal_date (e.g. 2024). |
| cal_month | int64 | Yes | Calendar month number (1–12). |
| cal_month_name | string | Yes | Full month name (e.g. "January"). |
| MonthYear | string | Yes | Short month-and-year label (e.g. "Jan-2024") for chart axes. |
| cal_mon_year_int | int64 | Yes | Combined YYYYMM number, for strict chronological sort/join. |
| Start of Month | dateTime | Yes | First day of the month containing cal_date. |
| Start of Quarter | dateTime | Yes | First day of the quarter containing cal_date. |
| Quarter | string | Yes | Calendar quarter label (e.g. "Q1"). |
| Quarter_num | int64 | Yes | Calendar quarter number (1–4). |
| Week of Year | int64 | Yes | ISO week number of the year. |
| fiscal_year | int64 | Yes | Australian financial year (July–June). |
| fy_label | string | Yes | Financial year label, "FY YY/YY" format. |

Only `cal_year` is exposed — it's the sole calendar attribute actually used in the report (a report-level filter and a Faculty-page chart); everything else is kept in the model for potential future drill-down but hidden today.

### dim_gl_code

Each unique GL account tracked in this report, with a plain-English label. Not referenced by any visual, but `Total Cost` and `Maintenance Cost` both filter `GLAccount` in DAX.

| Column | Data type | Hidden | Description |
|---|---|---|---|
| GLAccount | string | ⚠ No | Unique GL account code from SAP (e.g. equipment purchase, maintenance). |
| gl_description | string | ⚠ No | Plain-English label ("Other Equipment", "Other Assets-AUC", "Maintenance"), mapped from GLAccount. |

### dim_cost_centre

Each unique cost centre and the faculty/division it belongs to.

| Column | Data type | Hidden | Description |
|---|---|---|---|
| cost_centre_group | string | Yes | Unique SAP cost centre code; join key to the fact table. |
| faculty_code | string | No | Faculty/division name, derived from the first letter of the cost centre code. |

### dim_asset_class

Each unique SAP asset classification code. Referenced by no visual and no measure — the one table in the model that is genuinely unused, though still fully wired.

| Column | Data type | Hidden | Description |
|---|---|---|---|
| AssetClass | string | ⚠ No | Unique SAP asset classification code. |

### dim_asset

Each unique capitalised asset and its description.

| Column | Data type | Hidden | Description |
|---|---|---|---|
| AssetNumber | string | ⚠ No | Unique SAP identifier for a capitalised asset; join key to the fact table. |
| Description | string | No | Free-text description of the asset. |

### dim_age

Assets bucketed into 5-year age bands.

| Column | Data type | Hidden | Description |
|---|---|---|---|
| age_5y | int64 | Yes | Age bucket index in 5-year increments (0=0-4y, 1=5-9y, 2=10-14y, 3+=15+y); join key to the fact table. |
| age_groups | string | No | Plain-English label for the bucket (e.g. "0-4 years"), sorted by `age_group_sort`. |
| age_group_sort | int64 | Yes *(sort-helper)* | Numeric sort order so age bands display youngest-to-oldest instead of alphabetically. |

### dim_acquisition_value

Assets bucketed into $100K acquisition-value bands.

| Column | Data type | Hidden | Description |
|---|---|---|---|
| acquisition_value_100K | int64 | Yes | Bucket index in $100K increments (0 = under $100K, -1 = not specified); join key to the fact table. |
| acquisition_value_group | string | No | Plain-English label (e.g. "$1M-$2M"), sorted by `acquisition_value_group_sort`. |
| acquisition_value_group_sort | int64 | Yes *(sort-helper)* | Numeric sort order so value bands display lowest-to-highest instead of alphabetically. |

### dim_ri_master_list

Shared cross-system reference table listing all RI capabilities (facilities/platforms), reused with different join keys across the RI reporting suite (iLab, PURE, Survey, Finance, Awards, Risk).

| Column | Data type | Hidden | Description |
|---|---|---|---|
| INDEX | int64 | Yes | Row sequence number from the source table; not used for reporting or joins. |
| CAPABILITY_CODE | string | ⚠ No | Unique code identifying a capability (facility/platform). |
| CAPABILITY_NAME | string | Yes | Display name of the capability. |
| NODE_ID | string | ⚠ No | Org node identifier, joins to fact tables' `NODE_ID` across the RI suite. |
| NODE_NAME | string | Yes | Display name of the organisational node. |
| COST_CENTRE_NAME | string | Yes | Name of the cost centre associated with the capability. |
| COST_CENTRE | string | **No** | SAP cost centre code; join key (many-to-many) to `fact_sap_asset_gl_mapping[CostCentre]`. |
| FUND_ID | string | Yes | Fund identifier, used for finance-report joins in `ri_pbi_finance`. |
| CAPABILITY_ISO | string | Yes | ISO accreditation status/code for the capability. |
| CAPABILITY_TYPE | string | **No** | Classification of the capability (e.g. platform, facility, service). |
| CAPABILITY_GOVERNANCE | string | **No** | Governance model/committee the capability reports into. |
| SURVEY_CAPABILITY_ID | string | Yes | Join key to `ri_pbi_survey` results. |
| PURE_ORGANISATION_ID | string | Yes | Join key to PURE research-organisation records. |
| PURE_FACILITY_NAME | string | Yes | Facility name in PURE, used for `ri_pbi_publication` joins. |
| PURE_FACILITY_ID | int64 | Yes | Numeric facility ID, join key to PURE publication records. |
| ILAB_CAPABILITY_ID | string | Yes | Join key to iLab booking/utilisation records. |
| ILAB_CORE_NAME | string | Yes | Core facility name in iLab, used for `ri_pbi_ilab_utilisation` joins. |
| RLS_FACILITY_GROUP | string | Yes | RLS group for facility-level access restriction (not currently used — this report has no RLS roles). |
| RLS_FACULTY_GROUP | string | Yes | RLS group for faculty-level access restriction (not currently used). |
| _BUSINESS_KEY | string | *(unverified)* | SCD2 business key — added to the export on 2026-09-15; not yet checked against live TMDL for hidden status or description. |
| _EXPIRATION_TIMESTAMP | dateTime | *(unverified)* | SCD2 row-expiration timestamp — see [[Projects/Databricks/Tables/ri_master_list SCD2 Reference|ri_master_list SCD2 Reference]]. |
| _ROW_ACTIVE_FLAG | string | *(unverified)* | SCD2 active-row flag; always `Y` here since `ri_lakehouse.ri_master_list` exposes only active rows. |
| _START_TIMESTAMP | dateTime | *(unverified)* | SCD2 row-start timestamp. |
| _SURROGATE_KEY | int64 | *(unverified)* | SCD2 surrogate key. |

**At least five columns are exposed** (as at the 2026-09-01 TMDL read): `COST_CENTRE`, `CAPABILITY_TYPE` and `CAPABILITY_GOVERNANCE` are the three the report's filters and charts use, and `CAPABILITY_CODE` and `NODE_ID` are visible alongside them without being used. Most of the remaining columns are cross-system join keys for *other* RI reports and are genuinely hidden here; the five SCD2 columns above were added to the export on 2026-09-15 and their hidden status has not been checked against live TMDL.

The table now arrives with the full 24-column shape — unlike [[Finance]], which narrows the same table to nine in M before load. Asset hides what it does not need rather than dropping it, so a future role or join could reach any master-list identifier without a Power Query change.

### dim_finance_fund_centre

SAP fund-centre reference table giving the organisational hierarchy above each cost centre — seven nested levels, each with a code, a short name and a description, plus a derived faculty code. Joined to the fact table on `fact_sap_asset_gl_mapping[CostCentre] → FUND_CENTRE_CODE`, so the same `CostCentre` value drives both this hierarchy and the `dim_ri_master_list` capability lookup.

Every column is string-typed and **none is hidden** — unlike `dim_ri_master_list`, this table is fully exposed.

| Column | Data type | Hidden | Description |
|---|---|---|---|
| FUND_CENTRE_CODE | string | **No** | SAP fund-centre code; join key to `fact_sap_asset_gl_mapping[CostCentre]`. |
| FUND_CENTRE_ID | string | **No** | Fund-centre identifier. Marked `isDefaultLabel` — the default display field for the table. |
| FUND_CENTRE | string | **No** | Fund-centre short name. |
| FUND_CENTRE_CODE_DESCRIPTION | string | **No** | Description of the fund-centre code. |
| FUND_CENTRE_DESCRIPTION | string | **No** | Description of the fund centre. |
| FUND_CENTRE_LEVEL_1 … LEVEL_7 | string | **No** | Name at each of the seven hierarchy levels (7 columns). |
| FUND_CENTRE_LEVEL_1_CODE … LEVEL_7_CODE | string | **No** | Code at each hierarchy level (7 columns). Note level 4's column is named `FUND_CENTRE_LEVEL_CODE`, not `FUND_CENTRE_LEVEL_4_CODE` — an inconsistency carried through from the source. |
| FUND_CENTRE_LEVEL_1_DESCRPTION … LEVEL_5_DESCRPTION | string | **No** | Description at levels 1–5. **`DESCRPTION` is misspelled in the source** and the misspelling is preserved here; levels 6 and 7 use the correct `DESCRIPTION` spelling. Watch this when writing DAX or M against these columns. |
| FUND_CENTRE_LEVEL_6_DESCRIPTION / LEVEL_7_DESCRIPTION | string | **No** | Description at levels 6 and 7 (correctly spelled). |
| FACULTY_CODE | string | **No** | Faculty short code (`MNHS`, `ENGINEERING`, `PHARMACY`, `SCIENCE`, `IT`, `DVCRE`, `ARTS`), derived in M by a conditional mapping over `FUND_CENTRE_LEVEL_2_DESCRPTION`; any unmapped value falls through to the raw level-2 description. |

27 columns in total. Sourced from the `finance_fund_centre` expression (`queryGroup: preprocess`), which reads `ripm_finance_fund_centre`, adds `FACULTY_CODE`, then selects the final column set.

### key_measures

Container table for all report-wide DAX measures. Holds no data of its own.

| Column | Data type | Hidden | Description |
|---|---|---|---|
| *(no user-facing columns — measures only, see the measure inventory below)* | | | |

## Measure inventory

All six measures live in `key_measures`, following the shared-measures pattern used across the RI reporting suite ([[Shared Conventions]]). Transferred from `ri_asset_documentation.md` §5; DAX re-checked against `key_measures.tmdl`.

Two inconsistencies inside this small set are worth carrying forward, because they are the kind that survive precisely because the model is small enough that nobody audits it:

- **`Total Cost` and `Maintenance Cost` filter the dimension** (`dim_gl_code[GLAccount]`), while **`Other Assets-AUC` and `Other Equipment` filter the fact** (`fact_sap_asset_gl_mapping[GLAccount]`). Both reach the same rows through the relationship, so the results agree today — but the four measures read as one family and are not written as one.
- **`Other Equipment` is a no-op.** It re-filters `Total Cost` to `0000152006`, which `Total Cost` already filters to, so it returns `Total Cost` exactly. It only becomes meaningful if the commented-out `0000152013` is ever restored to `Total Cost`'s filter — which is presumably the intent, and is the clearest signal that the AUC exclusion was meant to be temporary.

Recorded, not repaired.

### Total Cost — *visible*

```dax
CALCULATE( SUM(fact_sap_asset_gl_mapping[PostedAmount]), dim_gl_code[GLAccount] IN {"0000152006"}) //,"0000152013"
```

Sums `PostedAmount` for GL account `0000152006` ("Other Equipment"). This is the base cost figure most other measures build on. **Note:** GL account `0000152013` (Assets Under Construction) is commented out of the filter, so AUC spend is currently excluded from this total — worth confirming with the business owner whether that's intentional.

### Distinct Assets — *visible*

```dax
DISTINCTCOUNTNOBLANK(fact_sap_asset_gl_mapping[AssetNumber])
```

Counts unique, non-blank asset numbers in the current filter context — i.e. the total number of distinct capitalised assets being reported on.

### Other Assets-AUC — *hidden (not yet bound to a visual)*

```dax
CALCULATE([Total Cost], fact_sap_asset_gl_mapping[GLAccount] in {"0000152013"})
```

Re-filters `Total Cost` to GL account `0000152013` (Assets Under Construction) — spend on assets still being built, not yet capitalised as finished equipment.

### Other Equipment — *hidden (not yet bound to a visual)*

```dax
CALCULATE([Total Cost], fact_sap_asset_gl_mapping[GLAccount] in {"0000152006"})
```

Re-filters `Total Cost` to GL account `0000152006` ("Other Equipment"). Since `Total Cost` already applies this same filter, this measure currently returns the same value as `Total Cost` — effectively a duplicate until `Total Cost`'s filter set changes.

### Maintenance Cost — *hidden (not yet bound to a visual)*

```dax
CALCULATE( SUM(fact_sap_asset_gl_mapping[PostedAmount]), dim_gl_code[GLAccount] IN {"0000737012"})
```

Sums `PostedAmount` for GL account `0000737012` ("Maintenance") — total spend on maintaining existing assets (as opposed to acquiring new ones).

### Proportion of Total Cost — *hidden (not yet bound to a visual)*

```dax
VAR check_for_year = IF(HASONEVALUE('calendar'[cal_year]), BLANK(), 1)
VAR numerator      = CALCULATE([Total Cost], ALLSELECTED('calendar'[cal_year]))
VAR denominator    = CALCULATE([Total Cost], ALLSELECTED())
VAR result         = DIVIDE(numerator, denominator)
RETURN
    IF(ISBLANK(check_for_year), BLANK(), result)
```

Shows each selected slice of `Total Cost` as a percentage of the grand total, ignoring the row/column filters within the visual itself — so a breakdown by, say, faculty always sums to 100%. Walkthrough:
- `check_for_year` is a guard: it evaluates to `1` unless exactly one calendar year is selected, in which case it's `BLANK()`.
- `numerator` recomputes `Total Cost` for the *selected* year(s) only (`ALLSELECTED('calendar'[cal_year])` clears any finer filter below the year level but respects the year slicer).
- `denominator` recomputes `Total Cost` with **all** filters in the visual cleared (`ALLSELECTED()`), i.e. the grand total.
- The final `IF` returns blank whenever a single year is explicitly selected, because "percentage of total" isn't a meaningful figure once the context has already been narrowed to one year.

**Currently hidden measures**: `Other Assets-AUC`, `Other Equipment`, `Maintenance Cost`, and `Proportion of Total Cost` are not bound to any visual in the current report and were hidden during a field-usage cleanup pass. They are fully functional and easy to surface again — hidden, not deleted.

## See also

- [[Asset]] — the repo entry note, including why there is no RLS here
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the shared identity table, joined here on `COST_CENTRE`
- [[Shared Conventions]] — the `Databricks_MACE` / `get_table_from_mace` pattern this repo shows most plainly
- [[Finance]] — where the same master list is projected to nine columns, and where the orphaned finance queries here appear to come from
- [[ri_pbi_asset semantic model]] — the exported model (derived, never hand-edited): every column and type, measure DAX, relationships and Power Query expressions
- **Derived layer** (`graphify/`, never hand-edited): [[_COMMUNITY_Finance Data Pipeline]], [[_COMMUNITY_Asset Class Mapping]], [[_COMMUNITY_Asset Number Mapping]], [[_COMMUNITY_General Ledger Mapping]], [[fact_sap_asset_gl_mapping]], [[dim_ri_master_list]], `dim_platform` *(query removed from the semantic-model export on 2026-09-15; no node since export `51b1e84`)*, [[platform_cost_centre]], [[2023 Platform CC List - FiRM Verified1]], [[preprocess_sap_asset_gl_mapping]], [[get_table_from_mace_5]]
- **Derived layer — M queries** (`graphify/`, never hand-edited; `_N` suffixes as of export `0c73b0cf`, each checked to be the `ri_pbi_asset`-sourced node): [[finance_fund_centre_1]], [[ripm_finance_fund_centre]], [[funds_centre_hierarchy]], [[finance_value_type_lookup]], [[fund_management_financial_summary]], [[sap_asset_gl_mapping_vendor]], [[process_iLab_1]], [[get_random_table_1]], [[lowercase_col_names_5]], [[ri_master_list_2]], [[StartDate_7]], [[EndDate_7]]
