# Risk RLS

Row-level security for [[Risk]], defined in `ri_risk.SemanticModel/definition/roles/*.tmdl`. **22 roles, 21 filters** — the smallest roster in the suite. Verified against TMDL on 2026-09-01.

> [!warning] Point-in-time snapshot
> Re-derive from `roles/*.tmdl` rather than quoting this note as current — though note this is the one roster that has not moved at all since the 2026-07-13 audit.

## The pattern

The simplest RLS in the suite. Twenty-one platform roles, each with exactly one filter:

```tmdl
role MBI
	modelPermission: read

	tablePermission dim_ri_master_list = [CAPABILITY_CODE] == "MBI"
```

One table, one column, one value, `==` throughout, and **every role's filter value is identical to its own name** — verified across all 21.

There is **no faculty or governance tier** here, unlike [[Finance]], [[Survey]] and [[iLab Utilisation]]. There are **no dual-filter roles**, unlike [[iLab Utilisation]]. There are **no multi-value roles**, unlike [[Survey]]. Nothing in this repo deviates from the single shape above except `TESTING`.

Risk and [[Publication]] share this shape exactly — same table, same column, same operator. The difference is scale: Publication carries 60 platform roles to Risk's 21.

## The 21 platform roles

`CDCO`, `CRYO`, `FLOW`, `MADP`, `MARP`, `MBI`, `MCAM`, `MCEM`, `MCN`, `MERC`, `MFGP`, `MFP`, `MGBP`, `MGMP`, `MHP`, `MMCP`, `MMI`, `MMIC`, `MMPP`, `MPMP`, `MXP`

Every one is a `CAPABILITY_CODE` value; 21 of the master list's 61 distinct codes have a role here. The roster is a deliberate subset — the platforms that actually carry risk-register entries — not an incomplete projection.

Where other repos split a unit by site, Risk keeps the umbrella code: `FLOW` here against `FLOW-ARA`/`FLOW-CLAYTON`/`FLOW-MHTP` in [[Awards]], [[Finance]], [[iLab Utilisation]] and [[Survey]]; likewise `MBI`, `MMI`, `MGBP` and `MPMP`. A user granted `FLOW-ARA` elsewhere has no matching role here, only the broader `FLOW`. That mismatch is tracked in [[RLS Role Naming Normalization]] rather than fixed inside this repo.

## The `TESTING` role — known gap

```tmdl
role TESTING
	modelPermission: read
```

That is the whole file, plus a `PBI_Id` annotation. With `modelPermission: read` and **no `tablePermission` at all**, anyone mapped to `TESTING` in the Power BI service sees every row in the model, unfiltered.

The same dev leftover exists in [[Finance]] and [[Publication]]. Recorded here as a **known security gap**, flagged in [[RLS Alignment Audit]] §2.3, and pre-approved for deletion under [[RLS Role Naming Normalization]] — repairing it is separate work and out of scope for this note.

**Do not use it as a template**, and do not read it as a "no restriction needed" pattern. The suite's deliberately unfiltered roles — `DVCRE-ADMIN` and `PVCRI-ADMIN` in [[iLab Utilisation]] — are named, governed and documented. This one is not.

## What RLS here does cover

Unlike [[Awards]] and [[Publication]], there is no unsecured-fact finding in this repo, and the arrangement is tighter than either.

`dim_ri_master_list` joins `fact_risk_register` on `CAPABILITY_CODE` — **the same column the roles filter**. In [[Awards]] the role filters `ILAB_CAPABILITY_ID` while the relationship joins `ILAB_CORE_NAME`, so the filter reaches the fact by a different path than it names. Here they coincide, and with a single fact table there is nowhere for the restriction to fail to reach.

The one table RLS does **not** cover is `Sheet1`, the standalone Excel import — it has no relationship to anything ([[Risk Data Model]]), so no role filters it. Since it is an executive "key risks" summary rather than register detail, whether that matters is a question for the report owner, not a defect on its face. Recorded.

## Rename history — none

Risk is the quietest repo in the naming campaign. Its mapping records **zero renames and zero flagged roles**: every role name already matched a live `CAPABILITY_CODE` value. The handover document records no rename either.

It is also unaffected by the 2026-08 manual passes that reshaped [[Awards]] and [[iLab Utilisation]]. The 22 roles here are the same 22 the 2026-07-13 audit saw. **When a cross-repo role question comes up, this repo is the stable reference point.**

## Adding a role

1. **Confirm the code exists as a `CAPABILITY_CODE` value** in the master list. A value that isn't there produces a **deny-all role** that reports no error — see [[RLS Patterns]].
2. **Name the file after the code, exactly.** The invariant holds across all 21; keep it.
3. **Copy the single-filter `[CAPABILITY_CODE] == "<CODE>"` form.** There is no variation in this repo to account for.
4. **Decide the granularity deliberately.** This roster uses umbrella codes where other repos use site-level ones; adding `FLOW-ARA` here would break that consistency without a reason.
5. **Renaming breaks Fabric role membership.** Every rename needs a handover entry.

## See also

- [[Risk]] — the repo entry note
- [[Risk Data Model]] — the master-list join this restriction travels through
- [[RLS Patterns]] — role shapes and filter columns across the whole suite
- [[RLS Alignment Audit]] — the cross-repo audit, including §2.3 on the `TESTING` roles
- [[RLS Role Naming Normalization]] — the campaign this repo needed no changes for
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the table every role here filters
- **Derived layer** (`graphify/`, never hand-edited): [[ri_pbi_risk Roles]], [[ri_pbi_risk MCN Role]], [[_COMMUNITY_Risk Role Mapping]], [[dim_ri_master_list_1]], `CAPABILITY_CODE` *(no node on Risk's `dim_ri_master_list`; the graph's `CAPABILITY_CODE_2` is Survey's)*, [[fact_risk_register.CAPABILITY_CODE]], [[ri_pbi_risk Role Naming Mapping]], [[ri_pbi_risk RLS Role Rename Handover]]
