# Risk

`ri_pbi_risk` — the Power BI PBIP project reporting on the **risk register** for Monash's research infrastructure platforms. Part of [[Overview|RI PBI Production]].

It covers risk descriptions and scoring, inherent versus residual likelihood, impact and rating, owners, controls, mitigation actions, treatment plans and status. Platform owners and RI governance use it to watch risk exposure and control effectiveness.

## Headline figures

Verified against TMDL on 2026-09-01.

| | |
|---|---|
| Semantic model folder | `ri_risk.SemanticModel` |
| Tables | 12 — 1 fact, 7 dimension, 1 date, 2 measure/calculation-group containers, 1 standalone local-file import |
| Relationships | 12 — 10 fact→dimension, 2 dimension→dimension; **3 inactive**; 1 many-to-many |
| Measures | 19 — 18 in `KeyMeasures`, 1 on `dim_likelihood_impact`; plus 4 calculation items in `Time intelligence` |
| RLS roles | 22 — the smallest roster in the suite |

## Inherent versus residual is the model's defining wrinkle

Three rating dimensions each carry **one active and one inactive relationship**, so a visual can switch between the pre-mitigation and post-mitigation view. The catch is that **the orientation is not consistent across the three**:

| Dimension | Active link (default) | Inactive link (needs `USERELATIONSHIP`) |
|---|---|---|
| `dim_risk_rating` | `RESIDUAL_RISK_RATING` — *post*-mitigation | `INHERENT_RISK_RATING` — *pre*-mitigation |
| `dim_impact` | `IMPACT` — *pre*-mitigation | `IMPACT_AFTER_MITIGATION` — *post*-mitigation |
| `dim_likelihood` | `LIKELIHOOD` — *pre*-mitigation | `LIKELIHOOD_AFTER_MITIGATION` — *post*-mitigation |

`dim_risk_rating` defaults to the **residual** view; `dim_impact` and `dim_likelihood` default to the **inherent** view. Opposite orientations, in the same model.

**A measure that assumes one convention holds for all three returns wrong figures silently, without erroring.** Verify against `relationships.tmdl` — or against the `USERELATIONSHIP` calls in `Inherent Risk` and `Post Mitigation Active Risks` — before writing new DAX here. The table above was re-derived from `relationships.tmdl` on 2026-09-01, and the repo's own `CLAUDE.md` now states it correctly.

## Also worth knowing up front

**Three dimensions are hardcoded literals**, not sourced from Databricks: `dim_impact`, `dim_risk_rating` and `dim_likelihood` are plain `#table(...)` scales typed directly in M. A fourth, `dim_likelihood_impact`, is a 25-row bridge cross-joining likelihood × impact to drive a 5×5 risk-matrix heatmap. See [[Risk Data Model]].

**`get_table_from_mace` takes one argument here**, not two — the schema is baked into `Databricks_MACE[database]` as `ri_lakehouse`. Risk is the only repo with the single-argument signature. Check before porting a call from another repo, per [[Shared Conventions]].

**RLS is the simplest in the suite** — one filter, one column, one table, 21 platform roles plus an unfiltered `TESTING` leftover. See [[Risk RLS]].

**The RLS filter column and the join key are the same column** (`CAPABILITY_CODE`), which is tighter coupling than [[Awards]], where the role filters one column of `dim_ri_master_list` and the relationship joins another.

## Detail notes

- [[Risk Data Model]] — the fact, the twelve tables' columns, the inactive relationship pairs, and the M flow
- [[Risk Measures]] — all 19 measures and the 4 calculation items
- [[Risk RLS]] — the 22 roles and the `TESTING` gap

## Known gotchas

Recorded, not repaired. Full detail sits with the relevant note; this is the index.

### The `Sheet1` Excel path does not resolve

> [!warning] Live refresh failure
> The `Sheet1` partition loads via:
>
> ```
> Excel.Workbook(File.Contents("C:\Users\maba0001\projects\ri_pbi_risk\Key Risks.xlsx"), null, true)
> ```
>
> That path is **stale and does not resolve** — rechecked 2026-09-01. It is missing the `ri_pbi_production` workspace folder that now sits between `projects` and `ri_pbi_risk`. The workbook itself is present at `...\projects\ri_pbi_production\ri_pbi_risk\Key Risks.xlsx`.
>
> If `Sheet1` fails to refresh with a file-not-found error, **the file is not missing — the path is wrong.** Fix it via `pbi-cli` partitions tooling. [[Publication]] carries the identical mismatch on `ref/journal_list.csv`; see [[Shared Conventions]].

