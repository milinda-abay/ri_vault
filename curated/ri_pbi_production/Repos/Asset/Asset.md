# Asset

`ri_pbi_asset` — the Power BI PBIP project reporting on Monash's **capitalised research-infrastructure asset and equipment costs**, sourced from SAP General Ledger postings. Users slice spend by faculty, cost centre, platform/capability, asset class, age, acquisition value and time. Part of [[Overview|RI PBI Production]].

It is the smallest and cleanest model in the suite, and the only one with **no row-level security at all**.

## Headline figures

Verified against TMDL on 2026-09-01.

| | |
|---|---|
| Semantic model folder | `ri_asset.SemanticModel` |
| Tables | 11 — 1 fact, 8 dimensions, 1 date table, 1 measure container |
| Relationships | 9 — all active, none bidirectional, 1 many-to-many |
| Measures | 6 in `key_measures` — 2 visible, 4 hidden |
| RLS roles | **0 roles** — no `roles/` directory exists |
| Report | 2 pages, 19 visuals |

`README.md` in this repo is the unfilled Azure DevOps default template. The real documentation is `CLAUDE.md` and `ri_asset_documentation.md`.

## Row-level security: none

**`ri_pbi_asset` has no `roles/` directory.** Not an empty one, not one holding a `TESTING` leftover — the folder does not exist, so the model defines no RLS whatever. Every other repo in the suite defines roles under `roles/*.tmdl` ([[RLS Patterns]]).

The absence is not obviously deliberate. `dim_ri_master_list` arrives here with its `RLS_FACILITY_GROUP` and `RLS_FACULTY_GROUP` columns intact, exactly as it does in the repos that *do* use RLS — the schema anticipates row-level security that was never wired up.

> [!warning] This is a recorded audit finding, not just an observation
> [[RLS Alignment Audit]] §3.1 raises it as a **medium-severity** item (finding 4): asset-cost data is visible to every viewer of the report, unrestricted by platform or faculty. The audit's position is that this *may* be fine — capitalised spend may not be sensitive per platform — but that it needs confirming and documenting rather than being left as an accident of omission. **That confirmation has not happened.** Nothing has changed here since the 2026-07-13 audit.

If RLS were ever added, the model is unusually well placed for it: the full 19-column master list loads (nothing is projected away, unlike [[Finance]]), so a role could filter `CAPABILITY_CODE`, `NODE_ID`, `CAPABILITY_GOVERNANCE` or any other identifier without a Power Query change first. The restriction would propagate to the single fact table through the `COST_CENTRE` join. Deciding *whether* to add it is the open question, not *how*.

## The join into the shared master list

`fact_sap_asset_gl_mapping[CostCentre] → dim_ri_master_list[COST_CENTRE]`, flagged `toCardinality: many`. Asset is the repo that joins the shared identity table on **`COST_CENTRE`** — the SAP-native key — where [[Awards]] joins `ILAB_CORE_NAME`, [[Publication]] joins `PURE_FACILITY_ID` and [[Survey]] uses its own facility table. See [[dim_ri_master_list Reference|dim_ri_master_list]].

The same `CostCentre` column also drives the join to `dim_finance_fund_centre`, so it carries two relationships at once. That is the single most important thing to know before touching it — see [[Asset Data Model]].

## Detail note

- [[Asset Data Model]] — the 11 tables, 9 relationships, source flow, full data dictionary and measure inventory

## Known gotchas

Recorded, not repaired.

### `Total Cost` excludes Assets Under Construction

```dax
CALCULATE( SUM(fact_sap_asset_gl_mapping[PostedAmount]), dim_gl_code[GLAccount] IN {"0000152006"}) //,"0000152013"
```

GL account `0000152013` (Assets Under Construction) is **commented out** of the filter, so the report's headline cost figure covers "Other Equipment" only. Anyone expecting total capitalised spend will read the number as wrong.

The hidden `Other Equipment` measure re-filters `Total Cost` to the same `0000152006` and so returns `Total Cost` exactly — a no-op today, and only meaningful once `0000152013` is restored. That pair is the clearest evidence the exclusion was meant to be temporary. Worth confirming with the business owner.

### No hardcoded local-file path — but `File.Contents` is present

