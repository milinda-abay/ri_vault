# Finance Data Model

The tables, relationships, source queries and measures behind [[Finance]]. Eleven tables, nine relationships, two facts, forty-two measures.

This note carries the measure inventory as well as the model structure — Finance's source documentation is compact enough that splitting them would separate things that are read together. Everything below the narrative is transferred in full and meant to be read as reference.

> [!note] Reconciled against [[ri_pbi_finance semantic model]] — last on 2026-09-19
> First reconciled 2026-09-10, when all 11 tables, 9 relationships, 42 measures, the 4 calculation items, and every column this note names matched the export. Re-checked 2026-09-14 against the export for `ri_pbi_finance` @ `ff738a0`: that sub-repo commit left the exported semantic model byte-identical — the 2026-09-13 export changed only `_meta.md` — so the column-level claims stood, and the table, relationship, measure and calculation-item counts were re-counted directly and matched. Reconciled again the same day against `ri_pbi_finance` @ `5621d064`: nine dev/pending-deletion expressions were deleted from `expressions.tmdl` — `Merge1`, `Merge2`, `bim_env_finance_commitment_item`, `bim_env_finance_cost_element`, `'dim_finance_commitment_item (old)'`, `'dim_finance_cost_centre (2)'`, `'dim_finance_fund_centre (2)'`, `platform_finance_cost_element` and `source_ri_gl_codes` — none of them fed a live table, so no table, relationship, measure or column count changes then; see the updated "Query notes and gotchas" section. Reconciled again 2026-09-15 against `5621d064` → `e55876ba`: `dim_ri_master_list`'s partition now references a new intermediate expression, `process_ri_master_list`, which itself calls the pre-existing `ri_master_list` fetch — a wrapper inserted between the table and the raw `get_table_from_mace` call, with no column or row change (still 9 columns). This note has no data dictionary; the export is the column-level reference — every column of every table, with its type — along with measure DAX and the Power Query expression inventory. Hidden flags and `toCardinality` are not in it, and those claims still rest on the 2026-09-01 TMDL read.
>
> Re-checked 2026-09-19 against the 2026-09-18 export (`ri_pbi_finance` @ `92742ba7`). The sub-repo commit moved, but the exported semantic model is byte-identical to the one reconciled on 2026-09-15, so nothing in the body changed. The graph export renumbered its `_N`-suffixed nodes, so the derived-layer links in See also were re-pointed to the `ri_pbi_finance`-sourced node for each name. Several had already pointed at another report's same-named node before this export.
>
> Re-checked 2026-09-19 against the 2026-09-19 export (`ri_pbi_finance` @ `91eb5721`). The sub-repo commit moved, but the export was rendered from the same source graph (`944e789f`) as the `11a98af` export this note was last reconciled against, and every file under `graphify/ri_pbi_production/` apart from `_meta.md` is byte-identical. So nothing the export shows has changed. It also means the export cannot show what that commit did change.

## Two facts that don't meet

| Fact | Drives | Grain |
|---|---|---|
| `fact_finance_forecast_budget_actuals` | P&L-style actual / budget / forecast measures | Scenario-and-version-driven financial lines |
| `fact_fund_management_financial_summary` | Fund-management and capex measures | Fund-management lines, filtered upstream to account codes `152005`, `152006`, `152013` |

They share `Calendar`, `dim_ri_master_list` and `dim_finance_fund_centre`, and nothing else. `dim_finance_cost_element` belongs to the first; `dim_finance_commitment_item` and `dim_finance_value_type_lookup` to the second. **There is no relationship between the two facts**, so a measure spanning both must reach through a shared dimension or compute each side independently.

The version dimension is not a table. `actuals_monthly`, `budget_monthly_2026` and `forecast_jan_2026` all filter `fact_finance_forecast_budget_actuals[VERSION]` on a **hardcoded string**, and each excludes `"All Months"` aggregate rows to avoid double-counting. See [[Finance]] for why that matters every planning cycle.

## Table inventory

