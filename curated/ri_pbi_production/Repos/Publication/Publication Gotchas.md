# Publication Gotchas

Known defects, dead code and open questions in [[Publication]]. Everything here is **recorded, not repaired** — each item is listed so it isn't rediscovered, mistaken for a convention, or "corrected" by accident.

> [!warning] Point-in-time snapshot
> Verified against TMDL and the working tree on **2026-09-01**. Re-check before acting on any specific item.

> [!note] Reconciled against [[ri_pbi_publication semantic model]] on 2026-09-19 (`ri_pbi_publication` @ `63ae148a`)
> Checked against the export: the stale `journal_list` path in `File.Contents`, exactly as quoted. No table reaches any of the dead helper cluster, `#shared` and `Query1` included. The `YTD` item's unused `max_day`, and `'Q1 %'`'s unused `monash_publication` variable with its `// Double check this` comment, are both as described. The file's current location, the doc comment on `'Publications per RI Platform'`, the commented-out helper and the hidden flags aren't in the export and rest on the 2026-09-01 read.

## Breaks refresh

### The `journal_list` CSV path is stale

`tables/journal_list.tmdl` loads its partition through an absolute path baked into the M:

```
Csv.Document(File.Contents("C:\Users\maba0001\projects\ri_pbi_publication\ref\journal_list.csv"), [Delimiter = ",", Columns = 3, Encoding = 65001, QuoteStyle = QuoteStyle.None])
```

That path **does not resolve.** It assumes the pre-workspace layout, where the repo sat directly under `projects\`. The file itself is present and healthy at the current location:

```
C:\Users\maba0001\projects\ri_pbi_production\ri_pbi_publication\ref\journal_list.csv
```

So if this table fails to refresh with a file-not-found error, **the CSV is not missing — the path is wrong.** Update the `File.Contents(...)` path with the `pbi-cli` partitions tooling rather than hunting for the file.

Two things make this worse than it first looks. The `journal_list` table has no model relationship to anything; it is consumed only inside the `ropm_research_journal` merge that enriches `dim_journal` with the `nature_science` column ([[Publication Data Model]]). So a silent failure here doesn't break an obvious visual — it removes the Nature/Science family classification from journal data. And any local-file dependency breaks scheduled refresh in the Service regardless of the path, unless a gateway is configured.

[[Risk]] carries the same prior-layout mismatch on a different file. See [[Shared Conventions]] for the suite-wide picture.

## Dead code

- **The `queryGroup: functions` helper cluster** in `expressions.tmdl` — `fix_columns`, `TableType`, `lowercase_col_names`, `preprocess_table_text`, `fix_table_column_type`, `preprocess_table_datetime`, `fetch_task`, plus the introspection expressions `#shared` and `Query1`. None of these is called by any query feeding a live table; every live fetch calls `get_table_from_mace` directly. They read as a general-purpose M utility belt inherited from another project template. Nothing marks them as decommissioned — this model has no `queryGroup: decomissioned` annotation at all, unlike [[Asset]] and [[Risk]] — so they look live until you trace them.
- **`Time intelligence[YTD]`** computes a `max_day` variable that is never referenced in its `RETURN`. See [[Publication Measures]].
- **`'Q1 %'`** computes a `monash_publication` variable that is no longer used in its `DIVIDE`, leaving the measure broader than the variable name implies — and the author's own `// Double check this` comment still sits on that line, unresolved.
- **An older single-argument `get_table_from_mace`** is left commented out immediately above the live two-argument definition. Harmless, but it will mislead anyone who reads the first definition they find.

## Left alone deliberately

### `Calendar[cal_mon_yeat_int]`

The column name contains a typo — "yeat" for "year" — inherited from the M step name that created it. **It is not being renamed.** Any visual or measure bound to the column would break, and the cost of the rename exceeds the cost of the typo. Expect to type it wrong; the model is consistent about it.

### `dim_research_output` has no `EDS_ROW_EXPIRATION_DATE`

