# Awards Gotchas

Known defects, dead code and open questions in [[Awards]]. Everything here is **recorded, not repaired** — listed so it isn't rediscovered, mistaken for a convention, or "corrected" by accident.

> [!warning] Point-in-time snapshot
> Verified against TMDL on **2026-09-01**; dead-code table re-checked against the [[ri_pbi_awards semantic model|2026-09-14 export]]. Re-check before acting on any specific item.

> [!note] Reconciled against [[ri_pbi_awards semantic model]] on 2026-09-19 (`ri_pbi_awards` @ `bea86c95`)
> Checked against the export: the dead-code table matches the expressions no table reaches, and no expression calls `File.Contents`. The `YTD` item's unused `max_day`, the orphan `Table`'s DAX and the identical proportion measures are all as described, and no measure uses `USERELATIONSHIP`. One correction: `#shared` was listed as deleted on 2026-09-14, but it is still in the export, reached by no table. The `data_path` value, the role counts and the hidden flags aren't in the export and rest on the TMDL read.

## RLS does not reach the facts this report is about

The most consequential item in this repo, and the reason it heads this list rather than sitting under RLS alone.

All 48 platform roles filter `dim_ri_master_list`, which has a relationship path to `fact_ilab` and **to nothing else**. `fact_research_award_funding` and `fact_research_income` are unfiltered by any role. A platform-scoped user sees every award and every income posting across all platforms.

It is a model-structure problem, not a role-file problem — no edit to `roles/*.tmdl` fixes it. Full detail, including the seven roles that may additionally be deny-all after the August renames, is in [[Awards RLS]]. Tracked as high severity in [[RLS Alignment Audit]] §2.1.

## No hardcoded local-file path — but a stale parameter that looks like one

Worth stating explicitly, because three repos in the suite *do* have a live path problem and it is the first thing to suspect on a refresh failure.

**No M expression in this repo calls `File.Contents` at all.** So neither the [[Publication]]/[[Risk]] stale-path failure nor [[Survey]]'s dormant chain applies here.

What does exist is an **orphaned `data_path` parameter**, set to:

```
C:\Users\teemo\projects\sap_equipment\data\
```

with alternatives listing `C:\Users\teemo\projects\ATR\` and `C:\Users\maba0001\Projects\ATR\`. None of these is under `ri_pbi_production`, and the `teemo` user and `sap_equipment` project are unrelated to this repo — it was almost certainly copied in with a template. **No expression references it.** It is stale, not a refresh risk, and it should not be mistaken for the hardcoded-path gotcha in [[Shared Conventions]].

## Dead code

Nothing here carries a `queryGroup: decomissioned` label, so these read as live until traced.

> [!note] Four entries removed in the 2026-09-14 export
> `external_organisation`, `ripm_research_income`, `'ri_lakehouse_research_award_funding_equipment (2)'` and `Query1` were deleted from `expressions.tmdl` at `ri_pbi_awards` @ `2ea8ea5b` — they no longer appear in [[ri_pbi_awards semantic model]]'s expression inventory. Kept below, struck through, as a record of what was cleaned up; the remaining rows are still live dead code.

| Expression | Why it's dead |
|---|---|
| ~~`external_organisation`~~ **(removed 2026-09-14)** | Hand-rolled its own `Databricks.Catalogs(...)` call against `lakehouse_bim_prd` instead of using `get_table_from_mace`. `dim_external_organisation`'s live partition sourced from the helper directly, so this expression fed nothing. Bypassed the shared-connection convention **and** was orphaned. |
| ~~`ripm_research_income`~~ **(removed 2026-09-14)** (`queryGroup: dev`) | Reduced a Databricks table to a distinct list of `AWARD_ID`. Ad-hoc dev/QA query. |
| ~~`'ri_lakehouse_research_award_funding_equipment (2)'`~~ **(removed 2026-09-14)** (`queryGroup: dev`) | Filtered to `AWARD_ID = 7278884`, grouped and counted. A one-off debugging query for a single award. |
| `#shared`; ~~`Query1`~~ **(removed 2026-09-14)** | Power Query "New Blank Query" boilerplate stubs. `#shared` is still defined: an earlier version of this note listed it as removed, but it is in the export at `bea86c95` (2026-09-19), reached by no table. |
| `fetch_task` | Opens with ~7 lines of commented-out legacy M referencing columns (`"Paid"`, `"Invoice date"`, `"PURE ID"`) that exist in no table here, followed by a working generic text-cleaning function that nothing calls. |
| `fix_columns`, `TableType`, `lowercase_col_names`, `preprocess_table_text`, `fix_table_column_type`, `preprocess_table_datetime` | The rest of the `functions` query group. Inherited boilerplate; no live partition calls any of them. |

