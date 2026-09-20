# RI PBI Production

`ri_pbi_production` is a workspace of **7 independent git repositories**, each a standalone Power BI project in **PBIP** format for Monash's Research Infrastructure (RI) reporting suite. An eighth, [[Non-iLab Utilisation]], was added on 2026-09-18 and is not yet published; unless a statement below names it, "the 7" means the original published set.

The workspace root is *also* a small git repo, but it is **not** a parent of the 7 — it was added later solely to version root-level artifacts (`RI_App_Presentation.html`, `docs/`, `RLS_Alignment_Report.md`, `PBI_Manual_QA_Test_Plan.md` / `.xlsx`, root `CLAUDE.md`). Its `.gitignore` excludes all 7 `ri_pbi_*` directories, so Power BI content is never staged from the root, and `git status` at the root says nothing about the sub-repos.

## Repos

Each repo goes by three names — the note title, the `repo:` directory name, and the short slug used in `applies_to:`. This table is the only place the three are mapped, so use it rather than guessing a transformation between them.

| Note | `repo:` directory | `applies_to:` slug | Report subject |
|---|---|---|---|
| [[Asset]] | `ri_pbi_asset` | `asset` | Capitalised equipment/asset costs (SAP asset/GL data) |
| [[Awards]] | `ri_pbi_awards` | `awards` | Research award and funding income |
| [[Finance]] | `ri_pbi_finance` | `finance` | Budget/forecast/actuals and fund-management financials |
| [[iLab Utilisation]] | `ri_pbi_ilab_utilisation` | `ilab-utilisation` | iLab equipment/service booking and utilisation |
| [[Publication]] | `ri_pbi_publication` | `publication` | Research publications/outputs (PURE + iLab) |
| [[Risk]] | `ri_pbi_risk` | `risk` | Risk register |
| [[Survey]] | `ri_pbi_survey` | `survey` | Client-satisfaction survey results |
| [[Non-iLab Utilisation]] | `ri_pbi_non_ilab_utilisation` | `non-ilab-utilisation` | Non-iLab (Pure) service applications and awards supported, on `pure_silver` — **added 2026-09-18, not yet published** |

The slug is the note title lowercased with spaces as hyphens; the directory is `ri_pbi_` plus the title lowercased with spaces as underscores. Neither is derivable from the other without knowing that, which is why they are listed.

Each repo's knowledge — data architecture, measures, RLS, gotchas — lives in its folder under `Repos/` here, not in the repo. What stays in the repo is a thin `CLAUDE.md` working brief covering the essentials an agent needs before touching files, plus stubs where the former `README.md` and `ri_<name>_documentation.md` used to be, each pointing back to the note that replaced it.

## Initiatives

- [[RLS Alignment Audit]] — cross-repo RLS audit (`RLS_Alignment_Report.md`, dated 2026-07-13)
- [[RLS Role Naming Normalization]] — renaming RLS roles to a consistent scheme across repos
- [[Semantic Model Documentation]] — semantic model documentation design/plan
- [[RI App Presentation Deck]] — `RI_App_Presentation.html` design/plan
- [[QA Test Plan]] — manual QA test plan for the report suite
- [[Delivery Matrix]] — `RI_Delivery_Matrix.html`, per-platform delivery-milestone tracker (built 2026-08-28)

## Reference

- [[Shared Conventions]] — conventions common to all 7 repos (PBIP layout, Databricks source pattern, centralised measures, TMDL editing hazards, known gotchas)
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the shared RI capability/platform identity table, its column groups and per-repo join keys
- [[RLS Patterns]] — how row-level security is built across the suite: role shapes, per-repo filter columns, how to add a role
- [[Migration Coverage]] — which source documents have been absorbed into this vault, and their status

## Tooling

No build/lint/test tooling — projects are edited via Power BI Desktop and/or `pbi-cli`. Use the `pbi-cli` skills (power-bi-modeling, power-bi-dax, power-bi-deployment, power-bi-security, power-bi-partitions, power-bi-visuals, power-bi-docs, power-bi-diagnostics) rather than hand-editing TMDL/JSON — most require an active `pbi connect` session against the live model.

## See also

- **Derived layer — workspace** (`graphify/`, never hand-edited): [[RI PBI Production Workspace]], `CLAUDE.md Workspace Guidance` *(no node since export `0c73b0cf`)*, [[Power BI Project PBIP Format]], [[_COMMUNITY_Power BI Repository Tooling]], [[ri_pbi_asset]], [[ri_pbi_awards]], [[ri_pbi_finance]], [[ri_pbi_ilab_utilisation]], [[ri_pbi_publication]], [[ri_pbi_risk]], [[ri_pbi_survey]]
