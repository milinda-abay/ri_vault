# Survey

`ri_pbi_survey` — the Power BI PBIP project reporting on **client-satisfaction survey results**. Part of [[Overview|RI PBI Production]].

It covers the annual satisfaction survey of RI platform users: per-question ratings on equipment, service and client interaction, response and completion rates, and the free-text comments people leave alongside them, sliced by platform, client type and year.

## Headline figures

Verified against TMDL on 2026-09-01.

| | |
|---|---|
| Semantic model folder | `ri_survey.SemanticModel` |
| Tables | 17 — the most in the suite: 2 fact, 13 dimension, 1 date, 1 measure container |
| Relationships | 14 — 13 one-directional, 1 both bidirectional **and** many-to-many |
| Measures | 21 — 20 in `Key measures`, 1 stray on `DIM_FACILITY` |
| RLS roles | 55 — 52 platform, 3 faculty; no `TESTING` role |

## The repo that opted out (partially, as of 2026-09-15)

Survey is **the one repo in the suite that does not use `dim_ri_master_list`** as its model-side table name — platform identity comes from its own `DIM_FACILITY` instead. That naming choice is still what makes this repo structurally different from the other six.

> [!warning] Resolved discrepancy — Survey's physical source was repointed on 2026-09-15
> Until the 2026-09-15 export, `DIM_FACILITY` read its own copy of the master list from a **different Databricks schema and a different SQL warehouse** than the other six repos, with **no `get_table_from_mace` helper** — both source queries inlined the full `Databricks.Catalogs(...)` call against schema `ilab` on warehouse `1fb6bc7e83d60086`. As of 2026-09-15, `DIM_FACILITY`'s `base_facility` query calls `get_table_from_mace("ri_master_list", "ri_lakehouse")` on the same warehouse the other six use, and a `Databricks_MACE` record now exists in this repo too. The old path still exists as unloaded expressions (`Merge1`, `ri_lakehouse_ri_master_list`, `ri_lakehouse_ri_master_list (2)`) that no table reaches — see [[pen_research_infrastructure_insights_prd.ilab.ri_master_list]].

`DIM_FACILITY` is built from the *same* `ri_master_list` Databricks source as everyone else's copy, now via the same path, and widened from 6 to 25 columns on 2026-09-15 — up from the old cut-down set of `CAPABILITY_NAME`, `NODE_NAME`(renamed), `CAPABILITY_TYPE`, `CAPABILITY_GOVERNANCE`, `SURVEY_CAPABILITY_ID` plus two computed flags. **It now has `CAPABILITY_CODE` and `NODE_ID`**, which it did not before — the claim that "the identifiers every other repo's roles filter on simply do not exist here" no longer holds for the table's shape, though whether any RLS role has actually started filtering on them is unconfirmed; see [[Survey RLS]] and [[Survey Data Model]]. Whether `DIM_FACILITY` still filters to rows with a non-null `SURVEY_CAPABILITY_ID` (as the pre-2026-09-15 version did) can't be confirmed from this export, since shared-expression bodies like `base_facility`'s aren't captured in it.

Survey was excluded from [[RLS Role Naming Normalization]] on the grounds that there was nothing in this model to normalise role names *against* — that reasoning should be re-checked now that `CAPABILITY_CODE` exists here too, even though it hasn't (yet, as far as this note can tell) changed which column any role actually filters.

## One dimension per question

The other structural signature of this repo. Rather than one shared rating-scale dimension reused across questions, **each survey question gets its own small lookup dimension** — eleven of them, most built from the identical underlying `satisfaction_rating` list:

`DIM_E_TRAINING`, `DIM_E_INSTRUMENT_AVAILABILITY`, `DIM_E_EASE_BOOKING`, `DIM_INSTRUMENT_SATISFACTION`, `DIM_SERVICE_COMPLETION`, `DIM_S_SL_SERVICE_SATISFACTION`, `DIM_C_PERFORMANCE_SATISFY`, `DIM_C_STAFF_INTERACTION`, `DIM_C_FUTURE_INTERACTION`, `DIM_C_PRICE_SATISFY_RATING`, and the orphaned `DIM_SERVICE_COMMUNICATION`.

This is deliberate and stated in the repo's own `CLAUDE.md`. **When adding a survey question, add a rating column to `FACT_SURVEY` and a new dedicated dimension** — do not reuse an existing rating dimension across unrelated questions, even where the scale is identical. It is also most of why this model has 17 tables.

## Detail notes

- [[Survey Data Model]] — the two facts, `DIM_FACILITY`, all 17 tables' columns, and the M flow
- [[Survey Measures]] — all 21 measures, including the three that carry the report
- [[Survey RLS]] — the 55 roles, the `SURVEY_CAPABILITY_ID` filter, and why this repo sits outside the normalisation work

## Known gotchas

Recorded, not repaired. Full detail sits with the relevant note; this is the index.

### The `data_path` parameter points outside the workspace

