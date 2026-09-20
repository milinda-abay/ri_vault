# Finance

`ri_pbi_finance` — the Power BI PBIP project reporting on **budget, forecast and actuals**, plus **fund-management and capex** financials. Part of [[Overview|RI PBI Production]].

Two reports really, sharing a model: a P&L-style view of actual against budget against forecast for RI platforms, and a fund-management view covering capex commitments. Each has its own fact table, and they meet only at the shared dimensions.

## Headline figures

Verified against TMDL on 2026-09-01.

> [!note] Reconciled against [[ri_pbi_finance semantic model]] on 2026-09-19 (`ri_pbi_finance` @ `92742ba7`)
> The export confirms: the table, relationship, measure and calculation-item counts; the three `get_table_from_mace` calls and the absence of any `File.Contents` call; `data_path` referenced by nothing; every measure deviation in the table below, the `(DEL)` measures, `Year` and `Measure`; the calendar-year `DATESYTD`, the `fiscal_YTD` name and the unused `max_day`; and the `Day`/`Date` and `cal_mon_yeat_int` column names. The one correction was **Dead M code**, rewritten below: every expression it listed was deleted on 2026-09-14.
>
> The export doesn't carry the RLS roles, `isHidden` flags, `formatString`, `sortByColumn` or relationship cardinality. The role counts, the six hidden flags, `'2021 Actual'`'s missing format string, `MonthYear`'s sort key and the three many-to-many relationships therefore still rest on the 2026-09-01 TMDL read.
>
> Re-checked 2026-09-19 against the 2026-09-19 export (`ri_pbi_finance` @ `91eb5721`). The sub-repo commit moved, but the export was rendered from the same source graph (`944e789f`) as the `11a98af` export this note was last reconciled against, and every file under `graphify/ri_pbi_production/` apart from `_meta.md` is byte-identical. So nothing the export shows has changed. It also means the export cannot show what that commit did change.

| | |
|---|---|
| Semantic model folder | `ri_finance.SemanticModel` |
| Tables | 11 — 2 fact, 7 supporting, 1 measure container, 1 calculation group |
| Relationships | 9 — 3 many-to-many, none inactive, none bidirectional |
| Measures | 42 in `KeyMeasures`; plus 4 calculation items in `Time intelligence` |
| RLS roles | 36 — 16 capability, 15 node, 4 faculty, 1 unfiltered `TESTING` |

## The repo where the RLS pattern is not a pattern

Finance and [[iLab Utilisation]] are the two repos that **mix filter columns within one repo**, and Finance does it across three:

| Group | Count | Filter column |
|---|---|---|
| Whole-platform | 16 | `CAPABILITY_CODE` |
| Sub-node / site | 15 | `NODE_ID` |
| Faculty / governance | 4 | `CAPABILITY_GOVERNANCE` |
| Unfiltered | 1 | none — `TESTING` |

The split is systematic, by scope granularity, not accidental. But it means **there is no repo-wide default to fall back on.** A new role must copy the shape of the roles it sits beside — a site-level role next to `MPMP-CLA` filters `NODE_ID`; a capability-wide one next to `MARP` filters `CAPABILITY_CODE`. Defaulting to `CAPABILITY_CODE` because that is what [[Publication]] and [[Risk]] do produces a role that silently grants nothing, or the wrong rows. See [[Finance RLS]].

## Also worth knowing up front

**`dim_ri_master_list` is projected down to 9 columns here**, before load, by `Table.SelectColumns` in M. The `ILAB_*`, `PURE_*`, `SURVEY_*` and `RLS_*` identifier groups are dropped, because finance has no facts keyed on them. Everything the 35 filtered roles reference survives — but **finance cannot grow a role filtering an iLab, PURE or survey identifier** without widening the projection first. See [[dim_ri_master_list Reference|dim_ri_master_list]].

**This repo actually hides things.** Six `isHidden` flags, including one entirely hidden table (`dim_finance_value_type_lookup`) — unlike [[Publication]], [[Awards]], [[Risk]] and [[iLab Utilisation]], which hide almost nothing. Don't carry the "nothing is hidden in this suite" assumption in here.

**One dimension is loaded but unjoined.** `dim_finance_cost_centre` has no relationship in `relationships.tmdl` at all. It refreshes and appears in the Fields pane, and filters nothing.

## Detail notes

- [[Finance Data Model]] — the two facts, the table inventory, relationships, source flow, and the full 42-measure inventory
- [[Finance RLS]] — the 36 roles, the three-column scheme, and the `TESTING` gap

## Known gotchas

Recorded, not repaired.

### No hardcoded local-file path

Worth stating explicitly, because three repos in the suite do have one and it is the first thing to suspect on a refresh failure.

**No M expression in this repo calls `File.Contents` at all.** A `data_path` parameter is still defined but referenced by nothing — the same orphan [[Awards]] and [[Risk]] carry. Neither [[Publication]]'s and [[Risk]]'s live stale-path failures nor [[Survey]]'s dormant chain applies here. See [[Shared Conventions]].

### Hardcoded planning-cycle labels

`budget_monthly_2026` filters `VERSION = "Final Budget 2026"`; `forecast_jan_2026` filters `"Forecast Jan"`. Both strings are baked into the DAX, and **everything built on them inherits the hardcoding** — `budget_expenditure`, `budget_revenue`, `budget_operating_result`, `forecast_revenue`, `forecast_expenditure`, `forecast_operating_result`.

