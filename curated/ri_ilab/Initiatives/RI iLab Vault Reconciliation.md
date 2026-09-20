# RI iLab Vault Reconciliation

The 2026-09-02 plan to bring the `Projects/RI iLab` notes — then 12 notes built by `/graphify` against the codebase, every one carrying `source_docs: []` — into line with what the `ri_ilab` repo's code and `docs/` actually said, verified by a small repo-side lint toolkit rather than by eye. Nine of its fourteen tasks ran and were committed; the remaining five were never executed, and on **2026-09-11** the plan was marked **superseded** in the repo. Any further reconciliation of these notes needs a fresh plan baselined against the current vault, not this one.

The plan itself is `docs/superpowers/plans/2026-09-02-obsidian-vault-resync.md` in `ri_ilab` (67 KB, task-by-task with checkboxes and verification commands). It is a working artifact with a status banner of its own, pointed at from here rather than absorbed: what it encodes that still matters — the ground truth it derived, the toolkit it built, and what it left undone — is below.

## Why it existed

Three things were wrong with the notes on 2026-09-02, at commit `75460b6` of `ri_ilab`:

| Problem | Detail |
|---|---|
| A live regression asserted as fact | Three notes said all eleven pipelines run automatically from `main()`. Only 8 of 11 did: `run_research_income()`, `run_research_output()` and `run_facility()` were commented out. A 2026-08-29 working-tree change had briefly uncommented them — which is what the notes described — but it was never committed, and `2b2419e` re-commented them. |
| Content in `docs/` with no note | `docs/2026-08-29-ri-external-institutes-scd2.md` (12 columns, including the always-null `POSTCODE` bug) and `docs/2026-08-29-ri-standalone-remap-tables.md` (7 columns) were reflected nowhere in the vault. |
| No provenance | Every note carried `source_docs: []`, so nothing could check a note's claims against the thing it claimed to describe. `ri_master_list SCD2 Reference` carried 4 of the source doc's 18 columns. |

The plan mirrored `ri_pbi_production`'s 2026-09-01 Obsidian migration (see [[Projects/RI PBI Production/Reference/Migration Coverage|Migration Coverage]]) but scaled down: that one re-synthesised 47 docs from nothing; here the content already existed and the job was re-verification.

## What was built and changed (Tasks 1–9, completed)

