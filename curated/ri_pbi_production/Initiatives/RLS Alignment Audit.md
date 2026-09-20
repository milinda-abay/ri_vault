# RLS Alignment Audit

A static, file-level audit of row-level security (RLS) across all 7 repos in [[Overview|RI PBI Production]], written up in `RLS_Alignment_Report.md` at the workspace root.

> [!warning] Superseded — read the findings, not the role names
> This note is marked `status: superseded`, and that is a statement about the document rather than about the problems it found. Two things aged out from under it:
>
> 1. **Its naming findings were overtaken by [[RLS Role Naming Normalization]]**, which checked role literals against live master-list data — something this audit explicitly did not do. Where the two disagree about what a role is called, the normalization work is later and better grounded.
> 2. **Its §3.4 detail table and Appendix A matrix are known stale.** They still carry pre-2026-08-06 file names for everything except one footnoted `HMST` case, and were never updated for the 2026-08-10 manual pass. Role names quoted below — `DMSE`, `DMAE`, `DCE` among them — no longer exist under those names.
>
> Specifically, `RLS_Alignment_Report.md` does not reflect any of these, all verified against TMDL on 2026-09-01:
>
> | What changed | Where | The report still shows |
> |---|---|---|
> | Six `FENG-*` roles renamed to `ENG-*`, **filter values rewritten too** | [[Awards RLS]] | `FENG-DCE` etc., and a 46-role roster |
> | Five engineering roles renamed to `ENG-*`; `DMSE` replaced by `ENG-DMSE` with its **filter column** switched `CAPABILITY_CODE` → `NODE_ID` | [[iLab Utilisation RLS]] | `DCE`, `DCHME`, `DECSE`, `DMAE`, `DMSE`, `FETS` |
> | `HELIX` kept its name but had **both filter values** corrected to `MERC-HELIX` | [[iLab Utilisation RLS]] | the pre-fix values |
> | `NANO` renamed to `MCN` | [[Awards RLS]] | `NANO` |
> | `NANO` **deleted** in favour of the existing `MCN` | [[Publication RLS]] | `NANO`, and a 62-role roster |
>
> The last row matters beyond naming: the report's Publication count of 62 is wrong, and the `CLAUDE.md` files repeat it. The current figure is 61 — see [[RLS Patterns]].
>
> **What is not superseded is the structural findings**: the unsecured facts in [[Awards RLS]] and [[Publication RLS]], the unfiltered `TESTING` roles, [[Asset]]'s missing RLS, and the filter-column divergence. None has been repaired, and the naming campaign explicitly placed all of them out of its own scope. Treat those as live.
>
> Verify any specific finding against current TMDL before relying on it — see [[RLS Patterns]] for the re-derived per-repo position, and [[#Status since the audit]] below for what had already moved by 2026-08-26.

## Purpose

RLS in this suite is meant to follow one convention: roles filter `dim_ri_master_list` (or a repo-specific equivalent) using its columns, and only [[iLab Utilisation RLS]] is permitted to use additional securable tables. The audit checked whether the 7 repos actually hold to that convention, and — separately — whether the filters that exist actually *reach* every fact table they're meant to secure. It's the diagnostic that the [[RLS Role Naming Normalization]] initiative was scoped from (see its brainstorming prompt, `docs/superpowers/prompts/2026-08-06-rls-alignment-brainstorming-prompt.md`, grounded in a fresh TMDL read on 2026-08-06).

## Scope and method

- **Static file audit only** — no live model connection (`pbi connect`) was used. It parsed `roles/*.tmdl`, master-list table definitions, and `relationships.tmdl` across all 7 repos.
- Parsed all 280 `roles/*.tmdl` files (324 `tablePermission` filters total, including 3 multi-line DAX filters in ilab), cross-checked every filter column against the target table's TMDL column definitions, and traced RLS propagation through each repo's `relationships.tmdl` (cardinality, cross-filter direction, active vs. inactive).
- **Baseline finding**: everything mechanical checked out — all 324 filters parse cleanly, every filter column exists in its target table, and role file names match role names everywhere. The findings below are about *design* (does the filter reach the right facts, is the convention followed, are rosters consistent), not malformed TMDL.

## Key findings

### High severity

1. **[[Awards RLS]] — RLS doesn't secure the core facts.** `dim_ri_master_list` has exactly one relationship in the awards model: `fact_ilab.core_name -> dim_ri_master_list.ILAB_CORE_NAME` (many-to-many, single direction). All 46 platform roles filter that table, but `fact_research_award_funding` and `fact_research_income` have no path to it at all — their dimensions (`dim_awards`, `dim_research_funding_scheme`, `dim_finance_fund`, etc.) don't connect, and an inactive `fact_ilab → fact_research_income` relationship doesn't help (inactive relationships are ignored by RLS). **Impact: every role sees all award and income data**; only iLab charge rows are actually restricted. Suggested fix: add a relationship chain (e.g. via `COST_CENTRE`, as finance does) or extend role filters directly.

2. **[[Publication RLS]] — `fact_research_output` unsecured.** `dim_ri_master_list` correctly secures `fact_pure` (via `PURE_FACILITY_ID`) and `fact_ilab_charges_award_researcher` (via `ILAB_CORE_NAME`), but `fact_research_output` only connects to `dim_researcher`, `dim_journal`, `dim_output_type`, `dim_research_output`, `dim_research_organisation`, and `Calendar` — none of which link back to the master list. **Every role sees all research-output rows.** Flagged as a gap if output visuals are meant to be platform/faculty-scoped; needs confirmation either way.

3. **Unfiltered `TESTING` roles.** [[Finance RLS|Finance]], [[Publication RLS]], and [[Risk RLS|Risk]] each carry a `TESTING` role with `modelPermission: read` and no `tablePermission` at all — full unrestricted access to anyone mapped to it. Flagged as likely dev leftovers. The follow-on normalization work already has explicit sign-off to **delete** these three roles (the one deletion exception to an otherwise additive/rename-only plan).

### Medium severity

4. **[[Asset]] has zero RLS roles**, the only repo with none. Its `dim_ri_master_list` copy already carries `RLS_FACILITY_GROUP` / `RLS_FACULTY_GROUP` columns that exist for exactly this purpose but are unused — suggesting RLS was anticipated but never built. Whether asset-cost data needs per-platform scoping is unconfirmed.

5. **[[Survey RLS|Survey]] filters `DIM_FACILITY`, not `dim_ri_master_list`** — a literal violation of the stated convention, though the workspace `CLAUDE.md` records it as by-design. Consequence: survey role codes are `SURVEY_CAPABILITY_ID` values that don't line up cleanly with other repos (survey's `MARP` enumerates 11 `MARP-*` facility IDs; `MERC` enumerates 4 including `MERC-HELIX`, which is a *separate* role in finance and `HELIX` in ilab). `DIM_FACILITY` also structurally lacks a `CAPABILITY_CODE` column, so this is a hard constraint, not just a naming quirk — the normalization work is explicit that survey stays on `SURVEY_CAPABILITY_ID` and does not get a schema change.

6. **Filter column differs by repo** — role codes are not interchangeable across reports:
   - awards: `ILAB_CAPABILITY_ID` (all 46)
   - finance / ilab: three-column scheme — `CAPABILITY_CODE` (capability-wide roles), `NODE_ID` (site/node roles), `CAPABILITY_GOVERNANCE` (`*-ADMIN` roles)
   - publication, risk: `CAPABILITY_CODE`
   - survey: `SURVEY_CAPABILITY_ID`, plus `CAPABILITY_GOVERNANCE` for admin roles
   
   The finance/ilab three-column mix is systematic (by role granularity), not accidental — but the divergence between repos means the same role *name* can filter a semantically different key depending on which report you're in.

7. **Role rosters and naming are inconsistent across repos.** 105 distinct role names exist across the 6 RLS-enabled repos; only **11 appear in all six** (`CRYO`, `MADP`, `MARP`, `MCAM`, `MCEM`, `MFGP`, `MGMP`, `MHP`, `MMCP`, `MMPP`, `MXP`). Notable naming-collision families for the same organisational unit, each needing normalization:
   - Engineering depts: `FENG-DCE`/`FENG-DCHME`/… (awards, survey) vs. bare `DCE`/`DCHME`/… (ilab)
   - FlowCore: `FLOW` (publication, risk) vs. `FLOW-ARA`/`FLOW-CLAYTON`/`FLOW-MHTP` (awards, finance, ilab, survey)
   - Monash Biomedical Imaging: `MBI` (awards, ilab, publication, risk) vs. `MBI-ARA`/`MBI-CLA`/`MBI-BP` (finance, survey)
   - Micro Imaging: `MMI` (publication, risk) vs. `MMI-ARA`/`MMI-CLA`/`MMI-MHTP` (awards, finance, ilab, survey)
   - Genomics: `MGBP` (publication, risk) vs. `MGBP-BI`/`MGBP-GEN` (awards, finance, ilab, survey)
   - Proteomics: `MPMP` (awards, ilab, publication, risk) vs. `MPMP-CLA`/`MPMP-CPN`/`MPMP-MIPS` (finance, survey)
   - eResearch/HELIX: `MERC` (most repos) vs. `MERC-HELIX` (finance) / `HELIX` (ilab, as a separate role)
   - Histology: `HMST` (awards, pre-rename ilab) vs. `MMIC`/`MMIC-HMST` (finance, publication, risk, survey) — see rename note below
   
   Publication additionally carries ~22 faculty/school-only roles no other repo has (`ADA`, `AQUA`, `ART`, `LAW`, `EDU`, `IT`, `PHRM`, `MIVP`, `MMTP`, `MUM`, `MWTRP`, `WMP`, `GF`, `MIS`, `MIF`, `MAP`, `MAXIMA`, `BDI`, `BUSECO`, `ENG`, `MNHS`, `SCI`) — the audit and the normalization prompt both treat these as legitimate (publication attributes outputs at faculty level), not drift to fix.

   Awards, publication, and risk also have **no governance/faculty tier at all** — every role in those three repos is a flat platform role, unlike finance/ilab/survey's admin roles filtering `CAPABILITY_GOVERNANCE`. Flagged as the largest structural gap versus the ilab reference design (see [[RLS Role Naming Normalization]]).

### Low severity / informational

- ilab's `DMSE` and `MGBP-BI` roles filter only `dim_facility_master_list`, missing the `dim_ilab_services[facility_id]` filter their ~46 sibling platform roles carry. Data is still restricted via the master-list relationship, but `dim_ilab_services` rows themselves stay visible to these two roles.
- ilab special cases, documented so they aren't "fixed" by mistake: `CENTRAL-ADMIN`/`MNHS-ADMIN` carry a `fact_ilab` DAX `SWITCH` splitting MARP bookings at 1 Jan 2026 (a deliberate handover); `DMAE` filters `fact_ilab` directly for FETS rows in category `"MAE"` alongside its own department; `DVCRE-ADMIN`/`PVCRI-ADMIN` are intentionally unfiltered all-access executive roles (unlike `TESTING`, these look deliberate).
- Operator style is cosmetic but inconsistent: awards/publication/risk/survey use `[col] == "X"`; finance/ilab use `[col] IN {"X"}`. The report suggests standardising on `IN {}` for multi-value roles.
- All master-list relationships are many-to-many, single-direction from master list to fact — works for RLS but implies the master-list key columns aren't unique; worth confirming duplicate keys can't leak rows across platforms. Survey's `DIM_FACILITY → FACT_SURVEY` relationship is the one written in reverse (`bothDirections`) and is called out as worth a live role-impersonated check.

## Limitations (per the report itself)

This was a **static file audit** — it did not verify against a live model. Explicitly out of scope / unconfirmed:

1. Whether each role's literal filter code (e.g. `"FENG-DCE"`, `"ADA"`) actually matches rows in the live master-list data — a typo'd or stale code silently produces an empty, deny-all role.
2. Actual role membership in the Power BI service (especially for `TESTING`, `DVCRE-ADMIN`, `PVCRI-ADMIN`).
3. Effective row counts per role via role-impersonated `EVALUATE` — the definitive test for the awards/publication unsecured-fact findings and the survey relationship-direction question.

Suggested remediation order from the report: fix the awards and publication unsecured-fact findings and delete the `TESTING` roles first, then confirm intent on asset's missing RLS, then align rosters/naming as a longer-term cleanup.

## Status since the audit

- **2026-08-26 (verified against current TMDL):** the total is still **280 role files** across the six RLS repos, but the per-repo split has moved — [[Awards]] 46 → **48**, [[Publication]] 62 → **61** (see [[RLS Patterns]] for the current table). Distinct role names across the six are now **103**, down from 105. The 11 roles present in all six are unchanged (`CRYO`, `MADP`, `MARP`, `MCAM`, `MCEM`, `MFGP`, `MGMP`, `MHP`, `MMCP`, `MMPP`, `MXP`). Two of the naming-collision families in finding 7 have since moved:
  - **Engineering depts** — awards' `FENG-*` and ilab's bare `DCE`/`DCHME`/… have *both* been renamed to `ENG-*`, so those two now agree. [[Survey]] alone still uses `FENG-*`, leaving a two-way split rather than the three-way one the audit found.
  - **Histology** — [[Awards]] now carries **both** `HMST` and `MMIC-HMST` as separate roles, and has added `MMIC-PARK-CLA`, which no other repo has. The old and new names now coexist in one repo.
  - The `FLOW`, `MBI`, `MMI`, `MGBP`, `MPMP` and `MERC`/`HELIX` families are **unchanged** from the audit's description.
  - Also worth recording: awards is no longer single-column. 46 of its 48 roles filter `ILAB_CAPABILITY_ID`, but `MMIC-HMST` and `MMIC-PARK-CLA` filter `NODE_ID` — so finding 6's "awards: `ILAB_CAPABILITY_ID` (all 46)" no longer holds.
- **2026-08-06 (git history, ilab):** ilab's `HMST` role file was renamed to `MMIC-HMST` as the first concrete step of the [[RLS Role Naming Normalization]] work, matching its own `dim_facility_master_list[NODE_ID]` filter value (already `"MMIC-HMST"`, unchanged). This resolves that specific `HMST`/`MMIC-HMST` file-naming clash — but note it's a *different* object from the `MMIC` role's `NODE_ID` filter *value* of `"MMIC-HMST"`, which also exists and is unrelated. The `dim_ilab_services[facility_id]` filter on the renamed role is still literally `"HMST"` and did not change. The other naming clashes (`FENG-DCE` vs `DCE`, `FLOW` vs `FLOW-ARA/CLAYTON/MHTP`, `MBI` vs `MBI-ARA/MBI-CLA`) remain open.
- **2026-09-15 (`ri_pbi_production` export):** two changes bear on findings above. First, iLab's master-list table (referenced in finding 87 below and elsewhere as `dim_facility_master_list`) was renamed to `dim_ri_master_list`, matching the other five RLS-enabled repos — a naming-only change with no effect on filter logic or the `DMSE`/`MGBP-BI` defects it carries forward. Second, and more consequential: Survey's `DIM_FACILITY` table — cited in finding 7 and by [[RLS Role Naming Normalization]] as the reason Survey has no `CAPABILITY_CODE`/`NODE_ID` and was excluded from that initiative — widened from 6 to 25 columns and **now has both columns**. Neither this audit's findings nor the normalization initiative's scope decision have been re-evaluated against that change; see the warning added to [[RLS Role Naming Normalization]].
- The brainstorming prompt that followed this audit (2026-08-06) locked in several scoping decisions for the normalization work worth noting here since they clarify which findings above are "will fix" vs. "out of scope":
  - **Additive/rename only, no deletions** without explicit sign-off — except the three `TESTING` roles, which are pre-approved for deletion.
  - Every rename requires a handover entry (old name → new name) since renaming breaks Fabric role membership bindings; membership remapping itself is out of scope for the TMDL work.
  - ilab's three known filter defects (`DMSE`/`MGBP-BI` missing the second filter, `MGBP-BI` using `NODE_ID` instead of `CAPABILITY_CODE`, `DMAE` filtering `fact_ilab` directly) are recorded as known issues and explicitly **not** being changed as part of normalization — only ilab's role *names* are in scope, not its filter logic.
  - The two high-severity "unreachable fact table" gaps (awards' award/income facts, publication's research-output fact) are **out of scope for the normalization work** — they require model/relationship surgery, not role-file edits — and are carried forward as known live exposure gaps.

## See also

- [[RLS Patterns]] — the RLS shape-variance summary this audit substantiates in detail
- [[Shared Conventions]] — the cross-repo conventions this suite otherwise follows
- [[Overview|RI PBI Production]]
- [[RLS Role Naming Normalization]] — the initiative scoped directly from this audit's findings
- [[Awards RLS]], [[Publication RLS]], [[Finance RLS]], [[Risk RLS]], [[iLab Utilisation RLS]], [[Survey RLS]] — the per-repo RLS notes carrying these findings forward
- [[Asset]] — finding 4, the repo with no RLS at all
- **Derived layer — the report and prompt** (`graphify/`, never hand-edited): [[RLS Alignment Report]], [[Current Role × Repository Matrix]], [[RLS Alignment Across the RI Reporting Suite Brainstorming Prompt]]
- **Derived layer — findings as concept nodes** (`graphify/`, never hand-edited): [[Three-Tier RLS Model]], [[Cross-Repository RLS Key Divergence]], [[Static RLS Audit Limitations]], [[RLS Propagation Through relationships.tmdl]], [[_COMMUNITY_RLS Rename Decisions]], [[Cross-Repository Role Roster Inconsistency]]
