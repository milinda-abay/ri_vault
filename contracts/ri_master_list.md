# contract: ri_master_list (the shared cross-system identity dimension)

mode: snapshot  (documented binding; refreshed live on the work laptop)
layer: bronze → silver → serving
captured: 2026-09-20  (from curated/databricks + the code-only graph)

## binding (canonical FQN)

`pen_research_infrastructure_insights_prd.ri_lakehouse.ri_master_list`

Grain: one row per (capability, node, cost-centre). 117 active rows, ~24 cols.
The single most load-bearing table — every report that filters RI identity joins it,
and it drives row-level security across the suite.

## chain (producer → consumer)

| stage | table | plane |
|---|---|---|
| producer | `standalone_bronze.ri_master_list_bronze` | standalone (Google-Sheet ref) |
| | `standalone_silver.ri_master_list` | standalone silver |
| consumer | `ri_lakehouse.ri_master_list` | serving (what the reports query) |

Written nightly by job `01_standalone_tables` (id `163544004016522`), with a gated
`ri_master_list_publish` step. The `standalone` plane is the only one wired end to end.

## consumers (Power BI) — and why the key varies

The table name matches across repos but the **join key does not carry over**. Read
a repo's role files before trusting any key.

| consumer | join key |
|---|---|
| `ri_pbi_asset` | `CAPABILITY_CODE` |
| `ri_pbi_finance` | `CAPABILITY_CODE` / `NODE_ID` |
| `ri_pbi_publication` | `CAPABILITY_CODE` |
| `ri_pbi_risk` | `CAPABILITY_CODE` |
| `ri_pbi_ilab_utilisation` | `ILAB_CORE_NAME` (renamed its `dim_facility_master_list` → `dim_ri_master_list` 2026-09-15; two filters per role) |
| `ri_pbi_awards` | `ILAB_CAPABILITY_ID` (46 of 48 roles) |
| `ri_pbi_non_ilab_utilisation` | has the table, **no relationship defined yet** |
| `ri_pbi_survey` | **does not use it** — uses `DIM_FACILITY`, joined on `SURVEY_CAPABILITY_ID` |

## note

This is the binding that was aspirational in `obsidian_life` (its `Contracts/` was
empty). On the work laptop, `refresh --live` re-derives it from the live catalog +
the unified graph, and flips `mode:` to `live`.
