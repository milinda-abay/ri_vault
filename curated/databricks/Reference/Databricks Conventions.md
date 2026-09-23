# Databricks Conventions

Standing rules for tables and notebooks in `pen_research_infrastructure_insights_prd`, distilled **2026-08-31** from the `standalone_bronze`/`standalone_silver` schemas (`ri_external_institutes`, `remap_*`, and `sap_customers` — a 174,372-row table with no SCD2 columns and no identifiable producer, since removed from the catalog; confirmed absent 2026-09-14) while building the `ri_external_institutes` silver table. Follow these for new tables and notebooks unless a documented reason says otherwise.

This note is the single source of truth for these rules. It absorbed `docs/databricks-conventions.md` from the `ri_ilab` repo on **2026-09-08**; that file has been deleted and the repo's `CLAUDE.md` now points here. See [[Projects/RI iLab/Reference/Local Development|Local Development]] for the repo's own operational setup.

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: the graphify node counts in the repo-doc table under Documentation, which had drifted and now carry an update. The rules themselves are conventions, which the export doesn't record.

## Medallion layout

- One schema per layer: `standalone_bronze`, `standalone_silver`, `standalone_gold`, and, added 2026-09-17, `pure_bronze`. `pure_silver` now exists too (added 2026-09-18, see [[Pure Silver Pipeline]]); only `pure_gold` remains reserved, not yet created. `mcn_bronze` added 2026-09-23 (see [[MCN Bronze Pipeline]]).
- A table keeps the **same name across layers** (`standalone_bronze.ri_external_institutes` → `standalone_silver.ri_external_institutes`), so lineage is a schema swap, not a name hunt.
- **Bronze**: closest to the source, SCD2 (see below), append-only via merge.
- **Snapshot exception, added 2026-09-17**: a bronze table may instead be a current-rows overwrite snapshot when its source already keeps SCD2 history — for example the Lakehouse PSA (`lakehouse_psa_prd.pure.*`) behind `pure_bronze`. A second SCD2 layer on top of one that already exists would be redundant. See [[Pure Bronze Pipeline]].
- **Silver**: cleaned/conformed, business logic applied (renaming, type fixes, code lookups, dedup) — or a pass-through snapshot of bronze's active rows when there is nothing to clean, as for `ri_master_list` and the three `remap_*` tables since 2026-09-14. Fully reproducible from bronze, so a plain `overwrite` each run — no SCD2 of its own. Reads only bronze's active rows (`_ROW_ACTIVE_FLAG = 'Y'`) and carries the 5 SCD2 columns through unchanged, so silver rows still trace back to a bronze row-version even though silver itself only holds the current snapshot.
- **Gold**: reporting/aggregate layer (schema reserved, not yet populated by these pipelines).

## Column naming

- `UPPER_SNAKE_CASE` for every column, in every layer — including derived/silver-only columns (e.g. `ISO_ALPHA_3_CODE`). No lower_snake_case tables in this catalog.
- String values are uppercased and trimmed on write, even when the source looks already clean — defensive, not load-bearing on today's data.

This is a deliberate departure from the local Python pipeline's own [[Projects/RI iLab/Subsystems/Shared DataFrame Utilities|fix_df()]], which lower-snake-cases columns for the pandas side.

## SCD Type 2 (bronze)

The same shape as [[ri_master_list SCD2 Reference|ri_master_list_history]]'s convention, generalised across `standalone_bronze`. Every bronze table that isn't a pure passthrough carries:

| Column | Type | Meaning |
|---|---|---|
| `_BUSINESS_KEY` | string | `sha2(concat_ws("\|", <identity columns>), 256)` |
| `_SURROGATE_KEY` | bigint | Monotonic, one per row-version, never reused |
| `_START_TIMESTAMP` | timestamp | When this version became active |
| `_EXPIRATION_TIMESTAMP` | timestamp | `9999-12-31 23:59:59.999` sentinel while active |
| `_ROW_ACTIVE_FLAG` | string | `Y`/`N` — exactly one `Y` per `_BUSINESS_KEY` |

- Identity column(s) are chosen deliberately per table (verified unique at migration time) and hardcoded, not inferred.
- Rebuild logic: null-safe-compare incoming vs. active rows; close (`Y`→`N`) anything active with no exact match, insert a new version for anything incoming with no exact match. Unchanged rows aren't touched — no version churn.
- No separate `_history` table + view unless a downstream consumer needs a fixed current-state-only shape (`ri_master_list` is the documented exception, not the default).

## Notebooks