| Table | Type | Visible? | Relationship status | Notes |
|---|---|---|---|---|
| `fact_finance_forecast_budget_actuals` | Fact | Yes | Related | Actual / budget / forecast fact table; joins cost element, calendar, RI master list, and fund centre. |
| `fact_fund_management_financial_summary` | Fact | Yes | Related | Fund-management / capex fact table; joins calendar, value type, RI master list, commitment item, and fund centre. |
| `Calendar` | Date/support | Yes | Related | Daily calendar table with derived year/month/fiscal columns. |
| `dim_finance_commitment_item` | Dimension | Yes | Related | Commitment-item hierarchy used by `raw_capex_amount`. |
| `dim_finance_cost_centre` | Dimension | Yes | **Unrelated** | Loaded into the model, but currently has no relationship in `relationships.tmdl`. |
| `dim_finance_cost_element` | Dimension | Yes | Related | Cost-element hierarchy plus custom categorisation used by operating-result measures. |
| `dim_finance_fund_centre` | Dimension | Yes | Related | Shared fund-centre hierarchy joined to both fact tables. |
| `dim_finance_value_type_lookup` | Lookup | **No** | Related | Hidden lookup table for `VALUE_TYPE_CODE`. |
| `dim_ri_master_list` | Shared reference | Yes | Related | Shared RI capability/node/governance table and RLS anchor. |
| `KeyMeasures` | Measures container | Yes | N/A | Empty table partition used only to hold measures. |
| `Time intelligence` | Calculation group | Yes | N/A | Calculation-group table with 4 items; `Ordinal` is hidden. |

## Relationships

`relationships.tmdl` currently defines **9** active relationships:

| From | To | Notes |
|---|---|---|
| `fact_finance_forecast_budget_actuals[ACCOUNT_CODE]` | `dim_finance_cost_element[ACCOUNT_CODE]` | Default single-direction relationship. |
| `fact_finance_forecast_budget_actuals[date]` | `Calendar[cal_date]` | Default single-direction relationship. |
| `fact_fund_management_financial_summary[FINANCIAL_YEAR]` | `Calendar[cal_year]` | `toCardinality: many`. |
| `fact_fund_management_financial_summary[VALUE_TYPE_CODE]` | `dim_finance_value_type_lookup[VALUE_TYPE_CODE]` | Default single-direction relationship. |
| `fact_finance_forecast_budget_actuals[FUND_CENTRE_CODE]` | `dim_ri_master_list[COST_CENTRE]` | `toCardinality: many`. |
| `fact_fund_management_financial_summary[FUND_CENTRE_CODE]` | `dim_ri_master_list[COST_CENTRE]` | `toCardinality: many`. |
| `fact_fund_management_financial_summary[COMMITMENT_ITEM_CODE]` | `dim_finance_commitment_item[COMMITMENT_ITEM_CODE]` | Default single-direction relationship. |
| `fact_fund_management_financial_summary[FUND_CENTRE_CODE]` | `dim_finance_fund_centre[FUND_CENTRE_CODE]` | Default single-direction relationship. |
| `fact_finance_forecast_budget_actuals[FUND_CENTRE_CODE]` | `dim_finance_fund_centre[FUND_CENTRE_CODE]` | Default single-direction relationship. |

Notes on the graph:

- `dim_finance_cost_centre` is present in the model but currently **unjoined**.
- There are **no inactive relationships** and none is bidirectional.
- Three are flagged `toCardinality: many`: both facts to `dim_ri_master_list[COST_CENTRE]`, and `fact_fund_management_financial_summary[FINANCIAL_YEAR]` to `Calendar[cal_year]`.

### The master-list join

Both facts reach `dim_ri_master_list` on **`FUND_CENTRE_CODE → COST_CENTRE`** — a SAP cost-centre key, matching [[Asset]] and unlike every other repo. See [[dim_ri_master_list Reference|dim_ri_master_list]] for how the join key varies.

That both facts are reachable is what makes Finance's RLS work end to end, unlike [[Awards]] and [[Publication]], where roles leave a fact unsecured. But note the roles filter `CAPABILITY_CODE`, `NODE_ID` or `CAPABILITY_GOVERNANCE` while the relationship joins `COST_CENTRE` — the filter reaches the facts through a different column than it names, as in [[Awards]]. It works because filtering any column of the master list restricts its rows, and the relationship propagates from there.

### The projected master list

