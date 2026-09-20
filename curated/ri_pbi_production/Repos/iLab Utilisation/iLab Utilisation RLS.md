# iLab Utilisation RLS

Row-level security for [[iLab Utilisation]], defined in `ri_ilab_utilisation.SemanticModel/definition/roles/*.tmdl`. **58 roles carrying 106 filters** — the largest and by far the most structurally varied role set in the suite. Verified against TMDL on 2026-09-01.

> [!warning] Point-in-time snapshot — as at 2026-09-01
> Role names, filter columns and filter values in this repo have all moved within the last month. Re-derive from `roles/*.tmdl` rather than quoting this note as current.
>
> **Table name note (2026-09-15):** the model-side master-list table was renamed from `dim_facility_master_list` to `dim_ri_master_list` in the 2026-09-15 export (see [[iLab Utilisation Data Model]]). `roles/*.tmdl` isn't captured by that export, so the `tablePermission` clauses below have been updated to the new name on the inference that a role filtering a renamed table must itself reference the new name for the model to still function — not from a direct read of the role files. Confirm against live TMDL before relying on the exact syntax.

## Why this repo is different

Every other repo has exactly **one** securable table, so a role is one filter. iLab has **two** — `dim_ilab_services` and `dim_ri_master_list` — and a third, `fact_ilab`, that three roles filter directly. A platform role must therefore restrict both dimensions, and **omitting either leaves that table unsecured for that role**.

That single structural fact produces everything below. Roles fall into three tiers written differently enough that they are not interchangeable, and several roles deviate even from their own tier. **Always check which tier a role belongs to before copying it as a template.**

| Shape | Roles | Filters each |
|---|---|---|
| Two filters — `dim_ilab_services` + `dim_ri_master_list` | 47 | 2 |
| One filter — `dim_ri_master_list` only | 6 | 1 |
| `dim_ri_master_list` + a bespoke `fact_ilab` DAX filter | 3 | 2 |
| No `tablePermission` at all | 2 | 0 |

## Tier 1 — platform roles (50)

One per RI platform or facility. The canonical shape:

```tmdl
role BCIF
	modelPermission: read

	tablePermission dim_ilab_services = [facility_id] IN {"BCIF"}

	tablePermission dim_ri_master_list = [CAPABILITY_CODE] IN {"BCIF"}
```

Note the `IN {…}` operator — iLab and [[Finance]] use it throughout, where [[Awards]], [[Publication]], [[Risk]] and [[Survey]] use `==`. It handles the multi-value roles below without a chain of `||`.

**The master-list half is not always on the same column.** Twenty-nine platform roles filter `CAPABILITY_CODE`, twenty-one filter `NODE_ID`:

| Filter column | Roles |
|---|---|
| `CAPABILITY_CODE` (29) | `BCIF`, `BLTB`, `CDCO`, `CRYO`, `DDP`, `DSAIP`, `IRT`, `MADP`, `MARP`, `MBBL`, `MBI`, `MCAM`, `MCEM`, `MDMF`, `MERC`, `MFGP`, `MFI`, `MFP`, `MGMP`, `MIPSCEM`, `MIPSIF`, `MMCP`, `MMPP`, `MPMP`, `MPPU`, `MUARC`, `MXP`, `SOBS`, `SOC` |
| `NODE_ID` (21) | `BDI-INF`, `BDI-OP`, `ENG-DCE`, `ENG-DCHME`, `ENG-DECSE`, `ENG-DMAE`, `ENG-DMSE`, `ENG-FETS`, `FLOW-ARA`, `FLOW-CLAYTON`, `FLOW-MHTP`, `HELIX`, `MGBP-BI`, `MGBP-GEN`, `MHP`, `MMI-ARA`, `MMI-CLA`, `MMI-MHTP`, `MMIC`, `MMIC-HMST`, `STM-GEN` |

The split is systematic, not accidental: site- and node-level scopes need `NODE_ID`, capability-wide scopes use `CAPABILITY_CODE`. See [[RLS Patterns]] for the same scheme in [[Finance]], and [[dim_ri_master_list Reference|dim_ri_master_list]] for why the two columns disagree in the first place.

### The role name is not the filter value

This is the trap in this repo. Several roles filter values that differ from their own name, and the two halves of a role can disagree with each other:

| Role | `dim_ilab_services[facility_id]` | `dim_ri_master_list` |
|---|---|---|
| `MMIC-HMST` | `"HMST"` | `NODE_ID` = `"MMIC-HMST"` |
| `ENG-DCE` | `"FENG-DCE"` | `NODE_ID` = `"ENG-DCE"` |
| `ENG-DCHME` | `"FENG-DCHME"` | `NODE_ID` = `"ENG-DCHME"` |
| `ENG-DECSE` | `"FENG-DECSE"` | `NODE_ID` = `"ENG-DECSE"` |
| `ENG-FETS` | `"FENG-FETS"` | `NODE_ID` = `"ENG-FETS"` |
| `HELIX` | `"MERC-HELIX"` | `NODE_ID` = `"MERC-HELIX"` |
| `MMIC` | `"MMIC"` | `NODE_ID` = `{"MMIC-HMST","MMIC-PARK-CLA"}` |

