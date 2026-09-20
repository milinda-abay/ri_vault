# Finance RLS

Row-level security for [[Finance]], defined in `ri_finance.SemanticModel/definition/roles/*.tmdl`. **36 roles, 35 filters** — all on `dim_ri_master_list`, but across **three different columns**. Verified against TMDL on 2026-09-01.

> [!warning] There is no repo-wide default here (as at 2026-09-01)
> This is the repo where "match the pattern actually in use" matters most. A new role must copy the shape of the roles it sits beside, not a suite-wide convention. Defaulting to `CAPABILITY_CODE` because [[Publication]] and [[Risk]] use it will produce a role that grants nothing, or the wrong rows.

## Three groups, three columns

| Group | Count | Filter | Roles |
|---|---|---|---|
| Whole-platform | **16** | `[CAPABILITY_CODE] IN {"<CODE>"}` | `CDCO`, `CRYO`, `MADP`, `MARP`, `MCAM`, `MCEM`, `MCN`, `MERC`, `MFGP`, `MFP`, `MGMP`, `MHP`, `MMCP`, `MMIC`, `MMPP`, `MXP` |
| Sub-node / site | **15** | `[NODE_ID] IN {"<CODE>"}` | `FLOW-ARA`, `FLOW-CLAYTON`, `FLOW-MHTP`, `MBI-ARA`, `MBI-CLA`, `MERC-HELIX`, `MGBP-BI`, `MGBP-GEN`, `MMI-ARA`, `MMI-CLA`, `MMI-MHTP`, `MMIC-HMST`, `MPMP-CLA`, `MPMP-CPN`, `MPMP-MIPS` |
| Faculty / governance | **4** | `[CAPABILITY_GOVERNANCE] IN {"<GROUP>"}` | `CENTRAL-ADMIN`, `ENG-ADMIN`, `MIPS-ADMIN`, `MNHS-ADMIN` |
| Unfiltered | **1** | none | `TESTING` |

**The split is systematic, by scope granularity** — not accidental drift. A capability-wide grant filters `CAPABILITY_CODE`; a single-site grant filters `NODE_ID`; a whole-faculty grant filters `CAPABILITY_GOVERNANCE`. [[iLab Utilisation]] uses the same three-column scheme on its own copy of the table; see [[RLS Patterns]].

Two invariants across the 35 filtered roles:

1. **Every role uses `IN { … }`**, not `==` — consistently. Finance and [[iLab Utilisation]] are the two repos with this style; [[Awards]], [[Publication]], [[Risk]] and [[Survey]] use `==`.
2. **Every role filters exactly one value.** There are no multi-value roles here, unlike [[Survey]] and [[iLab Utilisation]].

### Where the role name and the filter value differ

The 31 platform and node roles all filter a value identical to their own file name. **The four admin roles do not** — the `-ADMIN` suffix is not part of the governance value:

| Role | Filters |
|---|---|
| `CENTRAL-ADMIN` | `CAPABILITY_GOVERNANCE IN {"CENTRAL"}` |
| `ENG-ADMIN` | `CAPABILITY_GOVERNANCE IN {"ENG"}` |
| `MIPS-ADMIN` | `CAPABILITY_GOVERNANCE IN {"MIPS"}` |
| `MNHS-ADMIN` | `CAPABILITY_GOVERNANCE IN {"MNHS"}` |

So a new faculty role named `SCI-ADMIN` would filter `"SCI"`, not `"SCI-ADMIN"`. Getting this wrong produces a deny-all role that reports no error.

## What the projection constrains

Finance's `dim_ri_master_list` is **projected to nine columns in M before load** ([[Finance Data Model]]). All three filter columns survive, so every existing role works.

But the `ILAB_*`, `PURE_*`, `SURVEY_*` and `RLS_*` groups never arrive in the model. **A role filtering an iLab, PURE or survey identifier cannot be written here** without widening the projection first — which is worth knowing, because [[Awards]] filters `ILAB_CAPABILITY_ID` and [[Survey]] filters `SURVEY_CAPABILITY_ID`, so a role ported from either repo will not resolve. See [[dim_ri_master_list Reference|dim_ri_master_list]].

## The `TESTING` role — known gap

```tmdl
role TESTING
	modelPermission: read
```

No `tablePermission` block at all. Anyone mapped to it in the Power BI service sees every row of both facts, unfiltered.

The same dev leftover exists in [[Publication]] and [[Risk]]. Recorded here as a **known security gap**, flagged in [[RLS Alignment Audit]] §2.3, and pre-approved for deletion under [[RLS Role Naming Normalization]] — repairing it is separate work.

