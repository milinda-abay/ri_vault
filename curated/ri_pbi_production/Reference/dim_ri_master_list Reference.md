# dim_ri_master_list Reference

The shared reference table for RI platform/capability identity. Seven repos in [[Overview|RI PBI Production]] carry it under that name — [[Asset]], [[Awards]], [[Finance]], [[Publication]], [[Risk]], [[iLab Utilisation]] and, since 2026-09-18, [[Non-iLab Utilisation]] — and [[Survey]] carries a derived variant of it as `DIM_FACILITY`. It is the table every RLS role filters, so its shape determines how [[RLS Patterns|row-level security]] is written across the whole suite.

> [!warning] Point-in-time snapshot
> Column lists, join keys and row statistics below were derived from TMDL and the `docs/rls-role-naming/data/master-list-values.csv` extract on **2026-09-01**. Row-level statistics come from that extract, not a live query.
>
> Column counts, join keys and filter directions were reconciled against the `ri_pbi_production` export on **2026-09-10**, then again on **2026-09-15** after Asset, Awards, Publication, iLab Utilisation and Survey all widened to the table's full 24-column shape and Survey's binding was repointed onto the same physical path as the other six (see Physical source, below); per-report bindings are in [[pen_research_infrastructure_insights_prd.ri_lakehouse.ri_master_list]]. The row statistics were not re-run, and the Databricks side now reports 117 active rows against this extract's 106 — see [[Projects/Databricks/Tables/ri_master_list SCD2 Reference|ri_master_list SCD2 Reference]].
>
> Re-checked against the **2026-09-16** export: only `ri_pbi_asset`'s sub-repo commit moved (`890eeb42` → `738401ea`); the exported graph and every semantic-model node this note draws on are byte-identical to 2026-09-15, so nothing above changed.
>
> Reconciled against the **2026-09-18** export (`0c73b0cf`): the `ri_pbi_asset` (`738401ea` → `be5342dc`) and `ri_pbi_finance` (`d3ff3f2d` → `92742ba7`) sub-repo commits left both exported semantic models byte-identical, so their copies are unchanged. What is new is an eighth consumer, [[Non-iLab Utilisation]], which loads the full 24-column table but relates it to nothing. It is added to the tables below. The graph export renumbered the `_N`-suffixed derived nodes, so the derived-layer links in See also were re-mapped to report by `source_file`. The export was then re-issued at `11a98af`, which changed only `scripts/export-graph.sh` (graph hash and every sub-repo SHA unchanged), so this note is recorded against that commit.
>
> Re-checked 2026-09-19 against the 2026-09-19 export (`ri_pbi_production` @ `f3f3b03c`). The sub-repo commit moved, but the export was rendered from the same source graph (`944e789f`) as the `11a98af` export this note was last reconciled against, and every file under `graphify/ri_pbi_production/` apart from `_meta.md` is byte-identical. So nothing the export shows has changed. It also means the export cannot show what that commit did change. Re-reading the body turned up one miscount, left over from adding the eighth consumer: *The narrowed copies* said "none of the seven", now eight.

## What it actually is: an identifier crosswalk

The table is not a plain dimension. Every source system feeding the RI suite names the same organisational unit differently, and `dim_ri_master_list` is the row-per-unit table that reconciles those names. That is why its columns cluster by *source system* rather than by attribute — shown below as the 19 non-SCD2 columns, since that grouping is unaffected by which reports carry the five `_`-prefixed columns on top:

| Column group | Columns | Whose identifier |
|---|---|---|
| RI capability hierarchy | `CAPABILITY_CODE`, `CAPABILITY_NAME`, `NODE_ID`, `NODE_NAME`, `CAPABILITY_ISO`, `CAPABILITY_TYPE`, `CAPABILITY_GOVERNANCE`, `INDEX` | RI's own two-level scheme |
| SAP / finance | `COST_CENTRE`, `COST_CENTRE_NAME`, `FUND_ID` | SAP cost-centre coding |
| PURE | `PURE_ORGANISATION_ID`, `PURE_FACILITY_ID`, `PURE_FACILITY_NAME` | PURE research-outputs system |
| iLab | `ILAB_CAPABILITY_ID`, `ILAB_CORE_NAME` | iLab booking system |
| Survey | `SURVEY_CAPABILITY_ID` | client-satisfaction survey tool |
| RLS grouping | `RLS_FACILITY_GROUP`, `RLS_FACULTY_GROUP` | intended for row-level security |