- One notebook per build step, named `<table>_bronze` (e.g. `ri_external_institutes_bronze`, `remap_tables_bronze`), plus one matching validate notebook per build notebook, named `<table>_bronze_validate` (e.g. `ri_external_institutes_bronze_validate`, `remap_tables_bronze_validate`).
- **Clarification, added 2026-09-17: `<table>` is the notebook's logical name, not necessarily the table it writes.** Usually the two match. Two documented exceptions: `remap_tables_bronze` writes three tables (the three `remap_*` tables), not one; and `pure_bronze`'s `dim_application_bronze` writes `dim_upm_application` — the report's own model table is called `dim_application`, so the notebook is named for the report's name rather than the table's. See [[Pure Bronze Pipeline]]. The `_bronze_validate` notebooks are each parameterised over their own `TABLES_TO_VALIDATE` list; the silver validate notebook (below) takes different widgets and this parameterisation doesn't apply to it. Not one shared validate notebook for the whole bronze layer — that was tried (`validate_standalone_bronze`, covering `ri_external_institutes` and all three `remap_*` tables) and split back apart **2026-09-02**: a single combined notebook is a single point of failure, coupling unrelated pipelines' pass/fail status and blast radius together for no benefit, since neither reads the other's tables.
- **The rule now has a silver instance, added 2026-09-12**: `ri_external_institutes_silver` gets its own `ri_external_institutes_silver_validate`, run on its success (see [[ri_external_institutes SCD2 Migration]]). A silver validate is not a repeat of bronze's SCD2 structural checks — uniqueness, overlapping version windows, active-flag/expiration agreement all assume row *history*, and silver holds only the current snapshot, so those checks have nothing to bite on. Instead it's a **parity check against bronze**: row count and the surrogate-key set must match bronze's active rows exactly, in both directions — the check shape a plain-`overwrite` layer with no history of its own actually needs.
- **A pass-through silver validates every column, added 2026-09-14.** Where silver copies bronze's active rows unchanged (`ri_master_list` and the three `remap_*` tables), its validate compares all columns with `exceptAll` in both directions, and the schema by name, type and position, not just row count and surrogate keys. Surrogate-key parity is for a silver that transforms columns, like `ri_external_institutes`, where whole-row equality with bronze cannot hold.
- **Publishing into a schema Power BI reads, added 2026-09-14.** A table that crosses into `ri_lakehouse` is written there by a dedicated `<table>_publish` task. That task copies from silver and depends on the silver validate; the bronze and silver builds never write the serving schema themselves. Power BI therefore sees only rows that passed validation, and a failure anywhere upstream skips publish and leaves the last validated copy in place. The publish notebook checks target against source after writing (schema, row count, `exceptAll` both ways), and its error names the pre-publish Delta version to `RESTORE`. First instance: `ri_master_list_publish` (see [[ri_master_list SCD2 Reference]]).
- Parameterise catalog/schema/table names via `dbutils.widgets.text(...)`, never hardcode a fully-qualified name inline.
- Markdown cells explain **why**, not just what (a design note beats a restated code comment).
- Live under `/Users/<email>/ri_standalone/`, mirroring the `standalone_*` schemas — or, added 2026-09-17, under `/Users/<email>/ri_pure/`, mirroring the `pure_*` schemas (see [[Pure Bronze Pipeline]]), or, added 2026-09-23, under `/Users/<email>/ri_mcn/`, mirroring `mcn_*` (see [[MCN Bronze Pipeline]]). A notebook's home folder always mirrors the schema family it builds.
- **Explained drift, added 2026-09-17**: a validate notebook may compare against a reference table built on a different refresh cycle, in which case exact parity is only possible at certain times of day. Such a validate should still fail on an *unexplained* mismatch, but pass a mismatch when every differing row is attributable to the reference's own refresh lag — see [[Pure Bronze Pipeline#Validation and the explained-drift rule]] for the worked pattern (`dim_external_organisation_bronze_validate`, `fact_application_bronze_validate`).
- **Shared `%run` helper pattern, added 2026-09-18 — a first for this catalog.** `pure_silver_common` is `%run` into every `ri_pure/<table>_silver` and `<table>_silver_validate` notebook, holding the column-uppercasing, string-normalisation, key-guarded write, and structural/parity check functions all 15 tables share. Every bronze notebook to date repeats this code per notebook instead. The reason to share it here: silver's validates prove parity by re-applying the *same* normalisation the build used, so a shared definition is what keeps a validate from passing against a rule the build has quietly stopped following. See [[Pure Silver Pipeline#The shared helper]].

## Reference data

Small, static, rarely-changing lookups are inlined as a Python literal in the notebook that needs them — not staged as a UC volume or its own reference table. Revisit this if a lookup grows large or needs to be shared across multiple notebooks.