`Sheet1` is a standalone executive "key risks" summary with **no relationship to any other table** — it sits outside the star schema entirely, so a silent failure here does not break the main register visuals. Any local-file dependency also breaks scheduled refresh in the Service without a gateway.

### Stale doc comments

`fact_risk_register.tmdl` uses `///` doc comments to record business meaning — a convention the repo's `CLAUDE.md` calls out, and the only table in the model that follows it. Three of those comments are now wrong:

- **`CAPABILITY_ID`** claims it "links to `dim_ri_master_list`". **No relationship uses it.** The real join — and the column every RLS role filters — is `CAPABILITY_CODE`, which carries no doc comment at all. Either the comment is stale or the column is redundant.
- **`ISSUBMISSIONCOMPLETED`**, **`OWNERDIVISION`** and **`RECORD_ID`** reference measures — `% Submission Completed`, `Overdue Rate by Division`, `Overdue Reviews` — that **do not exist** in `KeyMeasures` today. Either removed at some point or planned and never built; worth asking the report owner which.

The convention also lapsed: columns added after the initial documentation pass (`INHERENT_RISK_RATING` onward through `CAPABILITY_CODE`) have no doc comments. **Follow it for new columns on this table specifically** — it is the one place in the repo where comments are expected.

### Dead code

- **`data_path`** — a Text parameter defaulting to `C:\Users\teemo\projects\ATR\`, with alternates pointing at `sap_equipment` and `ATR`. Referenced by nothing. Stale boilerplate from another project, and **not** the same thing as the live `Sheet1` path failure above. [[Awards]] carries the identical orphan.
- **The `functions` query group** — `fix_columns`, `TableType`, `lowercase_col_names`, `preprocess_table_text`, `fix_table_column_type`, `preprocess_table_datetime`, `fetch_task`. Only `get_table_from_mace` is actually called. `fetch_task` additionally carries a large commented-out legacy block above its live definition.
- **The `dev` query group** — `'ri_grc_risk_register (2)'` and `'risk_register (2)'`, debug copies referenced by nothing.
- **`Query1` and `#shared`** — Power Query reflection and scratch queries.
- **`Time intelligence[YTD]`** computes a `max_day` variable it never uses — the same leftover [[Publication]] and [[Awards]] both carry in their own `YTD` items.

### Convention deviations

- **`colour_value` is defined on `dim_likelihood_impact`**, not `KeyMeasures` — the model's only departure from the centralised-measures convention. See [[Risk Measures]].
- **The `*_sort` columns are not hidden.** `Impact sort`, `Likelihood sort` and `Rating sort` exist purely to drive `sortByColumn` display order, and all three are visible in the Fields pane. [[Asset]] hides its equivalents. `dim_ri_master_list` and `Calendar` likewise expose every column here — including cross-system keys this repo never uses (`SURVEY_CAPABILITY_ID`, `PURE_FACILITY_ID`, `ILAB_CAPABILITY_ID`).
- **`Calendar[cal_mon_yeat_int]`** carries the "yeat" typo in the column name, exactly as [[Publication]] and [[Survey]] do.

## See also

- [[Overview|RI PBI Production]] — workspace map of all 7 repos
- [[Shared Conventions]] — PBIP layout, Databricks source pattern, the hardcoded-path gotcha
- [[dim_ri_master_list Reference|dim_ri_master_list]] — the shared identity table, joined here on `CAPABILITY_CODE`
- [[RLS Patterns]] — how row-level security is built across the suite
- **Derived layer** (`graphify/`, never hand-edited): [[ri_pbi_risk]], [[ri_pbi_risk Repository]], [[_COMMUNITY_Facility Master Attributes]], [[_COMMUNITY_Risk Register Pipeline]], [[fact_risk_register]], [[dim_ri_master_list_1]], `Key Risks.xlsx` *(source workbook; no node since export `51b1e84`)*, [[Hardcoded and External Data Path Dependencies]]
- **Derived layer — M queries** (`graphify/`, never hand-edited): [[Query1_1]], [[TableType_3]], [[fetch_task_3]], [[fix_columns_3]], [[fix_table_column_type_3]], [[lowercase_col_names_4]], [[preprocess_table_datetime_3]], [[preprocess_table_text_3]], [[get_table_from_mace_2]], [[data_path_4]]
