# Awards RLS

Row-level security for [[Awards]], defined in `ri_pbi_awards.SemanticModel/definition/roles/*.tmdl`. **48 roles, 48 filters** — one per role, all on `dim_ri_master_list`. Verified against TMDL on 2026-09-01.

> [!warning] Point-in-time snapshot — as at 2026-09-01
> This roster has moved more than any other in the suite during 2026-08 — two roles added, seven renamed with their filter values rewritten. Re-derive from `roles/*.tmdl` rather than quoting this note as current.

## The pattern

Every role is platform-scoped, single-filter, exact-match:

```tmdl
role MBI
	modelPermission: read

	tablePermission dim_ri_master_list = [ILAB_CAPABILITY_ID] == "MBI"
```

**There is no faculty or governance tier here, and no `TESTING` role.** Awards is one of three repos with a completely flat roster — every role is a platform. Contrast [[Finance]], [[Survey]] and [[iLab Utilisation]], which each carry `CAPABILITY_GOVERNANCE`-filtered admin roles, and [[Finance]]/[[Publication]]/[[Risk]], which each carry an unfiltered `TESTING` leftover.

Two invariants hold across all 48 and are worth relying on:

1. **Every role's filter value is identical to its own file name.** Verified across all 48.
2. **Every filter uses `==`**, not `IN {…}`, and matches exactly one value.

## The filter column is no longer uniform

This changed in August 2026 and is the thing most likely to break a script:

| Filter column | Roles |
|---|---|
| `ILAB_CAPABILITY_ID` (46) | `BCIF`, `BDI-INF`, `BDI-OP`, `BLTB`, `CRYO`, `DSAIP`, `ENG-DCE`, `ENG-DCHME`, `ENG-DECSE`, `ENG-DMAE`, `ENG-DMSE`, `ENG-FETS`, `FLOW-ARA`, `FLOW-CLAYTON`, `FLOW-MHTP`, `HMST`, `IRT`, `MADP`, `MARP`, `MBBL`, `MBI`, `MCAM`, `MCEM`, `MCN`, `MCSPEC`, `MDDP`, `MDMF`, `MFGP`, `MFI`, `MGBP-BI`, `MGBP-GEN`, `MGMP`, `MHP`, `MIPSCEM`, `MIPSIF`, `MMCP`, `MMI-ARA`, `MMI-CLA`, `MMI-MHTP`, `MMPP`, `MPMP`, `MPPU`, `MRNA`, `MUARC`, `MXP`, `SOC` |
| `NODE_ID` (2) | `MMIC-HMST`, `MMIC-PARK-CLA` |

Both `NODE_ID` roles were added on 2026-08-24, after the role-naming campaign closed. **Do not assume a single filter column when scripting against this repo's roles** — and when adding one, confirm which column the new code actually lives in before copying the dominant pattern. See [[dim_ri_master_list Reference|dim_ri_master_list]] for why the two columns hold different values for the same unit.

Note also that this repo now carries **both `HMST` and `MMIC-HMST`** as separate roles, filtering different columns.

## RLS does not secure the award or income facts

This is the high-severity finding in [[RLS Alignment Audit]] §2.1, and it follows entirely from the relationship graph rather than from anything in the role files.

`dim_ri_master_list` has exactly one relationship in this model — `fact_ilab[core_name] → dim_ri_master_list[ILAB_CORE_NAME]`. There is **no path**, active or inactive, to `fact_research_award_funding` or `fact_research_income`. Their dimensions do not connect to the master list, and a filter cannot flow backwards out of `fact_ilab` through `dim_awards` into another fact. The inactive `fact_ilab → fact_research_income` relationship does not help either: **RLS ignores inactive relationships.**

So all 48 roles restrict `fact_ilab` and nothing else.

**A member of any platform role sees the complete award-funding and research-income dataset, for every platform.** Only iLab charge rows are actually scoped. Given that awards and income are what this report is *about*, that is the widest exposure gap in the suite.

Fixing it means model surgery — a relationship or chain linking the award and income facts to the master list, as [[Finance]] does via `COST_CENTRE`, or extending each role's filter to those tables. That is out of scope for role-file work, which is why the naming-normalisation initiative explicitly carried it forward rather than addressing it. **Recorded here, not fixed.**

Note the extra subtlety: the relationship joins on `ILAB_CORE_NAME` while the roles filter `ILAB_CAPABILITY_ID` — two different columns of the same table. The filter still works, because filtering any column of `dim_ri_master_list` restricts its rows and the relationship propagates from there. But it means the column a role names and the column that carries the restriction to the fact are not the same one.

## Roster history

The role-naming campaign parsed a 46-role roster here and renamed **none** — its mapping records 46 `no-change` and one flagged (`NANO`). Everything that has since changed happened in three manual passes outside the pipeline, taking the count from 46 to its current 48:

| Date | Change | Beyond the naming-only constraint? |
|---|---|---|
| 2026-08-10 | `NANO` renamed to `MCN` (`9d25753`), resolving the flagged item | Rename only |
| 2026-08-10 | Six `FENG-*` roles renamed to `ENG-*` (`35d7134`, "Update RLS to match with other reports") — **which also rewrote each filter value**, `[ILAB_CAPABILITY_ID] == "FENG-DCE"` → `"ENG-DCE"` | **Yes** — behaviour changed, not just labels |
| 2026-08-24 | `MMIC-HMST.tmdl` and `MMIC-PARK-CLA.tmdl` **added** (`20c6c75`, "WIP"), both filtering `NODE_ID` | **Yes** — the constraint forbids additions outright |

[[RLS Role Naming Normalization]] records the full detail. The practical point: **commits that read as renames changed access behaviour**, so a role's history is not a safe guide to what it currently filters.

`RLS_Alignment_Report.md` has not been updated for any of this. Its §3.4 table and Appendix A still show `FENG-*` and a 46-role roster.

## The renamed roles may now be empty

> [!warning] Unverified — needs a live query (as at 2026-09-01)
> Seven roles filter `ILAB_CAPABILITY_ID` on values that the master-list extract holds only in a **different column**.

The 2026-08-10 pass rewrote both the names and the filter values of the six engineering roles from `FENG-*` to `ENG-*`, and `NANO` to `MCN`. But in `docs/rls-role-naming/data/master-list-values.csv`, the `ILAB_CAPABILITY_ID` column still contains `FENG-DCE`, `FENG-DCHME`, `FENG-DECSE`, `FENG-DMAE`, `FENG-DMSE` and `FENG-FETS`. The `ENG-*` spellings live in `NODE_ID`. `MCN` appears in neither.

A filter value that does not exist in the data produces a **deny-all role** — the member sees nothing, and the model reports no error ([[RLS Patterns]]). If the source table was not updated alongside the rename, these seven roles are empty:

`ENG-DCE`, `ENG-DCHME`, `ENG-DECSE`, `ENG-DMAE`, `ENG-DMSE`, `ENG-FETS`, `MCN`

The extract is itself a point-in-time capture from the campaign, so the live table may have moved since. **This cannot be settled from files** — it needs a role-impersonated query against the live model, which is also the first unverified limitation [[RLS Alignment Audit]] lists. Recorded, not fixed.

The comparison cuts the other way too: [[iLab Utilisation]]'s equivalent roles kept `FENG-*` on their `dim_ilab_services` half precisely because that is iLab's own coding, and switched only the master-list half to `NODE_ID`. This repo switched the value but kept the column.

## Adding a role

1. **Confirm which column the code lives in** — `ILAB_CAPABILITY_ID` or `NODE_ID` — before copying the dominant pattern. Getting this wrong produces a deny-all role that reports nothing.
2. **Follow the single-filter `==` form** on `dim_ri_master_list`. There is no second securable table here, unlike [[iLab Utilisation]].
3. **Name the file after the filter value.** The invariant holds across all 48; keep it.
4. **Remember the role will not scope awards or income** — only `fact_ilab`. Do not assume a new role restricts what the report principally shows.
5. **Renaming breaks Fabric role membership.** Every rename needs a handover entry.

## See also

- [[Awards]] — the repo entry note
- [[Awards Data Model]] — the relationship graph this gap follows from
- [[RLS Patterns]] — role shapes and filter columns across the whole suite
- [[RLS Alignment Audit]] — the cross-repo audit, including §2.1's finding above
- [[RLS Role Naming Normalization]] — the campaign and its out-of-scope manual follow-ups
- [[dim_ri_master_list Reference|dim_ri_master_list]] — why `ILAB_CAPABILITY_ID` and `NODE_ID` hold different values
- **Derived layer** (`graphify/`, never hand-edited): [[ri_pbi_awards Role Catalog (46 roles)]], [[ri_pbi_awards FENG- to ENG- Role Rename]], [[ri_pbi_awards NANO to MCN Role Rename]], [[ri_pbi_awards MMIC-PARK-CLA Role Addition]], [[Awards NANO Not Found in Master List]], [[Awards RLS Coverage Gap]], [[_COMMUNITY_MMIC-PARK-CLA Access Role]], [[Awards dim_ri_master_list]], `ILAB_CAPABILITY_ID` *(no Awards node; the graph's `ILAB_CAPABILITY_ID_2` is Survey's)*, `NODE_ID` *(no Awards node; the graph's `NODE_ID_2` is Asset's)*, [[ri_pbi_awards Role Naming Mapping]], [[ri_pbi_awards RLS Role Rename Handover]]
- **Derived layer — the unsecured facts** (`graphify/`, never hand-edited): [[fact_research_award_funding]], [[fact_research_income]], [[fact_ilab_1]], [[dim_awards]]