**Dead code inside live definitions:** the `YTD` calculation item computes a `max_day` variable it never references — the same leftover [[Publication]] carries in its own `YTD` item.

## The orphan calculated table

`tables/Table.tmdl` is a calculated table named, literally, `Table`. It:

- duplicates the same `CALCULATETABLE(SUMMARIZE(...))` shape used inside the `research_income` measure,
- has **no relationships** to anything in the model,
- carries no annotation explaining its purpose,
- and is not referenced in `model.tmdl`'s query order in any load-bearing way.

Its two columns (`RESEARCH_INCOME_ID`, `ACTUAL_AMOUNT`) are inferred from `fact_research_income`. It reads as a debugging or scratch artifact someone left behind. It is one of the 15 tables and it is visible in the Fields pane, so report users can see it.

## Duplicate measures

`Proportion of Research Income from Platform Users (%)` and `Research Income from Platform Users (%)` have the **identical** definition — `DIVIDE([research_group_income], [research_income])` — differing only in TMDL formatting. Almost certainly a leftover from a rename where the old measure was not deleted.

**Which one visuals are bound to is unconfirmed.** Check the PBIR definition before removing either. See [[Awards Measures]].

Related: `monash_income` is referenced by no other measure and is not the denominator of either proportion measure (that is `research_income`). It is either an unused alternative denominator or bound directly to a visual — also unconfirmed.

## Open questions for the model owner

- **Calendar year against financial year.** `research_group_income` matches `fact_ilab[completion_year]` to `fact_research_income[FINANCIAL_YEAR]` with `CONTAINS`. A calendar year and an Australian financial year are not the same window; whether the resulting attribution is intended needs confirming. See [[Awards Measures]].
- **Which proportion measure is live**, and whether `monash_income` is used at all.
- **Whether the inactive relationship should exist.** `fact_ilab[payment_information_cleaned] → fact_research_income[FUND_CENTRE_FUND]` is never activated by any measure — the one measure that would need it re-derives the match by hand instead. It is either a design intent nothing implemented, or a relationship that should be removed.

## Nothing is hidden

Not a defect, but it shapes the Fields pane and is easy to misread as curation.

**No table is hidden, and exactly one column is** — `Ordinal` on the `Time intelligence` calculation group, a sort helper. Every join key and every audit column on every fact and dimension is visible to report users, including the orphan `Table` above.

[[Asset]] takes the opposite approach, hiding two entire dimension tables and most raw columns. Don't port hiding assumptions in either direction.

## See also

- [[Awards]] — the repo entry note
- [[Awards RLS]] — the fact-coverage gap and the possibly-empty roles in full
- [[Awards Data Model]] — the relationship graph and the M source flow
- [[Awards Measures]] — the duplicate pair and the cross-fact workarounds
- [[Shared Conventions]] — the suite-wide hardcoded-path gotcha this repo avoids
- **Derived layer** (`graphify/`, never hand-edited): [[_COMMUNITY_Research Awards Funding]], `external_organisation` *(no node since export `51b1e84`)*, [[dim_external_organisation]], `ripm_research_income` *(no node since export `51b1e84`)*, [[fetch_task]], [[fix_table_column_type]], [[preprocess_table_datetime]], [[_COMMUNITY_Table Type Preprocessing]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): `Query1` *(no Awards node; the graph's `Query1_1` is Risk's)*, [[TableType]], [[fix_columns]], [[lowercase_col_names]], [[preprocess_table_text]], [[get_table_from_mace_1]], [[data_path]]