The Databricks table behind it has 24 columns, verified live on 2026-09-11: these 19, plus five `_`-prefixed SCD2 metadata columns (`_BUSINESS_KEY`, `_SURROGATE_KEY`, `_START_TIMESTAMP`, `_EXPIRATION_TIMESTAMP`, `_ROW_ACTIVE_FLAG`). `INDEX` is a dead column there — the pipeline stopped maintaining it on 2026-08-25 but never dropped it, so every current row still carries a stale pre-2026-08-25 value and any future row will carry `NULL` (see [[Projects/Databricks/Tables/ri_master_list SCD2 Reference|ri_master_list SCD2 Reference]]). An earlier version of this note said `INDEX` had been dropped and the reports had "not caught up" by still declaring it; that was wrong. What the reports should stop *relying on* is `INDEX`'s value, which no longer means anything.

As of the 2026-09-18 export, **six of the eight copies carry all 24 columns**, matching the table exactly: [[Asset]], [[Awards]], [[Publication]] and [[Survey]] joined [[iLab Utilisation]] in widening to the full shape on 2026-09-15 (previously only iLab Utilisation carried the SCD2 columns), and [[Non-iLab Utilisation]] copied iLab Utilisation's 24-column definition when it was built on 2026-09-18. Only [[Risk]] (19 — the non-SCD2 set) and [[Finance]] (9 — a further hand-picked projection, see below) still carry a narrower copy.

**The identifiers genuinely disagree, which is the whole point of the table.** In the 106-row extract, 36 of the rows where both are populated have `NODE_ID` ≠ `ILAB_CAPABILITY_ID` (for example `ENG-DCE` vs `FENG-DCE`), and 59 rows have `CAPABILITY_CODE` ≠ `NODE_ID` (`FLOW` vs `FLOW-ARA`). A join or an RLS filter is therefore only correct against the column belonging to the system that produced the fact rows.

The two `RLS_*` columns exist for row-level security but **no role in any of the six RLS-enabled repos filters on them** — every role uses `CAPABILITY_CODE`, `NODE_ID`, `CAPABILITY_GOVERNANCE`, `ILAB_CAPABILITY_ID` or `SURVEY_CAPABILITY_ID` instead. They look like an abandoned design.

## Grain and cardinality

One row per capability–node pair, not per capability. From the 106-row extract:

| Column | Distinct values | Populated rows |
|---|---|---|
| `CAPABILITY_CODE` | 61 | 106 |
| `NODE_ID` | 98 | 105 |
| `ILAB_CAPABILITY_ID` | 46 | 71 |
| `CAPABILITY_GOVERNANCE` | 14 | 106 |

`CAPABILITY_CODE` is the coarse level (`FLOW`, `MARP`, `MBI`); `NODE_ID` is the site/node level beneath it (`FLOW-ARA`, `MARP-ARL`, `MBI-CLA`). `ILAB_CAPABILITY_ID` and `SURVEY_CAPABILITY_ID` are sparse — a unit only has one if that system knows about it, which is why iLab-sourced and survey-sourced reports cannot cover every capability.

Because the grain is capability × node, none of these key columns is unique. Every relationship into the table is consequently many-to-many.

## Physical source

All eight repos now read the same physical table (Survey only since 2026-09-15, see the callout below):

```
pen_research_infrastructure_insights_prd.ri_lakehouse.ri_master_list
```

via the `Databricks_MACE` connection record and the `get_table_from_mace` helper (see [[Shared Conventions]]), all on SQL warehouse `5cc645cded66580f`. The M expression wrapping it is named `ri_master_list` in asset, finance, iLab, non-iLab and survey, and `ri_lakehouse_ri_master_list` in awards, publication and risk — same table, two naming habits.

