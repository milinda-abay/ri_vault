# Research Income & Research Output Pipelines

Two domains outside `ilab/`: `research_income/` and `research_output/`. `research_output/` pulls from the Elsevier API (`ELSEVIER_APIKEY`/`ELSEVIER_INSTOKEN`, see [[Local Development]]); `research_income/` ingests a manually-produced CSV rather than an SFTP or API pull.

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: both domains' communities, and `main()` calling neither `run_research_income()` nor `run_research_output()`. The `post_fetch()` rename, the `1000_` stripping and the Elsevier source come from reading the code.

## `research_income/`: manual file drop, not automated fetch

`post_fetch()` starts by renaming a literal `"Research Income.csv"` to `research_income.csv` before converting it. The space-containing original filename strongly suggests this file is manually exported/dropped into the input folder (e.g. from a finance system report) rather than pulled programmatically like the `ilab/*` SFTP domains — there's no `fetch.py` logic pulling from an external source the way `core.ConnectSFTP` does for iLab.

`preprocess()` then strips a literal `"1000_"` prefix from both `fund_centre_id` and `fund_id`:

```python
df["fund_centre_id"] = df["fund_centre_id"].str.replace(r"^1000_", "", regex=True)
df["fund_id"] = df["fund_id"].str.replace(r"^1000_", "", regex=True)
df["fund_fund_centre_id"] = df["fund_centre_id"] + "-" + df["fund_id"]
```

`"1000"` reads as an SAP company code being stripped so the ID matches iLab's own numbering — `fund_fund_centre_id` is the composite key this produces, and it's the exact join key [[Post-Processing & Orchestration|`create_charges_award.py`'s `merge_award()`]] uses to attach award/income data onto `ilab_charges`. This one normalisation step is the load-bearing link between the finance domain and the iLab charges domain — if the SAP prefix convention ever changes, this is where the join breaks silently (a mismatched key produces `NaN` awards, not an error).

## `research_output/`

Elsevier-API-sourced, same `fetch → preprocess → process` shape as the `ilab/` domains, using [[Shared DataFrame Utilities|csv_to_parquet()]] for its post-fetch conversion. No unusual rationale found in the code beyond the standard cleanup pattern.

## Both still commented out of `main()` (as of commit `2b2419e`)

`run_research_income()` and `run_research_output()` are both commented out of `main()` as of commit `2b2419e` ("Update test approval and commented non-ilab processes"). A 2026-08-29 working-tree change briefly re-enabled both, but it was never committed — see [[iLab Domain Pipelines]] for the full history, and [[Post-Processing & Orchestration]] for the input-staleness risk this leaves open in `create_charges_award()` while `run_research_income()` stays disabled.

## See also

- `research_income/` clusters into [[_COMMUNITY_CSV-to-Parquet Post-Fetch]]; `research_output/` into [[_COMMUNITY_Research Output Pipeline]]. As of the `ri_ilab` export at `1ac3015` (2026-09-19) the two still don't share a community: `research_income/`'s was renamed from `Member Data Pipeline`, and `research_output/` got a community of its own when the 2026-09-09 `Reference Data Pipelines` community split up
- [[research_incomepreprocess.py]], [[research_outputpreprocess.py]]
- [[Post-Processing & Orchestration]] — where the `fund_fund_centre_id` join actually gets used
- **Derived layer — entry points and modules** (`graphify/`, never hand-edited): [[run_research_income()]], [[run_research_output()]], [[research_incomefetch.py]], [[research_incomeprocess.py]], [[research_outputfetch.py]], [[research_outputprocess.py]], [[create_charges_award.py]], [[create_charges_award()]], [[merge_award()]]
