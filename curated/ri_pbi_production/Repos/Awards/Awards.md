# Awards

`ri_pbi_awards` — the Power BI PBIP project reporting on **research awards and funding income**. Part of [[Overview|RI PBI Production]].

It tracks research awards, the SAP research-income postings that follow from them, and the iLab facility charges booked against those awards. Users slice awarded and actual income by scheme, category, funder, fund and fund centre, researcher and time — and, distinctively, ask how much research income is attributable to researchers who actually use RI platforms.

## Headline figures

Verified against TMDL on 2026-09-01.

| | |
|---|---|
| Semantic model folder | `ri_pbi_awards.SemanticModel` |
| Tables | 15 — 3 fact, 8 dimension, 1 date, 1 measure container, 1 calculation group, 1 orphan calculated table |
| Relationships | 16 — 3 many-to-many, 1 inactive (which is also the only bidirectional one) |
| Measures | 11 in `KeyMeasures`, all visible; plus 4 calculation items in `Time intelligence` |
| RLS roles | 48 — all platform-scoped, no faculty tier, no `TESTING` role |

> [!warning] Two path irregularities (verified 2026-09-01)
> Awards is the only repo whose semantic-model folder keeps the `pbi_` infix — `ri_pbi_awards.SemanticModel`, not `ri_awards.SemanticModel` — and the only one whose documentation file is `ri_pbi_awards_documentation.md` rather than `ri_<short>_documentation.md`. Scripts that derive either path from the repo name will miss this repo silently.

## The shape of the model

Three facts, at three different grains, from three different systems:

- **`fact_research_award_funding`** — one row per award-funding line: awarded amounts by scheme and category.
- **`fact_research_income`** — one row per SAP research-income posting: actual, committed and pro-rata income.
- **`fact_ilab`** — one row per iLab charge/booking line, carrying award, researcher and core-facility identifiers.

`dim_awards`, `dim_external_organisation` and `dim_research_funding_category` are shared across two facts each; `dim_finance_fund` and `dim_finance_fund_centre` belong to the income fact alone.

**`dim_ri_master_list` connects only to `fact_ilab`.** That one fact about the relationship graph is the most consequential thing to know about this repo, and it drives two separate problems:

1. **RLS reaches only `fact_ilab`.** The 48 platform roles all filter `dim_ri_master_list`, which has no path — active or inactive — to the award-funding or research-income facts. A platform-scoped user still sees every award and every income posting. This is the high-severity finding in [[RLS Alignment Audit]] §2.1, and it is recorded here rather than fixed. See [[Awards RLS]].
2. **Cross-fact measures work by hand.** The one relationship that would bridge iLab charges to finance income — `fact_ilab[payment_information_cleaned] → fact_research_income[FUND_CENTRE_FUND]` — is **inactive**, and deliberately so, to avoid ambiguous filter propagation between two facts. Rather than activating it with `USERELATIONSHIP`, the headline attribution measure `research_group_income` re-derives the researcher-and-year match manually with `CONTAINS`. See [[Awards Measures]].

## Also worth knowing up front

**The relationship join key and the RLS filter key are different columns of the same table.** The model joins `fact_ilab[core_name] → dim_ri_master_list[ILAB_CORE_NAME]`; the roles filter `[ILAB_CAPABILITY_ID]`. Both live on `dim_ri_master_list`, and confusing them is easy — see [[dim_ri_master_list Reference|dim_ri_master_list]].

**Time comparisons run through a calculation group.** Automatic time intelligence is disabled at the model level (`__PBI_TimeIntelligenceEnabled = 0`), replaced by four `Time intelligence` calculation items.

**Almost nothing is hidden** — one column in the entire model, the `Ordinal` sort-helper on the calculation group. The opposite of [[Asset]].

## Detail notes

- [[Awards Data Model]] — the three facts, all 15 tables' columns, the inactive relationship, and the M flow
- [[Awards Measures]] — all 11 measures and the 4 calculation items, including the duplicate pair
- [[Awards RLS]] — the 48 roles, the split filter column, the fact-coverage gap, and the post-campaign roster churn
- [[Awards Gotchas]] — dead M queries, the orphan calculated table, and the stale `data_path` parameter

## See also

- [[Overview|RI PBI Production]] — workspace map of all 7 repos
- [[Shared Conventions]] — PBIP layout, Databricks source pattern, centralised measures
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the shared identity table, and why its join and filter columns differ
- [[RLS Patterns]] — how row-level security is built across the suite
- **Derived layer** (`graphify/`, never hand-edited): [[ri_pbi_awards]], [[ri_pbi_awards Repository]], [[_COMMUNITY_Research Awards Model]], [[_COMMUNITY_Research Awards Funding]], [[fact_research_award_funding]], [[fact_research_income]], [[fact_ilab_1]], [[Awards dim_ri_master_list]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[dim_awards]], [[dim_finance_fund]], [[dim_finance_fund_centre]], [[dim_research_funding_category]], [[dim_external_organisation]], [[data_path]]