The `FENG-*` values on the services side are not stale leftovers — `dim_ilab_services[facility_id]` carries iLab's own facility coding, which was never renamed. Only the master-list side follows RI's `ENG-*` naming. **Do not "align" the two halves of a role; they legitimately differ.**

**Multi-value roles.** `MHP` filters `{"MHP-ARA","MHP-CLA","MHP-MHTP"}` on both tables. `MMIC` filters two `NODE_ID` values against a single `facility_id`. `ENG-DMAE` spans two nodes. Everywhere else, one role means one value.

## Tier 2 — faculty/governance roles (6)

`BUSECO-ADMIN`, `CENTRAL-ADMIN`, `ENG-ADMIN`, `MIPS-ADMIN`, `MNHS-ADMIN`, `SCI-ADMIN`. These scope a whole faculty rather than one platform, through a single filter on a different column:

```tmdl
tablePermission dim_ri_master_list = [CAPABILITY_GOVERNANCE] IN {"MNHS"}
```

They rely on the many-to-many relationship to propagate down to `fact_ilab`, and **deliberately do not add the `dim_ilab_services` filter** — the faculty grant is meant to be broader than any single `facility_id`. Do not "complete" them by adding a second filter.

### MARP custodianship carve-outs

`CENTRAL-ADMIN` and `MNHS-ADMIN` each carry an **additional** bespoke `fact_ilab` filter implementing a custodianship handover of the Monash Animal Research Platform at 2026-01-01 — MNHS holds MARP data through 2025, CENTRAL takes it from 2026 onward:

```tmdl
	tablePermission fact_ilab =
			SWITCH(
			    TRUE(),
			    [core_name] == "MONASH ANIMAL RESEARCH PLATFORM" && [completion_date] < DATE(2026,1,1), FALSE(),
			    TRUE()
			)
```

That is `CENTRAL-ADMIN`'s. `MNHS-ADMIN`'s is the mirror image, `> DATE(2025,12,31)`. **The two are complements**: edit one and the other must still cover the gap, or MARP rows end up either double-covered or orphaned.

As of 2026-09-01 the cutoff is in the past, so the split no longer changes anything going forward — but the logic remains live and still hides historical rows from each role. Worth revisiting with the model owner; recorded, not changed.

## Tier 3 — unrestricted org roles (2)

`DVCRE-ADMIN` and `PVCRI-ADMIN` declare `modelPermission: read` and **no `tablePermission` at all**. They see the entire model, by design — top-level DVC Research Enterprise and PVC Research Infrastructure executive visibility.

**This is deliberate and named. Do not "fix" them by adding filters.** It is also the one place in the suite where an unfiltered role is legitimate: the `TESTING` roles in [[Finance]], [[Publication]] and [[Risk]] look identical in TMDL but are dev leftovers and a known security gap. The difference is governance, not syntax — see [[RLS Patterns]].

## Deviations — recorded, not fixed

Three roles do not follow their tier. Listed so they are not mistaken for the convention:

| Role | Deviation | Assessment |
|---|---|---|
| `ENG-DMSE` | Only `dim_ri_master_list[NODE_ID] IN {"ENG-DMSE"}`. The `dim_ilab_services` half is **still missing**, so that dimension is unfiltered for this role. | Potential over-exposure |
| `MGBP-BI` | Only `dim_ri_master_list[NODE_ID] IN {"MGBP-BI"}` — single filter, and on `NODE_ID` where its siblings use `CAPABILITY_CODE`. | Potential over-exposure |
| `ENG-DMAE` | Replaces the `dim_ilab_services` filter with a bespoke `fact_ilab` DAX filter — `([core_name] == "FACULTY OF ENGINEERING TECHNICAL SERVICES" && [category] == "MAE") \|\| [core_name] == "DEPARTMENT OF MECHANICAL AND AEROSPACE ENGINEERING"` — plus `NODE_ID IN {"ENG-DMAE","ENG-FETS"}`. Needed because DMAE's visibility splits by `category`, not by a single `facility_id`. | Looks intentional |

All three are open items, not settled patterns. Flag rather than replicate.

> [!warning] `ENG-DMSE`'s second filter was not restored
> [[RLS Role Naming Normalization]] records the 2026-08-10 pass as having fixed "the missing-second-filter defect" on this role. It did not. What that commit corrected was the filter **column and value** (`[CAPABILITY_CODE] IN {"FENG-DMSE"}` → `[NODE_ID] IN {"ENG-DMSE"}`). The `dim_ilab_services` filter is still absent as of 2026-09-01.

## `DDP` — unresolved

