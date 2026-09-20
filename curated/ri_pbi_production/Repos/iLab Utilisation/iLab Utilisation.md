# iLab Utilisation

`ri_pbi_ilab_utilisation` — the Power BI PBIP project reporting on **iLab equipment and service utilisation**. Part of [[Overview|RI PBI Production]].

It tracks usage of Monash's iLab-managed research infrastructure: equipment bookings and service requests charged through iLab, by researcher, lab, institute, platform and time. The audience is platform managers, faculty and institute administrators, and central RI governance (DVCRE/PVCRI) watching utilisation, revenue, and researcher and organisation reach.

## Headline figures

Verified against TMDL on 2026-09-01, and reconciled against [[ri_pbi_ilab_utilisation semantic model]] most recently on 2026-09-15: tables, relationships, measures and calculation items all match. (Between the 09-10 and 09-14 reconciliations, four dead queries were deleted from `expressions.tmdl` — see [[iLab Utilisation Data Model]] — with no effect on these counts. On 2026-09-15, the master-list copy's model-side table was renamed from `dim_facility_master_list` to `dim_ri_master_list`, matching the other six repos — see below.) The RLS role count is not in the export and still rests on the 2026-09-01 read. Re-checked 2026-09-19 against `ri_pbi_ilab_utilisation` @ `f8c4a836`: the export is byte-identical to the one reconciled on 2026-09-15 (same source graph, `944e789f`), so these figures stand, though that export cannot show what the new commit changed. The same re-read updated two counts that predated [[Non-iLab Utilisation]]: the 24-column copies, and the workspace map in See also.

| | |
|---|---|
| Semantic model folder | `ri_ilab_utilisation.SemanticModel` |
| Tables | 8 — 1 fact, 3 dimensions, 1 date table, 1 measure container, 1 calculation group, 1 disconnected parameter table |
| Relationships | 4 — three standard many-to-one, one many-to-many; none inactive, none bidirectional |
| Measures | 29 — 28 in `Key Measures`, 1 on `dim_ilab_lab`; plus 8 calculation items in `Time Intelligence` |
| RLS roles | 58 — the largest and most structurally varied role set in the suite |

## What makes this repo different

Structurally it is the **simplest model in the suite** — a single-fact star schema with four relationships, against Publication's three facts and seventeen. Its complexity is all in security.

**RLS here is unlike anywhere else.** iLab is the only repo with more than one securable table, so a platform role must carry **two** `tablePermission` filters rather than one. Roles fall into three tiers that are written differently and are not interchangeable, and several roles deviate even from their own tier. Read [[iLab Utilisation RLS]] before adding or editing a role — copying an existing role as a template without checking its tier is the specific way to get this wrong.

**Its master-list copy is named `dim_ri_master_list`, same as the other six repos, as of 2026-09-15.** Before that it was `dim_facility_master_list` — a naming divergence now resolved by rename, not by this repo adopting a different table. The table is still its own copy in this model, joined on `ILAB_CORE_NAME`, loaded from the same physical Databricks table through the same source expression as the shared object. This copy carries 24 columns: the usual 19 plus five underscore-prefixed SCD columns (`_BUSINESS_KEY`, `_START_TIMESTAMP`, `_EXPIRATION_TIMESTAMP`, `_ROW_ACTIVE_FLAG`, `_SURROGATE_KEY`) — this repo was the first in the suite to carry them; as of 2026-09-15, [[Asset]], [[Awards]] and [[Publication]] carry the same 24-column shape too, and [[Non-iLab Utilisation]] has since 2026-09-18. See [[iLab Utilisation Data Model]] for the columns and [[dim_ri_master_list Reference|dim_ri_master_list]] for the full cross-repo picture, and don't assume column lists carry between repos just because the RI-platform concept and, now, the table name do.

**Almost nothing is hidden.** Three columns in the model as read on 2026-09-01 — `Parameter Fields`, `Parameter Order`, `Ordinal` — all Power BI plumbing. No hidden tables. Six columns have appeared since (the five SCD columns above and `dim_ilab_services[category]`), and whether they are hidden is unverified. The opposite of [[Asset]]'s aggressive field-hiding, so don't port hiding assumptions in either direction.

**Model-level automatic time intelligence is off** (`__PBI_TimeIntelligenceEnabled = 0`), deliberately, in favour of the manual `Time Intelligence` calculation group. Eight calculation items rather than the usual four.

## Detail notes

- [[iLab Utilisation Data Model]] — `fact_ilab`, the three dimensions, all 8 tables' columns, and the M flow including its several dead chains
- [[iLab Utilisation Measures]] — all 29 measures and the 8 calculation items
- [[iLab Utilisation RLS]] — the three tiers, the dual-filter requirement, and the documented deviations
- [[iLab Utilisation Gotchas]] — dead code, the stale MARP date split, and the `model.tmdl` rename trap

## See also

- [[Overview|RI PBI Production]] — workspace map of all the report repos
- [[Shared Conventions]] — PBIP layout, Databricks source pattern, centralised measures
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the shared identity table, now carried under the same name here too
- [[RLS Patterns]] — how row-level security is built across the suite
- **Derived layer** (`graphify/`, never hand-edited): [[ri_pbi_ilab_utilisation]], [[ri_pbi_ilab_utilisation Repository]], [[_COMMUNITY_iLab Data Pipeline]], [[_COMMUNITY_RLS Filter Configuration]], [[_COMMUNITY_iLab Booking Records]], [[dim_facility_master_list]], [[dim_ilab_services]], [[dim_ilab_lab]], [[ilab_award_income_researcher_1]]
