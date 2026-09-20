# Publication RLS

Row-level security for [[Publication]], defined in `ri_publication.SemanticModel/definition/roles/*.tmdl`. **61 role files** — the largest roster in the suite — verified against TMDL on 2026-09-01.

> [!warning] Point-in-time snapshot — as at 2026-09-01
> Role counts and names move between audits. Re-derive from `roles/*.tmdl` rather than quoting this note as current.

## The pattern

Sixty of the 61 roles are platform or faculty scopes, and every one of them has **exactly one** `tablePermission`, of exactly this form:

```tmdl
role MBI
	modelPermission: read

	tablePermission dim_ri_master_list = [CAPABILITY_CODE] == "MBI"
```

There are no exceptions among the 60 — one table, one column, one value, the `==` operator throughout. Two invariants hold across the whole roster and are worth relying on:

1. **Every role filters `CAPABILITY_CODE`.** No role in this repo uses `NODE_ID`, `CAPABILITY_GOVERNANCE` or any iLab/survey identifier, unlike [[Finance]] and [[iLab Utilisation]], which mix columns by granularity.
2. **Every role's filter value is identical to its own file name.** Verified across all 60 — there is no role here where the name and the code diverge, which is a real hazard elsewhere in the suite (iLab's `MMIC-HMST` filters `"HMST"`, for instance).

This makes Publication the simplest RLS model in the suite to extend, and the safest to reason about. See [[RLS Patterns]] for how the other repos differ.

## Why the roster is the largest

Publication's 60 filtered roles are effectively **one role per `CAPABILITY_CODE` in the master list**. The `docs/rls-role-naming/data/master-list-values.csv` extract holds 61 distinct capability codes; 60 of them have a role, and only `DDD` (MIPS Drug Delivery Disposition and Dynamics) does not. Nothing else in the repo drives the count — the roster is a projection of that column, so it grows and shrinks with the master list rather than with anything in this model.

That also explains the roles other repos don't have. Alongside the RI platforms, the roster carries **faculty- and school-level codes** — `ADA`, `AQUA`, `ART`, `BDI`, `BUSECO`, `EDU`, `ENG`, `GF`, `IT`, `LAW`, `MAP`, `MAXIMA`, `MIF`, `MIS`, `MIVP`, `MMTP`, `MNHS`, `MUM`, `MWTRP`, `PHRM`, `SCI`, `WMP`. These are legitimate here, not drift: research outputs are attributed at faculty level as well as to RI platforms, so a faculty needs a scope in this report even though it has no equipment in the iLab or asset models. The [[RLS Alignment Audit]] reaches the same conclusion and explicitly does not flag them for normalisation.

## Full roster

The 60 filtered roles, each filtering `dim_ri_master_list[CAPABILITY_CODE]` on its own name:

`ADA`, `AQUA`, `ART`, `BCIF`, `BDI`, `BLTB`, `BUSECO`, `CDCO`, `CRYO`, `DSAIP`, `EDU`, `ENG`, `FLOW`, `GF`, `IRT`, `IT`, `LAW`, `MADP`, `MAP`, `MARP`, `MAXIMA`, `MBBL`, `MBI`, `MCAM`, `MCEM`, `MCN`, `MCSPEC`, `MDDP`, `MDMF`, `MERC`, `MFGP`, `MFI`, `MFP`, `MGBP`, `MGMP`, `MHP`, `MIF`, `MIPSCEM`, `MIPSIF`, `MIS`, `MIVP`, `MMCP`, `MMI`, `MMIC`, `MMPP`, `MMTP`, `MNHS`, `MPMP`, `MPPU`, `MRNA`, `MUARC`, `MUM`, `MWTRP`, `MXP`, `PHRM`, `SCI`, `SOBS`, `SOC`, `STM-GEN`, `WMP`

Plus `TESTING`, which is unfiltered — see below.