Finance's copy is narrowed **in M, before load**, to nine columns: `CAPABILITY_CODE`, `CAPABILITY_NAME`, `NODE_ID`, `NODE_NAME`, `COST_CENTRE_NAME`, `COST_CENTRE`, `CAPABILITY_ISO`, `CAPABILITY_TYPE`, `CAPABILITY_GOVERNANCE`. The other ten — `INDEX`, `FUND_ID`, and the `PURE_*`, `ILAB_*`, `SURVEY_*` and `RLS_*` groups — never arrive.

All three RLS filter columns survive, so the projection is safe today. **It is also a constraint**: a role filtering an iLab, PURE or survey identifier cannot be written here until the projection widens. See [[Finance RLS]].

The same expression carries a row filter, `[COST_CENTRE] <> "" or [COST_CENTRE] <> null`, which is a tautology and removes nothing. Recorded as-is.

## Source flow

The live model uses a mix of shared helper-based and direct Databricks queries.

### Queries used by live partitions

| Expression | Used by | Summary |
|---|---|---|
| `ri_lakehouse_finance_forecast_budget_actuals` | `fact_finance_forecast_budget_actuals` via `process_ri_lakehouse_finance_forecast_budget_actuals` | Uses `get_table_from_mace("ri_finance","ri_lakehouse")`. |
| `process_ri_lakehouse_finance_forecast_budget_actuals` | `fact_finance_forecast_budget_actuals` | Currently passes the source through unchanged; earlier sign-flip logic is commented out. |
| `process_fund_management_financial_summary` | `fact_fund_management_financial_summary` | Filters `ACCOUNT_CODE` to `152005`, `152006`, `152013`. |
| `account_finance_cost_element` | `dim_finance_cost_element` | Uses `bim_account_finance_cost_element` and adds `CUSTOM_CATEGORY`. |
| `bim_account_finance_commitment_item` | `dim_finance_commitment_item` | Direct Databricks query to `lakehouse_bim_prd.account.finance_commitment_item`, filtered to `_ROW_ACTIVE_FLAG = "Y"`. |
| `bim_account_finance_cost_centre` | `dim_finance_cost_centre` | Direct Databricks query to `lakehouse_bim_prd.account.finance_cost_centre`, filtered to `_ROW_ACTIVE_FLAG = "Y"`. |
| `bim_account_finance_fund_centre` | `dim_finance_fund_centre` | Direct Databricks query to `lakehouse_bim_prd.account.finance_fund_centre`, filtered to `_ROW_ACTIVE_FLAG = "Y"`. |
| `bim_env_finance_value_type_lookup` | `dim_finance_value_type_lookup` | Direct Databricks query to `pen_research_infrastructure_insights_prd.bim_env.finance_value_type_lookup`. |
| `process_ri_master_list` → `ri_master_list` | `dim_ri_master_list` | `process_ri_master_list` (added 2026-09-15) wraps `ri_master_list`, which uses `get_table_from_mace("ri_master_list","ri_lakehouse")`; keeps 9 columns. |
| Inline `List.Dates(...)` partition | `Calendar` | Generates the date table from `StartDate` to `EndDate`. |
| `#table({},{})` stub partition | `KeyMeasures` | Empty table used only as a measure container. |

### Query notes and gotchas

- `get_table_from_mace(...)` is **actively used** in this repo for:
  - `ri_lakehouse_finance_forecast_budget_actuals`
  - `ri_master_list`
  - `bim_env_fund_management_financial_summary`
- `data_path` is still defined as a parameter but is **not referenced** by any live table.
- As of the 2026-09-14 export (`ri_pbi_finance` @ `5621d064`), the dev / pending-deletion expressions previously recorded here — `platform_finance_cost_element`, `source_ri_gl_codes`, `bim_env_finance_commitment_item`, `bim_env_finance_cost_element`, `'dim_finance_commitment_item (old)'`, `'dim_finance_cost_centre (2)'`, `'dim_finance_fund_centre (2)'`, `Merge1` and `Merge2` — have been deleted from `expressions.tmdl`. None fed a live table, so this is cleanup, not a model change.

**Two source conventions coexist here**, which is unusual in the suite. Three queries go through the shared `get_table_from_mace` helper against `pen_research_infrastructure_insights_prd`; four others hand-roll a direct connection to a **different catalog** — `lakehouse_bim_prd.account` — for the SAP dimension tables. The direct queries all filter `_ROW_ACTIVE_FLAG = "Y"`, so they are reading slowly-changing tables and taking the current version. Neither convention is wrong, but a new query needs a deliberate choice about which catalog it belongs to rather than a copy of whichever neighbour it lands next to.