> [!warning] Open question — `DDP` may be a deny-all role (as at 2026-09-01)
> `DDP` filters `dim_ri_master_list[CAPABILITY_CODE] IN {"DDP"}`, and **no such capability code appears** in the master-list extract at `docs/rls-role-naming/data/master-list-values.csv`. The nearest value is `MDDP`.
>
> If the code genuinely does not exist in the live data, anyone mapped to this role **sees nothing at all**, and the model reports no error — the silent failure mode described in [[RLS Patterns]].
>
> **This cannot be settled from the files.** It needs a role-impersonated `EVALUATE` against the live model, which is exactly the check [[RLS Alignment Audit]] listed as out of scope for a static audit. Until someone runs it, treat `DDP` as unverified rather than working.
>
> It is the **one flagged role in this repo that no subsequent pass resolved** — the role-naming mapping flagged it `flagged-not-found-in-master-list` on 2026-08-06 and it has been untouched by every commit since. Recorded, not fixed.

## Rename history

The role-naming mapping parsed 58 roles here and flagged 7, plus one multi-value ambiguity. Two separate passes followed:

- **The pipeline rename** (commit `a85f747`): `HMST` → `MMIC-HMST`, so the file name matches its `NODE_ID` filter value. Its `dim_ilab_services[facility_id]` value stayed `"HMST"`, and correctly so. A follow-up commit (`10070ce`) fixed a **dangling `model.tmdl` reference** left by that rename — see [[iLab Utilisation Gotchas]].
- **A manual pass** (commit `beb91c3`, 2026-08-10): `DCE`/`DCHME`/`DECSE`/`DMAE`/`FETS` renamed to `ENG-*`; `DMSE.tmdl` deleted and replaced by `ENG-DMSE.tmdl` with its filter column and value corrected; `HELIX` kept its name but had **both** filter values corrected to `MERC-HELIX`.

That second pass **went beyond the initiative's naming-only constraint**, changing filter columns and values as well as names. It was a deliberate manual decision rather than pipeline output, and it fixed real access defects — but it means role *behaviour* changed in commits that read as renames. [[RLS Role Naming Normalization]] records the full detail.

`RLS_Alignment_Report.md` has **not** been updated for that manual pass; it still shows pre-2026-08-06 names for everything except the one footnoted `HMST` case. Prefer [[RLS Patterns]] and this note over the report's Appendix A for current naming.

## Adding a role

1. **Decide the tier first.** Platform, faculty/governance, or unrestricted — they are written differently.
2. **For a platform role, write both filters.** One securable table is not enough here; that is the defect `ENG-DMSE` and `MGBP-BI` currently exhibit.
3. **Pick the master-list column by granularity** — `NODE_ID` for a site/node scope, `CAPABILITY_CODE` for a capability-wide one.
4. **Expect the two halves to differ.** `dim_ilab_services[facility_id]` uses iLab's coding; the master list uses RI's.
5. **Confirm both literal values exist** in their respective tables, or you have built a deny-all role that reports nothing.
6. **Update `model.tmdl`.** A new role needs a `ref role` line; a renamed one needs its existing line changed. See [[iLab Utilisation Gotchas]].
7. **Renaming breaks Fabric role membership.** Every rename needs a handover entry.

## See also

- [[iLab Utilisation]] — the repo entry note
- [[RLS Patterns]] — role shapes and filter columns across the whole suite
- [[RLS Alignment Audit]] — the cross-repo audit, including this repo's single-filter findings
- [[RLS Role Naming Normalization]] — the rename campaign and its manual follow-ups
- [[dim_ri_master_list Reference|dim_ri_master_list]] — why `CAPABILITY_CODE` and `NODE_ID` disagree
- **Derived layer — roles and decisions** (`graphify/`, never hand-edited): [[_COMMUNITY_RLS Filter Configuration]], [[_COMMUNITY_Research Infrastructure Data]], [[ri_pbi_ilab_utilisation Role Catalog (58 roles)]], [[HMST to MMIC-HMST Rename]], [[ri_pbi_ilab_utilisation DVCRE-ADMIN Role]], [[ri_pbi_ilab_utilisation PVCRI-ADMIN Role]], [[_COMMUNITY_DVCRE Admin Role]], [[_COMMUNITY_PVCRI Admin Access]], [[ri_pbi_ilab_utilisation DDP Decision]], [[ri_pbi_ilab_utilisation HELIX Decision]], [[ri_pbi_ilab_utilisation DMAE Multi-Value Decision]], [[Utilisation DDP Not Found in Master List]], [[DDP Role]], [[HELIX Role]], [[Potential Silent Deny-All RLS Defect]]
- **Derived layer — filtered tables and generated docs** (`graphify/`, never hand-edited): [[Additional RLS Filters]], [[No Additional RLS Filters]], [[dim_facility_master_list]], [[dim_ilab_services]], [[ri_pbi_ilab_utilisation Role Naming Mapping]], [[ri_pbi_ilab_utilisation RLS Rename Handover]]