`data_path` hardcodes `C:\Users\maba0001\projects\ri_insights\data` (alternate: `C:\Repos\ri_insights\data\`), feeding `output\facility.parquet` through `fetch_base_facility`. Neither path is under `ri_pbi_production`; both point at a separate `ri_insights` project.

**It resolves on this machine today — and it is dormant.** `fetch_base_facility` sits in the `DEV` query group with `'fetch_base_facility (2)'` and `Merge1`, and **no table partition resolves through any of them**. `DIM_FACILITY` loads from the Databricks master list instead. So this is not a live refresh risk, and it is not the same failure as [[Publication]]'s and [[Risk]]'s stale `File.Contents` paths, which are wired into live partitions and do not resolve.

What it *is*: an out-of-workspace external dependency sitting one re-enablement away from being a portability and scheduled-refresh problem. If that chain is ever revived, repoint the path via `pbi-cli` partitions tooling first and consider a gateway. See [[Shared Conventions]].

### Orphaned and broken objects

- **`DIM_SERVICE_COMMUNICATION`** is built exactly like its nine sibling rating dimensions but has **no relationship to anything** — `FACT_SURVEY` has no `SERVICE_COMMUNICATION` column to join. Its only consumer is the `'Selected service communication'` measure, and neither appears in any report visual. Debris from a retired survey question.
- **`DIM_FACILITY[Measure]`** — a stray measure attached to the dimension rather than `Key measures`, reading `SELECTEDVALUE(DIM_FACILITY[survey_facility_id])`. **That column does not exist**; the real one is `SURVEY_CAPABILITY_ID`. Non-functional as written, left over from a rename.
- **`'Comments Selected facility'`** is dead: its live body is `BLANK()`, with the original dynamic-title logic commented out and referencing a `facility_code_lvl1` column that no longer exists.
- **Unused M helpers** `clean_table`, `prep_survey_questions`, `prep_base_survey` (`Functions` group), superseded by logic now inlined in the fact partitions.

### Measures that don't do what they're named

- **`Average Performance Rating`** (one of only three measures the report actually shows) averages `[Responses]` — *response volume* — and touches neither `C_PERFORMANCE_SATISFY_RATING` nor `DIM_C_PERFORMANCE_SATISFY`. Its name and its logic disagree. Confirm with the model owner.
- **`'Service (%)'`** computes a `denominator_responses` variable it never uses, and **`'Equipment (%)'`** omits the `REMOVEFILTERS` treatment its otherwise-parallel sibling applies. The two near-identical measures are not actually parallel. See [[Survey Measures]].

### `Calendar` is not marked as a date table

No `dataCategory` or "Mark as Date Table" annotation appears anywhere in the TMDL, and `__PBI_TimeIntelligenceEnabled = 0`. The model still behaves as though it has a date table through the `SURVEY_DATE → cal_date` relationship, but **every column of `Calendar` is reported hidden** and report visuals appear to filter on `FACT_SURVEY[YEAR]` directly instead. Worth confirming in Power BI Desktop whether the flag is set and simply not surfacing in TMDL, or genuinely absent.

`Calendar[cal_mon_yeat_int]` also carries the "yeat" typo in the column name, exactly as [[Publication]] does — preserved verbatim from the M source, and unfixable for the same reason.

### What TMDL says about hiding, and what the documentation says

> [!warning] Discrepancy — needs a check against the live model (TMDL read 2026-09-01)
> The source documentation describes 18 hidden measures, a wholly hidden `DIM_E_EASE_BOOKING`, and every `Calendar` column hidden. **No object anywhere in this model carries an `isHidden` flag in TMDL.** What 31 objects carry is `changedProperty = IsHidden` — a marker that the property was *changed at some point*, not an assertion of its current value. Sibling repos do emit real `isHidden` flags where things are hidden ([[Publication]]'s `Time intelligence[Ordinal]`, for instance), so its total absence here is meaningful.
>
> The 31 markers line up exactly with what the documentation calls hidden: 17 measures in `Key measures`, 1 on `DIM_FACILITY`, 9 `Calendar` columns, 4 on `DIM_E_EASE_BOOKING`. The documentation appears to have read the marker as the flag. Whether these objects are actually hidden in Power BI Desktop can only be settled against the live model. Recorded, not resolved.

## See also

- [[Overview|RI PBI Production]] — workspace map of all 7 repos
- [[Shared Conventions]] — PBIP layout, Databricks source pattern, the hardcoded-path gotcha
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the shared identity table this repo now reads via the same path but still carries under its own `DIM_FACILITY` name
- [[RLS Patterns]] — how row-level security is built across the suite
- **Derived layer** (`graphify/`, never hand-edited): [[ri_pbi_survey]], [[_COMMUNITY_Facility Training Survey]], [[_COMMUNITY_Base RI Survey]], [[FACT_SURVEY]], [[FACT_COMMENTS_1]], [[DIM_FACILITY]], [[Survey RLS Uses DIM_FACILITY]], [[ri_lakehouse_ri_master_list_1]]
- **Derived layer — M queries** (`graphify/`, never hand-edited): [[prep_base_survey]], [[prep_survey_questions]], [[fetch_base_facility]], [[clean_table]], [[satisfaction_rating]], [[Merge1]], [[data_path_1]], [[Calendar_3]], [[DIM_FACILITY_2]], [[DIM_E_TRAINING]]