| Task | Outcome |
|---|---|
| 1 | `docs/` and `scripts/` in `ri_ilab` tracked in git (they had been untracked); `graphify-out/` added to `.gitignore` |
| 2–5 | A repo-side lint toolkit in `ri_ilab/tools/vault-lint/`: `frontmatter.js` (a verified copy of the vault-wide parser, kept local to avoid a cross-repo `require`), `derive-facts.js` (parses `main.py` for active vs commented-out `run_*()` calls; `--assert <vault>` fails on notes that contradict it), `check-ledger.js` (every `ri_ilab` documentation source claimed by at least one note's `source_docs`), `check-entities.js` (every table heading or `## Column reference` row in a claimed doc carried into the claiming note — the class of miss that had dropped `POSTCODE`), plus `fixtures/`. Each built test-first against a fixture. |
| 6 | The pipeline-automation regression fixed across five notes — [[Overview|RI iLab]], [[iLab Domain Pipelines]], [[Post-Processing & Orchestration]], [[Research Income & Research Output Pipelines]], [[External Institutes & Facility Pipeline]] — verified by `derive-facts.js --assert` going from 5 failures to 0 |
| 7 | `ri_master_list SCD2 Reference` re-verified as the template task, its full 18-column reference table added (now [[Projects/Databricks/Tables/ri_master_list SCD2 Reference|ri_master_list SCD2 Reference]]) |
| 8 | New note for `ri_external_institutes`, and the Databricks-side section of [[External Institutes & Facility Pipeline]] trimmed to a pointer (now [[Projects/Databricks/Tables/ri_external_institutes SCD2 Migration|ri_external_institutes SCD2 Migration]]) |
| 9 | New note for the three remap tables (now [[Projects/Databricks/Tables/Standalone Remap Tables Reference|Standalone Remap Tables Reference]]) |

The plan's two standing rules carried over into how this vault is worked: **ground truth for pipeline-automation claims is `main.py`, re-derived, never a note's prose**; and **known data-quality issues are recorded, not fixed** — `POSTCODE` being `NULL` on every `ri_external_institutes` row and the single-owner, no-service-principal risk on the master-list job were both written down and neither was repaired.

## What was never done (Tasks 10–14)

| Task | Intended | Where it stands |
|---|---|---|
| 10 | Document `scripts/check_stuff.py`, `scripts/classify_nature_science.py`, `scripts/research_outputs.dax` as manual scratch scripts in [[Post-Processing & Orchestration]] | Not done |
| 11 | Re-verify the six remaining notes line-by-line against their sources and give each real `source_docs` | Not done as planned; several of these notes have since been re-verified in other sessions, but not under this plan |
| 12 | Add the two new notes to the Overview's Subsystems table | Moot — the notes moved to `Projects/Databricks/` when that project was split out (`c0b7dc3`), and are linked from both Overviews |
| 13 | Final verification gate: vault-wide linters plus the four new checks | Not run |
| 14 | Pointer paragraph in `ri_ilab/CLAUDE.md` to the vault | Already present by 2026-09-11, added outside this plan |

## Why it was superseded rather than resumed

Between 2026-09-02 and 2026-09-11 the ground the plan stood on moved:

- The repo docs its Ground Truth table and `check-ledger.js` reference were migrated into this vault and **deleted from the repo**: `ri-external-institutes-scd2` and `ri-standalone-remap-tables` (`a87ed1b`, 2026-09-08), `databricks-conventions.md` (same day, now [[Projects/Databricks/Reference/Databricks Conventions|Databricks Conventions]]), and `2026-08-13-historical-services-pipeline.md`, replaced by `2026-09-09-ilab-historical-bronze-tables.md` (`aed1522`, now [[Projects/Databricks/Pipelines/Historical Services Bronze Pipeline|Historical Services Bronze Pipeline]]). The ledger checker's list of seven sources no longer matches what exists.
- The vault itself was restructured: `c0b7dc3` split the Databricks notes into [[Projects/Databricks/Overview|Databricks]], and `67feda5` established the derived/curated/join layer model this vault's `CLAUDE.md` now describes. The plan's file paths under `Projects/RI iLab/Subsystems/` are wrong for every Databricks-side note it names.
- The plan's own success criterion — every note carrying real `source_docs`, checked by a repo-side ledger — was overtaken by the vault-side `stale-check.sh` and `source_commit` mechanism, which answers "is this note current?" against the export rather than against a list of docs.

> [!warning] Do not read the plan's checkboxes as status
> Tasks 1–9 are ticked; Tasks 10–14 are not. That much is accurate, but the unticked tasks cannot be picked up as written — their file paths, source lists and verification commands all predate the restructuring above.

## See also

- [[Overview|RI iLab]] — the project these notes belong to
- [[iLab Domain Pipelines]], [[Post-Processing & Orchestration]], [[Research Income & Research Output Pipelines]], [[External Institutes & Facility Pipeline]] — the notes Task 6 corrected
- [[Projects/Databricks/Tables/ri_master_list SCD2 Reference|ri_master_list SCD2 Reference]], [[Projects/Databricks/Tables/ri_external_institutes SCD2 Migration|ri_external_institutes SCD2 Migration]], [[Projects/Databricks/Tables/Standalone Remap Tables Reference|Standalone Remap Tables Reference]] — the notes Tasks 7–9 produced, since relocated
- [[Projects/RI PBI Production/Reference/Migration Coverage|Migration Coverage]] — the sibling migration this plan was modelled on
- **Derived layer** (`graphify/`, never hand-edited): [[RI iLab Obsidian Vault Reconciliation Plan]], [[derive-facts.js]], [[check-ledger.js]], [[check-entities.js]], [[frontmatter.js]], `Reuse-Don't-Duplicate Vault Checks Constraint` *(no node since export `1ac3015`)*, [[Vault note frontmatter contract (type, project, updated, source_docs, applies_to)]], `_COMMUNITY_Ground-Truth Fact Derivation` and `_COMMUNITY_Entity Ledger Validation` *(both merged into [[_COMMUNITY_Vault Resync Plan]] at export `1ac3015`)*, [[_COMMUNITY_Fixture Three Active]], [[_COMMUNITY_Fixture One Disabled]], [[one-disabled.py]], [[three-active.py]], [[main.py run_() Orchestrator]], `ri_external_institutes SCD2 Migration Note` *(no node since export `1ac3015`; nearest is [[ri_external_institutes SCD2 Table]])*, `Standalone Remap Tables Reference Note` *(no node since export `1ac3015`; nearest is [[Standalone Remap Tables (remap_core_name, remap_customer_institute, remap_customer_lab)]])*
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[main.py]], [[run_facility()]], [[run_research_income()]], [[run_research_output()]]
