# Survey RLS

Row-level security for [[Survey]], defined in `ri_survey.SemanticModel/definition/roles/*.tmdl`. **55 roles, 55 filters** — one per role, all on `DIM_FACILITY`. Verified against TMDL on 2026-09-01.

> [!warning] Point-in-time snapshot — as at 2026-09-01
> Re-derive from `roles/*.tmdl` rather than quoting this note as current. Note that unlike every other repo, nothing here changed during the 2026-08 renaming work — see below.

## Two groups, two columns

| Group | Count | Filter |
|---|---|---|
| Platform/facility | 52 | `tablePermission DIM_FACILITY = [SURVEY_CAPABILITY_ID] == "<CODE>"` |
| Faculty/governance | 3 | `tablePermission DIM_FACILITY = [CAPABILITY_GOVERNANCE] IN {"<FACULTY>"}` |

The three governance roles are `CENTRAL-ADMIN`, `MIPS-ADMIN` and `MNHS-ADMIN`. **They are not platform roles with an admin-sounding name** — they scope a whole faculty through a different column, and mixing the two conventions silently grants the wrong rows. Match the group when adding a role.

**Every one of the 55 carries a real filter.** There is no `TESTING` role here, and no deliberately unrestricted role either — unlike [[Finance]], [[Publication]] and [[Risk]] (unfiltered dev leftovers) and [[iLab Utilisation]] (two governed all-access roles). Survey is the only repo where the roster is uniformly filtered.

## Filtering `DIM_FACILITY` is structural, not a preference

Every other repo filters `dim_ri_master_list` — as of 2026-09-15, iLab Utilisation's copy carries that same model-side name too. Survey filters `DIM_FACILITY`, which [[RLS Alignment Audit]] §3.2 records as a **medium-severity divergence** from the stated convention.

It is not, however, something that could be fixed by editing role files alone. `DIM_FACILITY` is derived from the same `ri_master_list` source, and until 2026-09-15 was reduced to six columns with **no `CAPABILITY_CODE` and no `NODE_ID`**. As of the 2026-09-15 export, `DIM_FACILITY` widened to 25 columns and **does now carry `CAPABILITY_CODE` and `NODE_ID`** — see [[Survey Data Model]] and the resolved-discrepancy note in [[Survey]]. Whether any role file has been updated to use them is unconfirmed; the roles table above (55 filters, all on `SURVEY_CAPABILITY_ID`/`CAPABILITY_GOVERNANCE`) still reflects the 2026-09-01 TMDL read and needs re-checking against live `roles/*.tmdl` before this section's "structural, not a preference" framing can be trusted as still current.

Two consequences follow.

**Survey role codes do not line up with other repos'.** They are `SURVEY_CAPABILITY_ID` values, which is a different identifier family from `CAPABILITY_CODE`, `NODE_ID` or `ILAB_CAPABILITY_ID` — see [[dim_ri_master_list Reference|dim_ri_master_list]] for why those disagree. `MERC-HELIX` is folded inside Survey's `MERC` role, is a **separate role** in [[Finance]], and is named `HELIX` in [[iLab Utilisation]]. Workspace-level role membership cannot be managed uniformly across the suite.

**This repo was excluded from [[RLS Role Naming Normalization]] outright** — and it is the only one of the six RLS-enabled repos with no role-mapping or handover document. There was nothing to normalise names *against*: the initiative aligned roles to master-list `CAPABILITY_CODE`/`NODE_ID` values, and this model exposes neither. The initiative is explicit that Survey stays on `SURVEY_CAPABILITY_ID` and does not get a schema change to enable normalisation.

## Survey is now the only repo still using `FENG-*`

A direct consequence of that exclusion. Six roles here are named `FENG-DCE`, `FENG-DCHME`, `FENG-DECSE`, `FENG-DMAE`, `FENG-DMSE` and `FENG-FETS`.

[[Awards]] and [[iLab Utilisation]] both renamed their equivalents to `ENG-*` during the 2026-08 manual passes. Survey did not, because it was out of scope. **What [[RLS Alignment Audit]] recorded as a three-way naming split is now a two-way one**, with Survey alone on the old naming — which is a smaller problem than the audit described, but a more confusing one, because the old names now look like an oversight rather than one of several conventions.