These need a manual edit every planning cycle. Nothing errors when the cycle rolls over; the measures simply return the previous cycle's numbers, or nothing.

### Measures that don't match their siblings

Four inconsistencies, each verified against `KeyMeasures.tmdl`. They sit inside otherwise-uniform families, which is what makes them easy to miss:

| Measure | Deviation |
|---|---|
| `'2026 Actual'` | Missing the `ALL('Calendar'[cal_month_name])` clause every other year measure carries |
| `'2021 Actual'` | Missing the currency `formatString` its siblings have — and carries a redundant `KEEPFILTERS('Calendar'[cal_year])` with no predicate |
| `'Internal Monash Allocation'` | Filters `[actuals_revenue]`, where its sibling category measures filter `[platform_actuals_revenue]` |
| `monash_actuals_operating_result` | **Byte-for-byte identical DAX** to `platform_actuals_operating_result`. The name implies a Monash-wide versus platform-scoped distinction that the definition does not make |

Whether any is deliberate is unconfirmed. Recorded, not changed.

### `(DEL)`-suffixed measures are still live

`using_inscope (DEL)` and `Subsidy (DEL)` are both flagged for deletion by name, and both remain in the model, visible and wired in. Cleanup candidates, not templates.

`Year` (an empty-string stub in the Capex folder) and `Measure` (a bare `BLANK()`) are also present and serve no purpose.

### Time intelligence is calendar-year, not fiscal

The `YTD`, `PY YTD` and `YTD (%)` calculation items call `DATESYTD(last_date)` **with no year-end-date argument**, so they compute a calendar-year YTD. The model otherwise tracks an Australian July-start fiscal year through `Calendar[fiscal_year]` and `[fy_label]`.

The giveaway is in the code: the variable holding the result is named `fiscal_YTD` while computing a calendar YTD. Worth confirming intent with the business owner — a finance report is the place this matters most.

`YTD` also computes a `max_day` variable it never uses, the same dead leftover [[Publication]], [[Awards]] and [[Risk]] all carry.

### Calendar column names mislead

- **`Calendar[Day]` holds the weekday *name*; `Calendar[Date]` holds the day-of-month *number*.** They read as swapped.
- **`Calendar[cal_mon_yeat_int]`** carries the "yeat" typo, as in [[Publication]], [[Survey]] and [[Risk]] — but here it is also referenced as `MonthYear`'s sort key, so renaming it needs a matching reference update rather than being merely awkward.

### Dead M code

The dev and pending-deletion expressions this section used to list were deleted from `expressions.tmdl` at `ri_pbi_finance` @ `5621d064` (2026-09-14): `source_ri_gl_codes`, `'dim_finance_commitment_item (old)'`, `'dim_finance_cost_centre (2)'`, `'dim_finance_fund_centre (2)'`, `Merge1`, `Merge2` and `platform_finance_cost_element`. None of them fed a live table.

What remains unused, as of the 2026-09-18 export, is the shared helper kit that most repos in the suite carry: the functions `fetch_task`, `fix_columns`, `fix_table_column_type`, `lowercase_col_names`, `preprocess_table_datetime`, `preprocess_table_text`, `TableType` and `#shared`, plus the `data_path` parameter. No table reaches any of them. They are cleanup candidates rather than dev debris, and removing them does not touch the model.

> [!warning] Correction to earlier documentation
> An earlier version of this note stated that the `Databricks_MACE` / `get_table_from_mace` helper pair was unused in this repo. **That is wrong.** The helper is called three times — `get_table_from_mace("ri_finance","ri_lakehouse")`, `get_table_from_mace("ri_master_list","ri_lakehouse")` and `get_table_from_mace("fund_management_financial_summary","bim_env")` — verified in `expressions.tmdl` on 2026-09-01. The repo's own documentation agrees. What *is* true is that four other queries bypass it and hit `lakehouse_bim_prd.account` directly; see [[Finance Data Model]].

## See also

- [[Overview|RI PBI Production]] — workspace map of all the report repos
- [[Shared Conventions]] — PBIP layout, Databricks source pattern, centralised measures
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the shared identity table, projected to 9 columns here
- [[RLS Patterns]] — how row-level security is built across the suite
- **Derived layer** (`graphify/`, never hand-edited): [[ri_pbi_finance]], [[ri_pbi_finance Repository]], [[_COMMUNITY_Finance Forecast Model]], [[_COMMUNITY_Finance Data Pipeline]], [[_COMMUNITY_Journal Lookup Table]], [[fact_finance_forecast_budget_actuals]], [[fact_fund_management_financial_summary]], [[dim_ri_master_list]], [[Databricks_MACE_6]], [[get_table_from_mace_7]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): `Merge1` *(expression deleted 2026-09-14; the graph's `Merge1` node is Survey's)*, `Merge2` *(no node since export `51b1e84`)*, `dim_finance_cost_centre` *(no node since export `51b1e84`)*, [[dim_finance_cost_element]], [[dim_finance_value_type_lookup]], `source_ri_gl_codes` *(no node since export `51b1e84`)*, `platform_finance_cost_element` *(no node since export `51b1e84`)*, [[data_path_2]], [[MARP]], [[MPMP-CLA]], [[TESTING]]
