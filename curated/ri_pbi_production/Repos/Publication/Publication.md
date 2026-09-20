# Publication

`ri_pbi_publication` — the Power BI PBIP project reporting on Monash's **research publications and outputs**. Part of [[Overview|RI PBI Production]].

It blends two source systems that were never designed to meet: **PURE**, the research-information system that knows about publications, journals, outputs and organisations; and **iLab**, the facility booking and billing system that knows who used which RI platform. Joining them is what lets the report answer its central question — *which research output came out of which piece of research infrastructure* — and slice output volume and quality (Q1 outlet rate, peer-review rate, collaboration rate) by researcher, award, journal, faculty, platform and time.

## Headline figures

Verified against TMDL on 2026-09-01.

| | |
|---|---|
| Semantic model folder | `ri_publication.SemanticModel` |
| Tables | 14 — 3 fact, 7 dimension, 1 local reference, 1 date, 2 measure/calculation-group containers |
| Relationships | 17, all single-direction, none inactive; 4 many-to-many |
| Measures | 21 in `key_measures`, plus 4 calculation items in `Time intelligence` |
| RLS roles | 61 — 60 platform/facility, 1 unfiltered `TESTING` |

Two of those figures make Publication an outlier in the suite: it has the **largest role roster** of any repo, and it is the only repo built on **three fact tables** rather than one star schema.

## Why it is not a single star schema

The three facts arrive from different systems at different grains, and they share *some* but not all dimensions:

- **`fact_pure`** — one row per PURE publication ↔ equipment/facility/award link.
- **`fact_research_output`** — one row per PURE research output attributed to a researcher. Despite being fetched from the `ri_ilab` Databricks schema under the table name `research_output`, this is PURE data, not iLab data — a naming artifact of the source pipeline that reliably misleads on first reading.
- **`fact_ilab_charges_award_researcher`** — one row per iLab facility charge line, attributed to an award and researcher.

The consequence that shapes everything else: **`fact_research_output` has no relationship to `dim_ri_master_list` at all.** There is no path through the model's relationships from a PURE research output to the RI platform that produced it. The other two facts each reach the master list, but by *different keys* — `ILAB_CORE_NAME` from iLab and `PURE_FACILITY_ID` from PURE — so they do not share a single RI-platform filter path either.

That gap is not an oversight waiting to be filled in a measure; it is the reason `researcher_publication` exists, matching researcher and year across two unrelated facts with `CONTAINS` in place of a relationship. Anything you write that crosses facts inherits this problem. Be explicit about which fact and which key you are filtering through.

## Detail notes

- [[Publication Data Model]] — the three facts, all 14 tables' columns, the 17 relationships, and the M/Power Query flow
- [[Publication Measures]] — all 21 measures and the 4 calculation items, the `(app)`/`(pure)`/`(ilab)` suffix convention, and the measures whose names don't match their logic
- [[Publication RLS]] — the 61 roles, the single uniform filter pattern, and the `TESTING` gap
- [[Publication Gotchas]] — the stale `journal_list.csv` path, dead code, and open questions for the model owner

## See also

- [[Overview|RI PBI Production]] — workspace map of all 7 repos
- [[Shared Conventions]] — PBIP layout, Databricks source pattern, centralised measures
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the shared identity table this repo joins on two different keys
- [[RLS Patterns]] — how row-level security is built across the suite
- **Derived layer** (`graphify/`, never hand-edited): [[ri_pbi_publication]], [[ri_pbi_publication Repository]], [[_COMMUNITY_PURE Publication Records]], [[fact_pure_1]], [[fact_research_output_1]], [[fact_ilab_charges_award_researcher_1]], [[dim_ri_master_list_6]], [[journal_list]], [[Hardcoded and External Data Path Dependencies]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[dim_ri_master_list_2]], [[research_output]]