## Multi-value roles

Three roles cover several capability IDs each, chaining `==` comparisons with `||` rather than using `IN {…}`:

| Role | Covers |
|---|---|
| `MARP` | 11 IDs — `MARP-ARL`, `MARP-CLA`, `MARP-EAF`, `MARP-GFS`, `MARP-LAF-13`, `MARP-LAF-41`, `MARP-MMC`, `MARP-PPS`, `MARP-RBF`, `MARP-RU`, `MARP-VU` |
| `MERC` | 4 IDs — `MERC-CLOUD`, `MERC-HPC`, `MERC-RDS`, `MERC-HELIX` |
| `MHP` | 3 IDs — `MHP-ARA`, `MHP-CLA`, `MHP-MHTP` |

The other 49 platform roles each filter exactly one value, and **every one of those filter values is identical to its own role name** — verified across all 49.

The operator style is worth noting: Survey (like [[Awards]], [[Publication]] and [[Risk]]) writes `[col] == "X"`, so `MARP` is an eleven-term `||` chain. [[Finance]] and [[iLab Utilisation]] use `IN {…}`, which handles this case in one expression. Cosmetic, but `MARP` is the clearest argument for the other style in the whole suite.

## What RLS here does cover

Unlike [[Awards]] and [[Publication]], there is no unsecured-fact finding in this repo. `DIM_FACILITY` relates to `FACT_SURVEY`, and `FACT_COMMENTS` hangs off `FACT_SURVEY` — so both facts are reachable.

**One caveat.** That relationship is the model's only **bidirectional many-to-many** ([[Survey Data Model]]). A static reading says restriction propagates correctly, but [[RLS Alignment Audit]] singles it out as the one relationship in the suite genuinely worth confirming with a role-impersonated `EVALUATE`, because bidirectional many-to-many filtering is harder to reason about on paper than the one-directional links everywhere else. Unverified, recorded.

## Adding a role

1. **Pick the group first** — platform (`SURVEY_CAPABILITY_ID`) or faculty (`CAPABILITY_GOVERNANCE`). They filter different columns and grant different things.
2. **Confirm the code is a `SURVEY_CAPABILITY_ID` value.** As at the 2026-09-01 TMDL read, no role filtered `CAPABILITY_CODE` or `NODE_ID` here — `DIM_FACILITY` now carries both columns as of the 2026-09-15 export (see above), but until the role files are re-checked, treat `SURVEY_CAPABILITY_ID` as the identifier to use. A value that does not exist produces a **deny-all role** that reports no error ([[RLS Patterns]]).
3. **Remember the roster was a subset, as at 2026-09-01.** `DIM_FACILITY` held only rows with a non-null `SURVEY_CAPABILITY_ID`, so capabilities the survey does not cover could not have a role here at all. Whether that filter survived the 2026-09-15 widening of `DIM_FACILITY` is unconfirmed — see [[Survey Data Model]].
4. **Name the file after the filter value** for single-value roles; the invariant holds across all 49.
5. **Renaming breaks Fabric role membership.** Every rename needs a handover entry — and note this repo has no handover document yet, so one would need creating.

## See also

- [[Survey]] — the repo entry note
- [[Survey Data Model]] — `DIM_FACILITY`'s derivation and the bidirectional relationship
- [[RLS Patterns]] — role shapes and filter columns across the whole suite
- [[RLS Alignment Audit]] — §3.2's finding on this repo's divergence
- [[RLS Role Naming Normalization]] — the initiative this repo was excluded from
- [[dim_ri_master_list Reference|dim_ri_master_list]] — why `SURVEY_CAPABILITY_ID` doesn't line up with other repos' codes
- **Derived layer** (`graphify/`, never hand-edited): [[Survey RLS Uses DIM_FACILITY]], [[_COMMUNITY_Survey Capability Roles]], [[DIM_FACILITY]], [[FACT_SURVEY]], [[CENTRAL-ADMIN_1]], [[FLOW-ARA_1]], [[FENG-DCE]], [[FENG-DCHME]], [[FENG-DECSE]], [[FENG-DMAE]], [[FENG-DMSE]], [[FENG-FETS]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[DIM_FACILITY_2]], [[FACT_COMMENTS_1]]