Every other PURE-derived dimension carries the full `EDS_ROW_*` audit trio. This one doesn't, because the `ropm_research_output` M query explicitly drops the column. That is intentional, not a load failure.

## Naming that doesn't match behaviour

Three measures compute something other than what their names suggest, and one is a one-off. Full detail in [[Publication Measures]]; recorded here so they surface in a defect sweep:

| Item | Issue |
|---|---|
| `'% Publications Linked to RI'` | Filters PURE's generic `valid` flag. Touches no RI-platform attribute at all, despite the name. |
| `'MNHS Q1 %'` | MNHS-specific denominator, non-MNHS numerator. Only means what it says inside a visual that already filters MNHS. |
| `'Q1 %'` | Broader than its leftover variable and comment suggest — see Dead code above. |
| `'MNHS PUBLICATIONS'` | Faculty hardcoded to MNHS with no equivalent for Science, Pharmacy or Engineering, though `FACULTY_CODE` supports all four. Reads as a one-off request rather than a pattern. |

`'Publications per RI Platform'` carries a doc comment stating it "replaces the previously broken measure". The predecessor is not preserved in TMDL — only the comment, which is the one signal that this area has already had a correction.

## No field-usage cleanup has been run

Not a defect, but it shapes what the Fields pane looks like and is easy to misread as deliberate curation.

**No table in this model is hidden, and exactly one column is** — `Time intelligence[Ordinal]`, a sort helper. Every join key, every source-system audit column (`EDS_ROW_START_DATE`, `EDS_SURROGATE_KEY`, and the rest), and every cross-system key on `dim_ri_master_list` — including `ILAB_CAPABILITY_ID` and `SURVEY_CAPABILITY_ID`, which exist only for other repos and drive nothing here — is visible to report users.

[[Asset]] takes the opposite approach, hiding unused join-key and audit columns and two entire dimension tables. The contrast is worth knowing before assuming a visible column here is one somebody chose to expose.

## Open questions for the model owner

Columns whose purpose could not be settled from the files. Listed with the table they sit on:

| Column | Table | Question |
|---|---|---|
| `upm_project_id` | `fact_pure` | What the associated UPM project record is, and whether anything uses it. |
| `author_id` | `fact_research_output` | How it differs from `researcher_id` on the same row. |
| `service_rls` | `fact_ilab_charges_award_researcher` | The name implies a row-level-security tag, but no role in this repo references it. |

Also unresolved at the model level: whether `fact_research_output` is *meant* to be platform-scoped. If it is, the missing relationship in [[Publication Data Model]] is a live exposure gap; if outputs are intentionally visible across all roles, that decision should be written down. See [[Publication RLS]].

## See also

- [[Publication]] — the repo entry note
- [[Publication Data Model]] — where the missing relationship and the M flow are described
- [[Publication Measures]] — full DAX for the measures listed above
- [[Publication RLS]] — the `TESTING` role gap, recorded with the other RLS findings
- [[Shared Conventions]] — the suite-wide hardcoded-path gotcha
- **Derived layer** (`graphify/`, never hand-edited): [[Hardcoded and External Data Path Dependencies]], [[journal_list]], [[journal_list Table]], [[Publication journal_list.csv Dependency]], [[Publication Research Output RLS Gap]], [[Query1]], [[fetch_task_2]], [[fix_columns_2]], [[lowercase_col_names_3]], [[preprocess_table_text_2]], [[_COMMUNITY_PURE Publication Records]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[TableType_2]], [[fix_table_column_type_2]], [[preprocess_table_datetime_2]], [[get_table_from_mace_8]], [[ropm_research_journal]], [[ropm_research_output]], [[dim_journal]], [[dim_research_output]], [[fact_pure_1]], [[fact_research_output_1]], [[fact_ilab_charges_award_researcher_1]], [[dim_ri_master_list_6]], [[dim_ri_master_list_2]]
