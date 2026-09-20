# RLS Patterns

How row-level security is actually built across [[Overview|RI PBI Production]]. Six of the seven repos define roles under `<model>.SemanticModel/definition/roles/*.tmdl` — **280 role files carrying 325 `tablePermission` filters** between them. [[Asset]] has no `roles/` directory at all.

This note describes the *patterns*: what shapes exist, why they differ, and how to add a role without breaking one. For the findings of the 2026-07-13 cross-repo audit — which facts are actually reachable, which roles are over-exposed — see [[RLS Alignment Audit]].

> [!warning] Point-in-time snapshot
> Every count and filter column below was derived from TMDL on **2026-09-01**. Role renames land between audits — awards alone gained two roles and renamed seven since 2026-07-13 — so re-derive counts from `roles/*.tmdl` rather than quoting this note as current.

## The mechanism, in one paragraph

A role grants `modelPermission: read` (all 280 do — no repo uses `readRefresh` or higher) and then declares one or more `tablePermission` filters. Each filter is a DAX expression evaluated against a dimension table; rows failing it disappear, and the restriction propagates along relationships to the fact tables on the many side. In practice that dimension is [[dim_ri_master_list Reference|dim_ri_master_list]] — carried under that model-side name in six of the seven RLS-enabled repos as of 2026-09-15 — or, in [[Survey]] alone, its derived variant `DIM_FACILITY`. **This is why RLS in this suite is really a question about the master list**: the filter reaches exactly as far as that table's relationships do, and no further.

## Per-repo shape

| Repo | Roles | Filtered table(s) | Filter column(s) | Filters |
|---|---|---|---|---|
| [[Publication]] | 61 | `dim_ri_master_list` | `CAPABILITY_CODE` (60) | 60 |
| [[iLab Utilisation]] | 58 | `dim_ri_master_list` (renamed from `dim_facility_master_list` 2026-09-15), `dim_ilab_services`, `fact_ilab` | `CAPABILITY_CODE` (29), `NODE_ID` (21), `CAPABILITY_GOVERNANCE` (6), `facility_id` (47), DAX on `fact_ilab` (3) | 106 |
| [[Survey]] | 55 | `DIM_FACILITY` | `SURVEY_CAPABILITY_ID` (52), `CAPABILITY_GOVERNANCE` (3) | 55 |
| [[Awards]] | 48 | `dim_ri_master_list` | `ILAB_CAPABILITY_ID` (46), `NODE_ID` (2) | 48 |
| [[Finance]] | 36 | `dim_ri_master_list` | `CAPABILITY_CODE` (16), `NODE_ID` (15), `CAPABILITY_GOVERNANCE` (4) | 35 |
| [[Risk]] | 22 | `dim_ri_master_list` | `CAPABILITY_CODE` (21) | 21 |
| [[Asset]] | 0 | — | — | 0 |

Where the filter count is below the role count, the difference is roles with **no `tablePermission` at all** — see below.

## Why the filter column differs

Not arbitrary drift. [[dim_ri_master_list Reference|dim_ri_master_list]] is an identifier crosswalk: each source system names the same organisational unit differently, in its own column. A role must filter the column belonging to the system that produced that repo's fact rows, so **each repo's role roster is effectively a projection of one master-list column**:

| Repo | Projects | Roster size vs. distinct values in the master list |
|---|---|---|
| [[Publication]] | `CAPABILITY_CODE` | 60 roles / 61 distinct codes — only `DDD` has no role |
| [[Awards]] | `ILAB_CAPABILITY_ID` | 46 roles / 46 distinct values — a clean one-to-one |
| [[Risk]] | `CAPABILITY_CODE` | 21 roles / 61 — a deliberate subset (platforms carrying risk entries) |
| [[Survey]] | `SURVEY_CAPABILITY_ID` | 52 roles, on the derived `DIM_FACILITY` |

That correspondence explains the counts that otherwise look arbitrary: publication has the most roles because `CAPABILITY_CODE` is the widest roster and publication attributes outputs at faculty level too; awards has 46 because only 46 units exist in iLab.

It also explains the naming friction the audit records. The same unit is `ENG-DCE` under `NODE_ID` and `FENG-DCE` under `ILAB_CAPABILITY_ID`; `FLOW` under `CAPABILITY_CODE` but `FLOW-ARA` under `NODE_ID`. Roles named after different columns cannot be reconciled by renaming alone.

### The two-column granularity scheme

[[Finance]] and [[iLab Utilisation]] both mix columns *within* one repo, systematically rather than accidentally:

- capability-wide roles filter `CAPABILITY_CODE`
- site/node roles (`FLOW-ARA`, `MPMP-CLA`, `MERC-HELIX`, `MMIC-HMST`) filter `NODE_ID`
- `*-ADMIN` roles filter `CAPABILITY_GOVERNANCE`

[[Awards]] joined them partway: its two newest roles (`MMIC-HMST`, `MMIC-PARK-CLA`) filter `NODE_ID` while the other 46 filter `ILAB_CAPABILITY_ID`, so "awards is single-column" is no longer true.

## Shapes a role can take

**One filter, one column, one value** — the common case, covering all of awards, finance, publication and risk, and survey's 52 platform roles:

```tmdl
role MBI
	modelPermission: read

	tablePermission dim_ri_master_list = [CAPABILITY_CODE] == "MBI"
```

**Two filters, two tables** — [[iLab Utilisation]] only, and its dominant pattern (47 of 58 roles). iLab has a second securable table, so a platform role must restrict both; omitting either leaves that table unsecured for the role:

```tmdl
role BCIF
	modelPermission: read

	tablePermission dim_ilab_services = [facility_id] IN {"BCIF"}

	tablePermission dim_ri_master_list = [CAPABILITY_CODE] IN {"BCIF"}
```

**Faculty/governance scope** — a single filter on `CAPABILITY_GOVERNANCE` instead of a platform code, granting a whole faculty. Thirteen roles: [[iLab Utilisation]] 6, [[Finance]] 4, [[Survey]] 3. iLab's deliberately omit the `dim_ilab_services` half, because the faculty grant is meant to be broader than any single `facility_id`.

**Multi-value roles** — one role covering several codes, where the role name is a parent of the filtered values. Survey's `MARP` enumerates 11 `MARP-*` facility IDs, `MERC` enumerates 4, `MHP` enumerates 3; iLab's `MHP`, `MMIC` and `ENG-DMAE` each cover 2–3. Everywhere else, one role means one value.

**DAX beyond an equality** — three iLab roles filter `fact_ilab` directly with a `SWITCH` or boolean expression rather than filtering a dimension. These implement time-boxed custodianship rather than a scope grant, and are documented in that repo.

**No filter at all** — five roles, in two very different categories:

| Role | Repo | Status |
|---|---|---|
| `DVCRE-ADMIN` | [[iLab Utilisation]] | Deliberate, named executive all-access grant |
| `PVCRI-ADMIN` | [[iLab Utilisation]] | Deliberate, named executive all-access grant |
| `TESTING` | [[Finance]] | Unfiltered dev leftover |
| `TESTING` | [[Publication]] | Unfiltered dev leftover |
| `TESTING` | [[Risk]] | Unfiltered dev leftover |

A role with `modelPermission: read` and no `tablePermission` sees the entire model. For the two iLab roles that is the intent — don't "fix" them by adding filters. The three `TESTING` roles are **a known security gap**: anyone mapped to one in the Power BI service has unrestricted access to that model. They are recorded here so the exposure is not forgotten; repairing them is separate work, tracked under [[RLS Role Naming Normalization]], which holds pre-approved sign-off to delete all three.

## The silent failure mode

A filter whose literal value does not exist in the data produces an **empty role** — the member sees nothing, and nothing in the model reports an error. Roles are therefore invisible to static checking in the one way that matters most, and the [[RLS Alignment Audit]] lists this as its first unverified limitation.

Two clusters currently look exposed to it, comparing role filter values against the master-list extract in `docs/rls-role-naming/data/master-list-values.csv`:

- **[[Awards]] — seven roles.** The 2026-08 renames changed both the role names *and* their filter values from `FENG-*` to `ENG-*` (six roles) and `NANO` to `MCN`. But those roles filter `ILAB_CAPABILITY_ID`, and in the extract that column still holds `FENG-DCE`, `FENG-DCHME`, `FENG-DECSE`, `FENG-DMAE`, `FENG-DMSE`, `FENG-FETS`. The `ENG-*` spellings live in `NODE_ID`, a different column. If the source table has not been updated to match, all seven are deny-all.
- **[[iLab Utilisation]] — one role.** `DDP` filters `CAPABILITY_CODE IN {"DDP"}`, and no such capability code appears in the extract; the nearest is `MDDP`.

Neither can be confirmed from files alone — the extract is itself a point-in-time capture from the role-naming campaign, and the live table may since have moved. Both need a role-impersonated query against the live model. Recorded, not fixed.

## Expression style

Cosmetic, but inconsistent enough to notice when reading across repos: awards, publication, risk and survey write `[col] == "X"`, chaining `||` for multi-value roles (survey's `MARP` chains eleven). Finance and iLab write `[col] IN {"X"}`, which handles multi-value roles without the chain. Nothing depends on the choice.

## Adding a role

1. **Read the repo's existing role files first.** The generic description above is a summary of six different conventions; match the one actually in use.
2. **Pick the filter column by granularity and source system**, not by what another repo does — capability-wide vs. node-level vs. faculty, on the column belonging to the system feeding that repo's facts.
3. **Confirm the literal value exists** in the master list for that column, or you have created a deny-all role.
4. **In [[iLab Utilisation]], write both filters.** One securable table is not enough there.
5. **Renaming is not free.** Role names bind AD groups to access in the Fabric service; a rename breaks those bindings until membership is remapped. Every rename in this suite carries a handover entry for that reason — see [[RLS Role Naming Normalization]].

## See also

- [[dim_ri_master_list Reference|dim_ri_master_list]] — the table nearly every role filters, and why its columns differ
- [[RLS Alignment Audit]] — findings, severities and propagation gaps from the 2026-07-13 audit
- [[RLS Role Naming Normalization]] — the initiative aligning role names across repos
- [[Shared Conventions]] — conventions common to all 7 repos
- [[Overview|RI PBI Production]]
- **Derived layer** (`graphify/`, never hand-edited): [[Three-Tier RLS Model]], [[Identity-Based RLS Filter]], [[Cross-Repository RLS Key Divergence]], [[Survey RLS Uses DIM_FACILITY]], [[Asset Model Has No RLS]], [[_COMMUNITY_Finance RLS Roles]], [[Additional RLS Filters]], [[_COMMUNITY_Capability Access Roles]], [[_COMMUNITY_RLS Filter Configuration]], [[RLS_FACILITY_GROUP_2]], [[RLS_FACULTY_GROUP_2]]