## Table notes

### Facts

- **`fact_finance_forecast_budget_actuals`**
  - scenario/version-driven fact table for actuals, budgets, and forecasts
  - key fields used by measures: `ACCOUNT_CODE`, `FINANCIAL_YEAR`, `FUND_CENTRE_CODE`, `MONTH`, `VERSION`, `AMOUNT`
- **`fact_fund_management_financial_summary`**
  - fund-management / capex fact table
  - filtered upstream to account codes `152005`, `152006`, `152013`
  - key fields used by measures: `COMMITMENT_ITEM_CODE`, `FINANCIAL_YEAR`, `FUND_CENTRE_CODE`, `VALUE_TYPE_CODE`, `AMOUNT`

### Supporting tables

- **`dim_finance_cost_element`**
  - primary operating-result dimension for actual/budget/forecast slicing
  - includes `CUSTOM_CATEGORY`
  - hidden column: `_SURROGATE_KEY`
- **`dim_finance_commitment_item`**
  - used by `raw_capex_amount` through `COMMITMENT_ITEM_LEVEL_2_CODE = "CAPEXPS"`
- **`dim_finance_fund_centre`**
  - linked to both facts on `FUND_CENTRE_CODE`
- **`dim_finance_value_type_lookup`**
  - hidden table
  - related only to the fund-management fact
- **`dim_ri_master_list`**
  - retains 9 columns in this repo: `CAPABILITY_CODE`, `CAPABILITY_NAME`, `NODE_ID`, `NODE_NAME`, `COST_CENTRE_NAME`, `COST_CENTRE`, `CAPABILITY_ISO`, `CAPABILITY_TYPE`, `CAPABILITY_GOVERNANCE`
  - is the anchor table for finance RLS
- **`dim_finance_cost_centre`**
  - loaded but currently unused in the relationship graph
- **`Calendar`**
  - generated from `StartDate = 2000-01-01` to `EndDate = 2027-01-01`
  - includes `cal_date`, `cal_year`, `cal_month_name`, `MonthYear`, fiscal-year columns, and day attributes

## 7. Measure inventory

`KeyMeasures.tmdl` currently defines **42** measures.

### 01 Core

- `actuals_monthly` — `Actual` version excluding `All Months`
- `budget_monthly_2026` — `Final Budget 2026` version excluding `All Months`
- `actuals_expenditure` — `actuals_monthly` filtered to `OPE_EXP1`
- `actuals_revenue` — `actuals_monthly` filtered to `OPE_REV1`
- `raw_pnl_amount_sum` — base sum of `fact_finance_forecast_budget_actuals[AMOUNT]`

### Budget

- `budget_expenditure` — `budget_monthly_2026` filtered to `OPE_EXP1`
- `budget_revenue` — `budget_monthly_2026` filtered to `OPE_REV1`
- `budget_operating_result` — revenue/expenditure rollup with `ISINSCOPE(...)` logic

### Forecast

- `forecast_jan_2026` — 2026 / `Forecast Jan` version excluding `All Months`
- `forecast_revenue` — `forecast_jan_2026` filtered to `OPE_REV1`
- `forecast_expenditure` — `forecast_jan_2026` filtered to `OPE_EXP1`
- `forecast_operating_result` — revenue/expenditure rollup with `ISINSCOPE(...)` logic

### Capex

- `raw_commitment_amount` — base negated sum of fund-management `AMOUNT`
- `raw_capex_amount` — `raw_commitment_amount` filtered to `COMMITMENT_ITEM_LEVEL_2_CODE = "CAPEXPS"`
- `2022 Capex`
- `2023 Capex`
- `2024 Capex`
- `2025 Capex`
- `2026 Capex`
- `Capex Variance 2025-2024`
- `Year` — empty-string stub measure in the Capex folder

### Platform / actuals / variance

- `platform_actuals_operating_result`
- `platform_operating_result_index`
- `platform_actuals_expenditure`
- `platform_actuals_revenue`
- `2021 Actual`
- `2022 Actual`
- `2023 Actual`
- `2024 Actual`
- `2025 Actual`
- `2026 Actual`
- `Variance 2025-2024`
- `monash_actuals_operating_result`