Where other repos split a unit by site, Publication keeps the umbrella code: `FLOW` here versus `FLOW-ARA`/`FLOW-CLAYTON`/`FLOW-MHTP` in [[Awards]], [[Finance]], [[iLab Utilisation]] and [[Survey]]; `MBI`, `MMI`, `MGBP` and `MPMP` likewise. A user granted `FLOW-ARA` elsewhere has no matching role here, only the broader `FLOW`. That mismatch is a known cross-repo issue tracked in [[RLS Role Naming Normalization]], not something to fix inside this repo.

## The `TESTING` role — known gap

```tmdl
role TESTING
	modelPermission: read
```

That is the whole file. With `modelPermission: read` and **no `tablePermission` at all**, anyone mapped to `TESTING` in the Power BI service sees every row in the model, unfiltered.

The same dev leftover exists in [[Finance]] and [[Risk]]. It is recorded here as a **known security gap**, flagged in [[RLS Alignment Audit]], and pre-approved for deletion under [[RLS Role Naming Normalization]] — repairing it is separate work and out of scope for this note. **Do not use it as a template for a new role**, and do not read it as the "no restriction needed" pattern; the deliberate unfiltered roles in the suite (`DVCRE-ADMIN`, `PVCRI-ADMIN` in iLab) are named and governed, and this one is not.

## What RLS here does *not* cover

Every role filters `dim_ri_master_list`, and restriction reaches a fact only along a relationship. In this model that means:

- `fact_pure` **is** secured, via `equipment_id → PURE_FACILITY_ID`.
- `fact_ilab_charges_award_researcher` **is** secured, via `core_name → ILAB_CORE_NAME`.
- `fact_research_output` **is not secured at all.** It has no relationship to the master list ([[Publication Data Model]]), and filters do not propagate to it through the shared dimensions. Every role sees every research-output row.

This is the high-severity finding in [[RLS Alignment Audit]] §2.2. It is a model-structure problem, not a role-file problem — no amount of editing `roles/*.tmdl` fixes it, which is why it sits outside the naming-normalisation work. Whether outputs are *meant* to be platform-scoped is still unconfirmed with the model owner.

## History

The roster held 62 role files at the 2026-07-13 audit. It is now 61: the `NANO` role file was removed because `MCN` already covered that platform, resolving the item the role-naming mapping had flagged as `flagged-not-found-in-master-list`. No role in this repo was renamed by that campaign — the mapping table records 60 `no-change`, one flagged (`NANO`), and `TESTING` excluded. If `NANO` had AD-group membership in the service, it needed migrating to `MCN`.

## Adding a role

1. Confirm the code exists as a `CAPABILITY_CODE` value in the master list. A value that isn't there produces a **deny-all role** that reports no error — see [[RLS Patterns]].
2. Name the file after the code, exactly. The invariant above is worth preserving.
3. Copy the single-filter `[CAPABILITY_CODE] == "<CODE>"` form. This repo has no variation to account for, unlike [[Finance]] or [[iLab Utilisation]].
4. Remember that a rename breaks AD-group-to-role bindings in Fabric; every rename needs a handover entry.

## See also

- [[Publication]] — the repo entry note
- [[RLS Patterns]] — role shapes and filter columns across the whole suite
- [[RLS Alignment Audit]] — the cross-repo audit, including the unsecured-fact finding above
- [[RLS Role Naming Normalization]] — the initiative aligning role names across repos
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the table every role here filters
- **Derived layer** (`graphify/`, never hand-edited): [[Publication Research Output RLS Gap]], [[_COMMUNITY_Capability Role Mapping]], [[ri_pbi_publication MCN Role]], [[ri_pbi_publication NANO Role Removal and MCN Migration]], [[ri_pbi_publication NANO Not Found in Master List]], [[dim_ri_master_list_6]], [[CAPABILITY_CODE]], [[ri_pbi_publication Role Naming Mapping]], [[ri_pbi_publication RLS Role Rename Handover]]
- **Derived layer — the facts the gap exposes** (`graphify/`, never hand-edited): [[dim_ri_master_list_2]], [[fact_pure_1]], [[fact_research_output_1]], [[fact_ilab_charges_award_researcher_1]]
