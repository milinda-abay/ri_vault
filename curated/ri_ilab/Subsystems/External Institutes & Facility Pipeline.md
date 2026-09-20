# External Institutes & Facility Pipeline

Two domains outside the `ilab/` namespace but following the same `fetch → preprocess → process` shape: `facility/` and `external_institutes/`. Both are the simplest pipelines in the repo — `facility/preprocess.py` is, in its entirety:

```python
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    return fix_df(df)
```

`external_institutes/preprocess.py` is the same shape.

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: the `INFERRED` `fix_df()` edges from both `preprocess()` functions, the community in See also, and `main()` calling `run_external_institutes()` but not `run_facility()`. The code excerpt and the Databricks-side history come from the code and the Databricks work, not the export.

## What it depends on

[[Shared DataFrame Utilities|fix_df()]] only — via `from utils import fix_df` (the package-level re-export), not the direct submodule import most other domains use. This is the exact import style that caused graphify's AST extractor to mark these two calls `INFERRED` rather than `EXTRACTED` (see [[Shared DataFrame Utilities]] for the full explanation) — worth knowing if you ever use the graph's confidence labels as a signal, since it's really an artifact of *which* import statement was used, not of code uncertainty.

## Design intent

There isn't much bespoke logic here — no remap dictionaries, no per-domain rationale comments, no date cutovers. Treat these two as the "plain" baseline pipeline shape that [[iLab Domain Pipelines|the seven ilab/ domains]] deviate from whenever they need real cleanup (histology-node splitting, historical-source reconciliation, email-driven corrections, etc.). If a future domain pipeline needs to be added with no special-case logic, this is the template to copy.

`run_facility()` is commented out of `main()`'s automatic sweep as of commit `2b2419e`; a 2026-08-29 working-tree change briefly uncommented it, but that change was never committed and has since been re-commented (see [[iLab Domain Pipelines]]). `run_external_institutes()` was never disabled and has always run automatically — only `external_institutes/` runs automatically today, not `facility/`.

## Databricks-side: `ri_external_institutes` bronze → silver

The bronze-side SCD2 migration (source-of-truth pipeline, `_BUSINESS_KEY`/`_SURROGATE_KEY` mechanics, the `POSTCODE`-always-null bug and its 2026-09-02 fix) is documented in full in [[Projects/Databricks/Tables/ri_external_institutes SCD2 Migration|ri_external_institutes SCD2 Migration]] — that note is what the [[Projects/Databricks/Reference/Databricks Conventions|Databricks Conventions]] note was distilled from.

`external_institutes/preprocess.py` + `process.py` (drop-duplicates, ABN space-stripping) were ported into a separate PySpark notebook and applied to bronze's active rows, producing `standalone_silver.ri_external_institutes`. Silver reads only bronze's active rows and carries its 5 SCD2 columns through unchanged.

The original 2026-08-31 silver build ported the local pipeline's hand-maintained `ISO3_MAPPING` dict + inlined `iso3_codes.csv`. On 2026-09-02, once bronze's `COUNTRY` started holding ISO alpha-2 codes directly (an upstream sheet change), that logic was replaced with a join against Monash's shared `lakehouse_bim_prd.country.country` reference table — `COUNTRY` is renamed `ISO_ALPHA_2_CODE` and passed through raw, and `ISO_ALPHA_3_CODE`, `COUNTRY` (full name), `REGION_NAME`, `SUBREGION_NAME` are looked up from it. The lookup table isn't 1 row per country code (ABS sub-classifications, e.g. `GB` alone has 6 rows), so the notebook dedupes to one row per code first. A validation cell flags any `ISO_ALPHA_2_CODE` that doesn't match the lookup rather than silently fixing it — same "flag, don't silently fix" convention as the bronze `POSTCODE` bug.

## See also

- [[Projects/Databricks/Tables/ri_external_institutes SCD2 Migration|ri_external_institutes SCD2 Migration]] — the full bronze-side SCD2 migration writeup
- [[Projects/Databricks/Reference/Databricks Conventions|Databricks Conventions]] — medallion/SCD2/notebook conventions distilled from the `ri_external_institutes` silver build
- [[_COMMUNITY_External Institutes Pipeline]] — as of the `ri_ilab` export at `1ac3015` (2026-09-19), `facility/` and `external_institutes/` form a community of their own again. The 2026-09-09 rebuild had put them in a broader `Reference Data Pipelines` community with `research_output/` and `pen/adb_mace.py`, which has since split up
- [[facilitypreprocess.py]], [[external_institutespreprocess.py]]
- [[Shared DataFrame Utilities]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[run_external_institutes()]], [[run_facility()]], [[external_institutesfetch.py]], [[external_institutesprocess.py]], [[facilityfetch.py]], [[facilityprocess.py]], [[POSTCODE Always-NULL Bug (ri_external_institutes)]]