### Revenue / cost categorisation

- `External Revenue`
- `Direct Cost`
- `Internal Monash Allocation`
- `Internal User Revenue`
- `Indirect Cost`
- `Cost recoveries`
- `Subsidy (DEL)`

### Diagnostics / placeholders

- `using_inscope (DEL)`
- `Measure`

### Verified measure notes

- `platform_operating_result_index` was added recently and is now included in the documented measure count.
- `raw_capex_amount` is the capex-specific base measure used by the yearly capex measures; they do **not** calculate directly from `raw_commitment_amount`.
- `Internal User Revenue` currently filters `dim_finance_cost_element[COST_ELEMENT_LEVEL_6_CODE]` for `736061`, `736056`, and `736057`.
- `Cost recoveries` currently uses:
  - numerator = `External Revenue - Internal User Revenue`
  - denominator = `platform_actuals_expenditure`
- `budget_monthly_2026` and `forecast_jan_2026` are hardcoded to the current planning cycle names.

## 8. Calculation group

`Time intelligence.tmdl` contains **4** calculation items:

- `Current`
- `YTD`
- `PY YTD`
- `YTD (%)`

`Time intelligence[Ordinal]` is hidden and used as the sort key for `Time intelligence[Name]`.

## 9. Visibility summary

### Hidden tables

- `dim_finance_value_type_lookup`

### Hidden columns

- `dim_finance_cost_element[_SURROGATE_KEY]`
- `dim_finance_value_type_lookup[VALUE_TYPE_CODE]`
- `dim_finance_value_type_lookup[VALUE_TYPE_DESCRIPTION]`
- `dim_finance_value_type_lookup[VALUE_TYPE_INDICATOR]`
- `Time intelligence[Ordinal]`

## See also

- [[Finance]] — the repo entry note
- [[Finance RLS]] — the three-column role scheme and what the projection constrains
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the shared identity table, projected to nine columns here
- [[Shared Conventions]] — the PBIP layout and Databricks source pattern
- [[ri_pbi_finance semantic model]] — the exported model (derived, never hand-edited): every column and type, measure DAX, relationships and Power Query expressions
- **Derived layer — model** (`graphify/`, never hand-edited): [[_COMMUNITY_Finance Forecast Model]], [[_COMMUNITY_Finance Data Pipeline]], [[_COMMUNITY_Journal Lookup Table]], [[fact_finance_forecast_budget_actuals]], [[fact_fund_management_financial_summary]], `dim_finance_cost_centre` *(no node since export `51b1e84`)*, [[dim_finance_cost_element]], [[dim_finance_fund_centre_1]], [[dim_finance_commitment_item]], [[dim_finance_value_type_lookup]], `Merge1` *(expression deleted 2026-09-14; the graph's `Merge1` node is Survey's)*, `Merge2` *(no node since export `51b1e84`)*, [[process_ri_lakehouse_finance_forecast_budget_actuals]], [[process_fund_management_financial_summary]]
- **Derived layer — upstream sources** (`graphify/`, never hand-edited): [[lakehouse_bim_prd.account.finance_cost_centre]], [[lakehouse_bim_prd.account.finance_fund_centre]], [[lakehouse_bim_prd.account.finance_commitment_item]], [[pen_research_infrastructure_insights_prd.bim_env.finance_value_type_lookup]]
- **Derived layer — M queries** (`graphify/`, never hand-edited; `_N` suffixes as of export `0c73b0cf`, each checked to be the `ri_pbi_finance`-sourced node): [[bim_account_finance_commitment_item]], [[bim_account_finance_cost_centre]], [[bim_account_finance_cost_element]], [[bim_account_finance_fund_centre]], [[bim_env_finance_value_type_lookup]], [[bim_env_fund_management_financial_summary]], [[account_finance_cost_element]], `platform_finance_cost_element` *(no node since export `51b1e84`)*, `source_ri_gl_codes` *(no node since export `51b1e84`)*, [[ri_lakehouse_finance_forecast_budget_actuals]], [[process_ri_master_list]], [[ri_master_list_3]], [[dim_finance_fund_centre_1]], [[get_table_from_mace_7]], [[data_path_2]], [[StartDate_1]], [[EndDate_1]], [[Calendar_1]], [[Finance dim_ri_master_list]]