> [!note] Superseded example, 2026-09-14
> This convention was originally illustrated with ISO3 country codes inlined in the silver notebook (a hand-maintained `ISO3_MAPPING` dict + `iso3_codes.csv`). That stopped being true **2026-09-02**, when bronze's `COUNTRY` began holding ISO alpha-2 codes directly and the silver notebook switched to joining Monash's shared `lakehouse_bim_prd.country.country` reference table instead (see [[Projects/RI iLab/Subsystems/External Institutes & Facility Pipeline|External Institutes & Facility Pipeline]]). No other currently-inlined small lookup is known to be verified true as a replacement example; this note doesn't invent one.

## Documentation

Non-trivial migrations or design decisions get a dated `docs/YYYY-MM-DD-<topic>.md` in the `ri_ilab` repo — motivation, rebuild pipeline, column reference, and any known data-quality issues (flag, don't silently fix, unless asked).

Once that working record has served its purpose, its durable content is absorbed into a vault note and the repo file is deleted — **unless something under a regeneration contract still sources it**.

> [!warning] Check graphify before deleting a repo doc
> `graphify/ri_ilab/` generates one note per entity found in the repo, including its `docs/*.md`. Deleting a doc that graphify indexes strands the generated notes at the next `/graphify` run, and with them the wikilinks that hand-authored notes make into them. Check first:
>
> ```bash
> grep -rl "source_file:.*<doc-name>" graphify/ri_ilab/ | wc -l
> ```
>
> Zero nodes → safe to absorb and delete. Non-zero → the doc stays in the repo, and the vault note stays a synthesis pointing at it. As of **2026-09-08** that split is:
>
> | Repo doc | graphify nodes | Status |
> |---|---|---|
> | `databricks-conventions.md` | 0 | absorbed → [[Databricks Conventions]], deleted |
> | `2026-08-29-ri-external-institutes-scd2.md` | 0 | absorbed → [[ri_external_institutes SCD2 Migration]], deleted |
> | `2026-08-29-ri-standalone-remap-tables.md` | 0 | absorbed → [[Standalone Remap Tables Reference]], deleted |
> | `2026-08-13-historical-services-pipeline.md` | 15 | **kept**, summarised by [[Historical Services Bronze Pipeline]] |
> | `2026-08-19-ri-master-list-reference.md` | 26 | **kept**, summarised by [[ri_master_list SCD2 Reference]] |
>
> **Update, `ri_ilab` export `1ac3015` (2026-09-19):** `2026-08-13-historical-services-pipeline.md` was deleted anyway, replaced by `2026-09-09-ilab-historical-bronze-tables.md` (14 nodes). As this callout warns, that stranded the vault's links into the old doc's nodes; they were repaired on 2026-09-19. `2026-08-19-ri-master-list-reference.md` now has 28 nodes and stays.

## Known drifts, found 2026-09-12 and deliberately not fixed

Surfaced while wiring up the silver orchestration above; recorded rather than fixed because each one needs a survey this change didn't do.

| Drift | Why it is open |
|---|---|
| `standalone_bronze.ri_master_list_bronze` carries a `_bronze` suffix inside a layer-named schema | Against the "same name across layers" rule this note states above — every other table in `standalone_bronze`/`standalone_silver` obeys it. Renaming it touches consumers that were not surveyed. |
| The three bronze build tasks run on classic `SPOT_WITH_FALLBACK_AZURE` compute, while the silver, silver-validate and publish tasks (seven since 2026-09-14) are serverless | They need Google Sheets egress; whether serverless can reach it is unverified — see [[ri_master_list SCD2 Reference]] for the egress failures documented against the classic cluster itself. |

## See also

- [[Projects/RI iLab/Reference/Local Development|Local Development]] — the `ri_ilab` repo's interpreter, commands, environment variables and version pins
- [[ri_master_list SCD2 Reference]] — the pre-existing SCD2 table this convention generalises from
- [[Projects/RI iLab/Subsystems/External Institutes & Facility Pipeline|External Institutes & Facility Pipeline]] — the pipeline whose bronze → silver build (2026-08-31) prompted writing this down
- [[Standalone Remap Tables Reference]] — a second worked example of the same convention
- [[Pure Bronze Pipeline]] — the snapshot-instead-of-SCD2 exception and the explained-drift validate pattern
- [[Pure Silver Pipeline]] — the shared `%run` helper pattern this note now documents
- [[Projects/RI iLab/Overview|RI iLab]]
- [[Overview|Databricks]] — the catalog these rules govern
- **Derived layer** (`graphify/`, never hand-edited): [[SCD Type 2 Convention (Monash house style)]], [[_BUSINESS_KEY SHA-256 of 8 identity columns]], [[Silver Column Naming UPPER_SNAKE_CASE vs Repo Names]], [[_COMMUNITY_Silver Naming Questions]], [[iLab TableSchema Naming Divergence from standalone_]], [[Inline REMAP_ Literals vs Governed Remap Tables]], [[ri_master_list_bronze_validate Notebook]], `Databricks Table Names and SQL Schemas` *(no node since export `1ac3015`)*