> [!warning] Resolved discrepancy — Survey's binding was repointed on 2026-09-15
> Survey used to be the exception here: its `ri_lakehouse_ri_master_list` expression bypassed the MACE helper entirely, hardcoded a different SQL warehouse (`1fb6bc7e83d60086`), and read from `pen_research_infrastructure_insights_prd.ilab.ri_master_list` (the `ilab` schema, not `ri_lakehouse`) — whether that was the same table under a second schema or a genuinely separate copy was never settled from the files. As of the 2026-09-15 export, `DIM_FACILITY`'s `base_facility` query now calls `get_table_from_mace("ri_master_list", "ri_lakehouse")` on the shared warehouse, same as the other six. The old `ilab.ri_master_list` path still exists in the model as a couple of unloaded expressions (`Merge1`, `ri_lakehouse_ri_master_list`, `ri_lakehouse_ri_master_list (2)`) that no table reaches — see [[pen_research_infrastructure_insights_prd.ilab.ri_master_list]] — but nothing live depends on them.

## Per-repo shape and join key

| Repo | Table name in model | Columns | Fact joined | Join key |
|---|---|---|---|---|
| [[Asset]] | `dim_ri_master_list` | **24** | `fact_sap_asset_gl_mapping.CostCentre` | `COST_CENTRE` |
| [[Awards]] | `dim_ri_master_list` | **24** | `fact_ilab.core_name` | `ILAB_CORE_NAME` |
| [[Finance]] | `dim_ri_master_list` | **9** | `fact_finance_forecast_budget_actuals.FUND_CENTRE_CODE`, `fact_fund_management_financial_summary.FUND_CENTRE_CODE` | `COST_CENTRE` (both) |
| [[Publication]] | `dim_ri_master_list` | **24** | `fact_ilab_charges_award_researcher.core_name`, `fact_pure.equipment_id` | `ILAB_CORE_NAME`, `PURE_FACILITY_ID` |
| [[Risk]] | `dim_ri_master_list` | 19 | `fact_risk_register.CAPABILITY_CODE` | `CAPABILITY_CODE` |
| [[iLab Utilisation]] | `dim_ri_master_list` | **24** | `fact_ilab.core_name` | `ILAB_CORE_NAME` |
| [[Non-iLab Utilisation]] | `dim_ri_master_list` | **24** | *none* | *none* |
| [[Survey]] | `DIM_FACILITY` | **25** | `FACT_SURVEY.FACILITY_ID` | `SURVEY_CAPABILITY_ID` |

Every relationship above is many-to-many with a single filter direction from the master list to the fact — except survey's, which is `bothDirections`.

[[Non-iLab Utilisation]] is the one copy with **no relationship at all**. It loads the table deliberately, staged for facility RLS and a platform slicer, but `pure_silver.fact_application` carries no facility, capability or equipment key to join it on. It also has no RLS roles, so nothing filters it. See that note for why the candidate keys (`PURE_ORGANISATION_ID`, `PURE_FACILITY_ID`) don't work.

[[Publication]] is the only repo joining the table on **two different keys inside one model**: iLab charge rows arrive keyed by `ILAB_CORE_NAME`, PURE rows by `PURE_FACILITY_ID`.

### Finance's column projection

Finance's copy is deliberately narrowed in M, before the table loads, to nine columns — `CAPABILITY_CODE`, `CAPABILITY_NAME`, `NODE_ID`, `NODE_NAME`, `COST_CENTRE_NAME`, `COST_CENTRE`, `CAPABILITY_ISO`, `CAPABILITY_TYPE`, `CAPABILITY_GOVERNANCE`. It drops the `ILAB_*`, `PURE_*`, `SURVEY_*` and `RLS_*` identifier groups, which finance has no facts for. Everything its 35 filtered roles reference survives the projection, so the narrowing is safe — but it means **finance cannot grow a role filtering on an iLab, PURE or survey identifier** without widening the projection first.

The same expression also carries a row filter, `[COST_CENTRE] <> "" or [COST_CENTRE] <> null`, which is a tautology and removes nothing. Recorded as-is; repairing it is separate work.

### The narrowed copies, and Survey's derived one

None of the eight is a different table underneath:

- **[[iLab Utilisation]]** used to be the odd one out on column count (its old `dim_facility_master_list` name carried the same 24 columns while the other six were narrower). As of 2026-09-15 its table was renamed to `dim_ri_master_list` — matching the other six model-side names — and Asset, Awards, Publication and Survey caught up to the same 24-column shape it already carried, so it's no longer an outlier on either axis. Because `ri_lakehouse.ri_master_list` holds only active rows, the five SCD2 columns carry no history here (`_ROW_ACTIVE_FLAG` is always `Y`).
- **[[Risk]]** and **[[Finance]]** are now the exceptions on column count: Risk stayed at the 19-column non-SCD2 shape, and Finance narrows further to 9 (see Finance's column projection, below).
- **[[Survey]]'s `DIM_FACILITY`** is still genuinely derived, not a plain copy: its `base_facility` query loads the same table `get_table_from_mace("ri_master_list", "ri_lakehouse")` (as of 2026-09-15 — previously a separate `ilab`-schema path, see the Physical source callout above) and adds two computed flags (`PLATFORM`, `NON_PLATFORM`); the table's own M then drops the raw `CAPABILITY_NAME` and renames `NODE_NAME` to `CAPABILITY_NAME` in its place. It carries 25 columns in the export — one more than the 24 raw plus computed columns would suggest by simple arithmetic, which isn't resolvable from the TMDL alone since `base_facility`'s own body isn't captured in this export; a live check of the PBIP source would settle it. It does still have a `CAPABILITY_CODE` column now (it didn't before), which removes one constraint the previous version of this note called structural: **verify against the model before assuming survey's roles still can't filter on it.**

So the practical rule stands even though the underlying data is shared: **don't assume the table name or the join key carries between repos.** Read the target repo's `relationships.tmdl` before writing a join, and its `roles/` before writing a filter.

## See also

- [[RLS Patterns]] — how roles filter this table, and why the filter column differs per repo
- [[Shared Conventions]] — the Databricks connection pattern and `get_table_from_mace` helper
- [[RLS Alignment Audit]] — the audit that traced RLS propagation through these relationships
- [[pen_research_infrastructure_insights_prd.ri_lakehouse.ri_master_list]] — the exported upstream node (derived, never hand-edited): which model table in each report loads this table, and through which expression
- [[Projects/Databricks/Tables/ri_master_list SCD2 Reference|ri_master_list SCD2 Reference]] — the upstream producer side in [[Projects/RI iLab/Overview|RI iLab]]: the Databricks table this one is copied from, its SCD2 history and pipeline
- [[Overview|RI PBI Production]]
- **Derived layer — the eight model-side copies** (`graphify/`, never hand-edited; the `_N` suffixes are renumbered on every export, so each is labelled with the report it came from as of `0c73b0cf`): asset [[dim_ri_master_list_3]], awards [[Awards dim_ri_master_list]], finance [[Finance dim_ri_master_list]], publication [[dim_ri_master_list_2]] (and its relationships side, [[dim_ri_master_list_6]]), risk [[dim_ri_master_list_1]], iLab [[dim_ri_master_list_4]], non-iLab [[dim_ri_master_list_5]], survey [[DIM_FACILITY_2]]; plus the workspace-level concept [[dim_ri_master_list]], the old iLab name [[dim_facility_master_list]], [[Capability Master List]], [[_COMMUNITY_Facility Master Attributes]], [[_COMMUNITY_Master List Pipeline]]
- **Derived layer — the M queries that load each copy, and the columns that join to it** (`graphify/`, never hand-edited): `ri_master_list` in survey [[ri_master_list]], iLab [[ri_master_list_1]], asset [[ri_master_list_2]], finance [[ri_master_list_3]], non-iLab [[ri_master_list_4]]; `ri_lakehouse_ri_master_list` in risk [[ri_lakehouse_ri_master_list]], survey (unloaded) [[ri_lakehouse_ri_master_list_1]], awards [[ri_lakehouse_ri_master_list_2]], publication [[ri_lakehouse_ri_master_list_3]]; join columns [[fact_risk_register.CAPABILITY_CODE]], [[fact_sap_asset_gl_mapping.CostCentre]]
- [[ri_pbi_non_ilab_utilisation semantic model]] — the exported model for the eighth consumer
