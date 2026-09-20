# Post-Processing & Orchestration

`main.py` is the single entry point (`run_*()` per domain, plus `main()` running the automated subset). `pipeline/` holds post-processing transforms that combine multiple domains' output — but only one of its four modules is actually wired into `main()`.

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: `main()` calls exactly eight `run_*()` functions plus `run_pipeline()`, `run_pipeline()` calls only `create_charges_award()`, and nothing calls `create_lab_staff.py`, `process_facility_cc.py` or `create_assets.py`. The merge keys, file paths and `adb_mace.py` behaviour come from reading the code.

## `main.py`: 8 of 11 domains run automatically (as of commit `2b2419e`)

See [[iLab Domain Pipelines]] for the full detail — eight of eleven `run_*()` domain calls currently run in `main()`, followed by `run_pipeline()`. `run_research_income()`, `run_research_output()`, and `run_facility()` are commented out as of commit `2b2419e`. A 2026-08-29 working-tree change briefly uncommented all three, but it was never committed and `2b2419e` re-commented them — treat this as the current, verified state rather than a stale draft.

## `pipeline/create_charges_award.py` — the only `pipeline/` module `main()` calls

`run_pipeline()` calls exactly one thing: `create_charges_award()`. It reads three parquet outputs — `ilab_charges.parquet`, `ilab_charge_ack.parquet`, `research_income.parquet` — and left-merges award and acknowledgment data onto the charges table:

- `merge_award()` joins on `payment_information_cleaned` (from `charges/process.py`'s `clean_payment_information()`) against `research_income`'s `fund_fund_centre_id` (see [[Research Income & Research Output Pipelines]] for how that key is built).
- `merge_charge_ack()` joins on `charge_id`.

**Still an open, silent risk**: `create_charges_award()` runs automatically every time `main()` runs (via `run_pipeline()`), reading three parquet inputs — `ilab_charges.parquet`, `ilab_charge_ack.parquet`, `research_income.parquet`. `run_research_income()`, the pipeline that produces `research_income.parquet`, is currently commented out of `main()` (see above), so `create_charges_award()` is silently depending on that file being produced some other way — an earlier manual run, or stale data already sitting on disk — rather than by the automated sweep itself. A 2026-08-29 working-tree change briefly closed this gap by re-enabling `run_research_income()`, but that change was never committed and has since been reverted; the gap is open again as of `2b2419e`. `create_charges_award()` itself does `pd.read_parquet(...)` on a default path with no explicit freshness or existence check beyond the implicit `FileNotFoundError` pandas would raise — worth flagging to whoever owns `main.py` next, not something this note can fix.

## The other three `pipeline/` modules are manual scratch scripts, not part of orchestration

`create_lab_staff.py`, `process_facility_cc.py`, and `create_assets.py` are **not imported by `main.py` or called by anything** — graphify's structural extraction still picked them up as code (they're real, executable modules), but nothing in the automated pipeline invokes them. Reading them confirms they're exploratory/interactive scripts, not production steps:

- **`create_lab_staff.py`** has no functions at all — it's module-level top-to-bottom script code that builds a master lab-name mapping (`LAB_MAP`) by comparing `ilab_staff`/`labs`/`members` records, and ends with `x.sort_values(...).to_clipboard()` — a call that only makes sense run interactively in a notebook/REPL, not in an automated job.
- **`process_facility_cc.py`** reads a manually-maintained Excel file (`SAP_ASSETS_PATH / "2023-Platform CC list-FiRM Verified1.xlsx"`) and a hardcoded `CC_TO_ID` mapping dict (including an inline `# Verify` comment on one entry — `"EAE SPECIAL PURPOSE-DRONE": "DDP",  # Verify`) to attach SAP cost-centre codes to facilities.
- **`create_assets.py`** ends with a bare `grc_equipment.describe()` — a diagnostic call with no effect on any output file, confirming this is left in a partial/exploratory state.

Treat all three as "run manually when needed, output feeds `facility_cost_centre.parquet` etc. by hand" rather than production code paths — don't assume they execute on any schedule.

## `pen/adb_mace.py`: Databricks upload, run separately from `main.py`

Not part of `main.py` at all — a standalone script (`if __name__ == "__main__"`) intended to run inside a Databricks notebook (`spark`/`dbutils` are used as ambient globals, never imported — this only runs where Databricks provides them). It filters `OUTPUT_DATA_PATH` parquet files against a hardcoded `included_file_list`, then for each: uploads to a Unity Catalog volume, then creates/replaces a managed table from that volume file.

The direct-to-table path exists but is disabled: `# upload_to_table(f, failed_files)` is commented out in favour of the volume-then-table two-step (`upload_to_volume()` + `create_table_from_volume()`). No comment explains why, but the two-step path is the one actually exercised — treat `upload_to_table()` as dead/untested code, not an equivalent alternative, if you need to touch this file.

## See also

- [[_COMMUNITY_Main Orchestration]]
- [[main.py]], [[create_charges_award.py]], [[create_lab_staff.py]], [[process_facility_cc.py]], [[create_assets.py]], [[adb_mace.py]]
- [[iLab Domain Pipelines]] — the dormant-pipeline finding this note builds on
- [[Research Income & Research Output Pipelines]] — the `fund_fund_centre_id` join key consumed here
- [[pen Databricks Upload Package]]
- **Derived layer — functions** (`graphify/`, never hand-edited): [[run_pipeline()]], `run_() Pipeline Functions` *(no node since export `1ac3015`)*, [[main.py run_() Orchestrator]], [[create_charges_award()]], [[merge_award()]], [[merge_charge_ack()]], [[clean_payment_information()]], [[upload_to_table()]], [[upload_to_volume()]], [[create_table_from_volume()]]