**Do not use it as a template.** The suite's legitimately unfiltered roles — `DVCRE-ADMIN` and `PVCRI-ADMIN` in [[iLab Utilisation]] — are named and governed; this one is not.

## What RLS here does cover

Both facts are reachable, so there is no unsecured-fact finding in this repo — unlike [[Awards]] and [[Publication]].

`dim_ri_master_list` relates to `fact_finance_forecast_budget_actuals` and `fact_fund_management_financial_summary`, both on `FUND_CENTRE_CODE → COST_CENTRE`. A role restricts master-list rows, and the restriction propagates to both facts along those relationships.

Note the filter column and the join column differ — roles filter `CAPABILITY_CODE`, `NODE_ID` or `CAPABILITY_GOVERNANCE`, while the relationship joins `COST_CENTRE`. That is the same arrangement [[Awards]] has, and it works for the same reason: filtering *any* column of the master list restricts its rows, and propagation happens from the restricted table. The difference is that here the relationships actually reach the facts that matter.

## Rename history — none

Finance's mapping records **zero renames and zero flagged roles**: every role name already matched a live value in its filter column. The handover document records no rename either.

Finance is also unaffected by the 2026-08 manual passes that reshaped [[Awards]] and [[iLab Utilisation]]. Along with [[Risk]], it is one of two rosters unchanged since the 2026-07-13 audit.

One cross-repo note: Finance splits `MERC` into `MERC` and a separate `MERC-HELIX` role. [[iLab Utilisation]] calls the same unit `HELIX`; [[Survey]] folds it inside its `MERC` role; [[Publication]] and [[Risk]] have only the umbrella `MERC`. Four treatments of one unit across five repos — tracked in [[RLS Role Naming Normalization]], not resolved here.

## Adding a role

1. **Decide the scope granularity first** — capability-wide, single site, or whole faculty. That determines the column, and nothing else does.
2. **Look at the roles beside it**, not at another repo. A site role next to `MPMP-CLA` filters `NODE_ID`; a capability role next to `MARP` filters `CAPABILITY_CODE`.
3. **For a faculty role, drop the `-ADMIN` suffix from the filter value.**
4. **Confirm the value exists** in the projected nine columns. A value absent from the data — or in a column the projection dropped — produces a **deny-all role** that reports nothing ([[RLS Patterns]]).
5. **Use `IN { … }`**, matching the repo's consistent style.
6. **Renaming breaks Fabric role membership.** Every rename needs a handover entry.

## See also

- [[Finance]] — the repo entry note
- [[Finance Data Model]] — the master-list join, the projection, and the relationship graph
- [[RLS Patterns]] — role shapes and filter columns across the whole suite
- [[RLS Alignment Audit]] — the cross-repo audit, including §2.3 on the `TESTING` roles
- [[RLS Role Naming Normalization]] — the campaign this repo needed no changes for
- [[dim_ri_master_list Reference|dim_ri_master_list]] — why the three filter columns hold different values
- **Derived layer** (`graphify/`, never hand-edited): [[_COMMUNITY_Finance RLS Roles]], [[ri_pbi_finance Role Catalog (36 roles)]], [[ri_pbi_finance MMIC-HMST Role (NODE_ID=MMIC-HMST)]], [[ri_pbi_finance TESTING Role]], [[dim_ri_master_list]], [[MERC-HELIX]], [[CENTRAL-ADMIN]], [[ENG-ADMIN]], [[MIPS-ADMIN]], [[MNHS-ADMIN]], [[TESTING]], [[ri_pbi_finance Role Naming Mapping]], [[ri_pbi_finance RLS Role Rename Handover]]
- **Derived layer — one node per role file** (`graphify/`, never hand-edited): [[CDCO]], [[CRYO]], [[FLOW-ARA]], [[FLOW-CLAYTON]], [[FLOW-MHTP]], [[MADP]], [[MARP]], [[MBI-ARA]], [[MBI-CLA]], [[MCAM]], [[MCEM]], [[MCN]], [[MERC]], [[MFGP]], [[MFP]], [[MGBP-BI]], [[MGBP-GEN]], [[MGMP]], [[MHP]], [[MMCP]], [[MMI-ARA]], [[MMI-CLA]], [[MMI-MHTP]], [[MMIC]], [[MMIC-HMST]], [[MMPP]], [[MPMP-CLA]], [[MPMP-CPN]], [[MPMP-MIPS]], [[MXP]]
- **Derived layer — the filtered facts** (`graphify/`, never hand-edited): [[fact_finance_forecast_budget_actuals]], [[fact_fund_management_financial_summary]]