The three-repo hardcoded-path hazard ([[Shared Conventions]]) does **not** apply here, and this is the first thing to rule out on a refresh failure.

The nuance: `File.Contents` does appear in this model, inside `process_iLab(filepath)` — but the path is a *parameter*, and nothing calls the function. So there is no hardcoded path and no live local-file dependency. The phrasing used for [[Finance]] ("no M expression calls `File.Contents` at all") would be wrong here; the correct statement is that the one call site is parameterised and dead.

### `EndDate` is a fixed literal

The `calendar` table is bounded by `StartDate` (1966-01-01) and `EndDate` (**2026-12-31**), both date parameter queries holding hardcoded values. The date table simply stops at the end of 2026 and needs a manual edit. Nothing errors when it lapses.

### `dim_finance_fund_centre` inherits SAP naming defects

Two, both carried through from the source and preserved in the model:

- Level 4's code column is `FUND_CENTRE_LEVEL_CODE`, **not** `FUND_CENTRE_LEVEL_4_CODE` — breaking the pattern the other six levels follow.
- Levels 1–5 spell it `..._DESCRPTION` (missing the second "I"); levels 6–7 spell it correctly. **Both spellings are live in the same table.**

Anything written against this table has to match the defect exactly, per level.

### Stale conditional-formatting selectors

Two visuals reference fields that no longer exist under those names — `Entity: "Calendar"/Property: "age_group"` and `Entity: "DIM_VALUE"/Property: "value_grouping"` — leftovers from a prior rename. Harmless, uncleaned.

### Substantial dead M

Eight expressions in `expressions.tmdl` are referenced by nothing, including `dim_platform` (which is annotated `PBI_ResultType = Exception` — it errors rather than merely sitting idle) and a cluster of finance queries that look lifted from [[Finance]]. The compressed `platform_cost_centre` Google Sheets snapshot appears used and is not — the name collides with a join alias. Full list in [[Asset Data Model]].

### One correction to the repo's own documentation

`ri_asset_documentation.md` marks two tables and six columns as hidden that TMDL says are visible, having read the `changedProperty = IsHidden` annotation as the `isHidden` flag. `dim_gl_code` and `dim_asset_class` are not hidden tables, and `dim_ri_master_list` exposes five columns rather than three.

The related claim that both tables are "unused" holds only for the report's visuals. `dim_gl_code[GLAccount]` is filtered by `Total Cost` and `Maintenance Cost` in DAX, so dropping the table would break the headline figure. `dim_asset_class` is genuinely unreferenced. Details in [[Asset Data Model]].

### `.approval_tests_temp/`

Helper Python scripts (`approve_all.py`, `remove_abandoned_files.py`) for an approval-testing workflow on report exports. Not part of the app.

## Where Asset is the good example

Worth knowing, because the suite's notes mostly record defects:

- **A field-usage cleanup pass actually happened here.** 50 columns carry a real `isHidden` flag; `calendar` exposes only `cal_year`; raw join keys and sort helpers are hidden so users browse the readable label. [[Publication]] never had this pass, and Asset is the model to point at when arguing the others could be tidied.
- **The `Databricks_MACE` / `get_table_from_mace(table, schema)` pattern is written most plainly here**, with every live fetch going through the helper and nothing bypassing it — unlike [[Finance]], where four queries hit a different catalog directly. [[Shared Conventions]] describes the pattern; this repo is the reference implementation of it.

## See also

- [[Overview|RI PBI Production]] — workspace map of all 7 repos
- [[Asset Data Model]] — the detail note
- [[Shared Conventions]] — PBIP layout, the Databricks source pattern, centralised measures
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the shared identity table, joined here on `COST_CENTRE`
- [[RLS Patterns]] — row-level security across the suite, and what its absence here means
- [[RLS Alignment Audit]] — §3.1, the medium-severity finding on this repo
- **Derived layer** (`graphify/`, never hand-edited): [[ri_pbi_asset]], [[Asset Model Has No RLS]], [[_COMMUNITY_Finance Data Pipeline]], [[dim_ri_master_list]], [[fact_sap_asset_gl_mapping]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): `dim_platform` *(no node since export `51b1e84`)*, [[platform_cost_centre]], [[File.Contents]]
