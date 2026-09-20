# Semantic Model Documentation

Initiative to produce one semantic-model documentation Markdown file per repo in [[Overview|RI PBI Production]], describing each PBIP model's tables, relationships, Power Query sources, data dictionary, measures, and RLS/appendix notes in a single human-readable reference.

## Purpose

`ri_pbi_asset/ri_asset_documentation.md` already existed as a hand-written reference doc for the asset model. The goal of this initiative was to extend that same documentation to the **other 6 repos** ([[Awards]], [[Finance]], [[iLab Utilisation]], [[Publication]], [[Risk]], [[Survey]]), matching its structure, depth, and style exactly, so every repo in the suite has an equivalent onboarding/reference document — not just tribal knowledge in each `CLAUDE.md`.

Source docs: `docs/superpowers/specs/2026-07-30-ri-pbi-semantic-model-documentation-design.md` (design, approved) and `docs/superpowers/plans/2026-07-30-ri-pbi-semantic-model-documentation.md` (implementation plan).

## Design decisions

- **One output file per repo**, named `<repo>_documentation.md` (basename follows each repo's `SemanticModel` folder basename, not always the repo folder name — e.g. `ri_pbi_finance` → `ri_finance_documentation.md`).
- **Six fixed sections**, numbered `## 1.` – `## 6.`, mirrored from the asset reference doc:
  1. Overview — plain-English summary + a table of table/relationship/measure/date-table counts
  2. Relationship Diagram — Mermaid `flowchart LR` (never `graph LR`), one node per table, edges labelled with join columns, solid for active / dotted for inactive relationships
  3. Data Sources (Power Query/M) — connection & helper functions, parameters, core data flow in dependency order, static/reference snapshots, legacy/decommissioned queries, and a **local file gotcha** callout for any hardcoded `File.Contents(...)` path
  4. Data Dictionary — one sub-section per table (fact first, then dimensions alphabetically, then date table, then measure-folder tables), column-level `Column | Data type | Hidden | Description` tables
  5. Measures — one sub-section per measure in TMDL order, full unmodified `dax` code block, plain-English explanation of business meaning/filter context/caveats
  6. Appendix/Notes — hidden tables/columns and why, RLS summary (role count, filtered table/column, `==` vs `IN`, how it differs from the rest of the suite), known cleanup items, repo-specific conventions
- **Style rules carried from the reference doc**: backtick every identifier; **bold** the Hidden-column value only when a column is *not* hidden (i.e. write **No**, not No); never truncate DAX; where a column's purpose can't be determined, write "Purpose unclear — review with model owner" instead of inventing an explanation.
- **No source changes** — documentation only. No TMDL/DAX/PBIR edits, and per standing instruction, no `git add`/`git commit` performed by the generating subagents.

## Plan / approach

Implemented as **six independent, parallel `general-purpose` subagent dispatches** (one per repo), each fully self-contained since subagents share no memory of the orchestrating conversation:

1. Each subagent first reads `ri_pbi_asset/ri_asset_documentation.md` in full to calibrate style before writing anything.
2. Each then reads its own repo's `CLAUDE.md`, `expressions.tmdl`, `relationships.tmdl`, every `tables/*.tmdl`, `model.tmdl`, and every `roles/*.tmdl` — plus skims the workspace-root `CLAUDE.md` for cross-repo conventions to reference in §6.
3. Each writes its single output file, then reports back gaps/ambiguities/"Purpose unclear" items for consolidation.

Repo-specific reminders were baked into individual dispatch prompts, since the shared body couldn't capture every repo's quirks:
- **[[iLab Utilisation RLS|iLab Utilisation]]**: each RLS role applies **two** `tablePermission` filters (`dim_ilab_services[facility_id]` and `dim_facility_master_list[CAPABILITY_CODE]`) — §6 needed to cover both, and table names use spaced/capitalized conventions (`Key Measures.tmdl`, `Time Intelligence.tmdl`) rather than snake_case.
- **[[Publication Gotchas|Publication]]**: the `journal_list` table's M partition uses a stale hardcoded path (`File.Contents("C:\Users\maba0001\projects\ri_pbi_publication\ref\journal_list.csv")`) that needed calling out verbatim in §3; `dim_ri_master_list` is joined via two different keys depending on source fact (`ILAB_CORE_NAME` vs `PURE_FACILITY_ID`).
- **[[Risk Data Model|Risk]]**: `Key Risks.xlsx` is loaded via a similarly stale absolute path; `fact_risk_register.tmdl` carries `///` doc comments to use as the primary source for column descriptions; `dim_risk_rating`/`dim_impact`/`dim_likelihood` each have an active (post-mitigation) and an inactive `USERELATIONSHIP`-activated (pre-mitigation) link that both needed to appear in the diagram.
- **[[Survey Data Model|Survey]]**: the only repo that doesn't use `dim_ri_master_list`/`dim_facility_master_list` — platform identity comes from `DIM_FACILITY`, joined **bidirectionally** to `FACT_SURVEY` via `SURVEY_CAPABILITY_ID`; roughly 8-9 small per-question rating dimensions (e.g. `DIM_E_TRAINING`) needed to be included in the diagram rather than abstracted away.

Verification per repo was grep-based (no line-by-line TMDL re-check, to avoid defeating the point of parallelizing): confirm the file exists, exactly 6 `## N.` headers, at least one `flowchart LR` and zero `graph LR`, `dax` fence count roughly matching measure count, zero `TBD`/`TODO`, and (per-repo) presence of the specific gotcha strings above. A final consolidation task collects all six subagents' reported gaps into one summary for the user, without re-committing anything.

## Status / outcome

All six documentation files exist in their respective repos, matching the planned filenames:

| Repo | Output file |
|---|---|
| [[Awards]] | `ri_pbi_awards/ri_pbi_awards_documentation.md` |
| [[Finance]] | `ri_pbi_finance/ri_finance_documentation.md` |
| [[iLab Utilisation]] | `ri_pbi_ilab_utilisation/ri_ilab_utilisation_documentation.md` |
| [[Publication]] | `ri_pbi_publication/ri_publication_documentation.md` |
| [[Risk]] | `ri_pbi_risk/ri_risk_documentation.md` |
| [[Survey]] | `ri_pbi_survey/ri_survey_documentation.md` |

Each has since been committed within its own sub-repo (commit messages like "Update documentation" / "Create markdown documentation"), so — despite the plan's explicit "leave uncommitted, no git operations" constraint for the generation step itself — the docs are now checked in as part of normal repo history, presumably via a later, separate, explicit commit request. `ri_pbi_asset/ri_asset_documentation.md` remains the original style reference and was untouched by this initiative.

**Superseded on 2026-09-01.** The six generated files, and the asset reference doc they were modelled on, were re-derived into this vault under `Repos/<Name>/` — one `Data Model`, `Measures`, `RLS` and `Gotchas` note per repo as that repo needed — and each file in the repo was reduced to a pointer stub back to those notes. [[Migration Coverage]] records all seven as `stubbed`. The spec and plan were annotated to say so on 2026-09-11, and also to note that their "workspace root isn't a git repo" remark was true only at the time. The initiative's outcome therefore lives on as the `Repos/` notes, not as the files it produced.

## See also

- [[Shared Conventions]] — the cross-repo patterns (`dim_ri_master_list` vs repo-specific master tables, RLS shape variance, Databricks source pattern, hardcoded local file paths) that each generated doc's §6 was asked to cross-reference
- [[Overview|RI PBI Production]] — workspace-level index of all 7 repos and other initiatives
- [[Awards]], [[Finance]], [[iLab Utilisation]], [[Publication]], [[Risk]], [[Survey]] — the 6 repos documented by this initiative
- [[RLS Patterns]] — the suite-wide RLS shapes each generated doc’s §6 summarises per repo
- [[RLS Alignment Audit]] — separate audit of RLS specifically, referenced by each doc's §6 RLS summary
- **Derived layer** (`graphify/`, never hand-edited): [[RI PBI Semantic Model Documentation Design]], [[RI PBI Semantic Model Documentation Plan]], [[Document Six Remaining RI PBI Semantic Models]], [[Six-Section Semantic Model Documentation Contract]], [[Grep-Based Documentation Verification]], [[Parallel Six-Subagent Documentation Execution]], [[Task 7 Consolidate Gap Summary]], [[_COMMUNITY_Semantic Documentation Design]], [[_COMMUNITY_Documentation Commit Design]]
