# Test Suite & Approval Testing

`tests/` — `pytest` + `pytest-approvaltests`. Two test areas — file-structure tests and utility-function tests — now cluster together in the graph ([[_COMMUNITY_Test Fixtures & Printers]]) around one shared piece of scaffolding: `tests/conftest.py`.

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: `verify_dataframe_structure()`'s 22 edges and third place among non-file nodes, and the communities named here. Fixture behaviour comes from reading `tests/`.

## What it does

`tests/conftest.py` defines the comparison primitives every structure test reuses:

- `printer_dataframe()` — captures a DataFrame's printed repr + `.info()` output via `capsys`.
- `printer_column_data_types()` / `printer_multiple_dataframe_column_data_types()` — dtype-only summaries (single frame / dict of frames), used when the test cares about schema shape, not values.
- `verify_dataframe_structure()` — wraps `approvaltests.verify()` with the `PythonNativeReporter`. This is the [[verify_dataframe_structure()|third-busiest god node]] in the whole graph (22 edges) because every `test_*_columns()` test in `tests/test_fetch/test_file_structure.py` and every schema test in `tests/test_process/test_file_structure.py` calls it.

**What "approval testing" means for this repo, concretely**: each `test_*_columns()` test doesn't assert against hand-written expected values — it prints a DataFrame's structure (dtypes/shape via the printer helpers above) and diffs that output against a checked-in `.approved.txt` baseline under each test folder's `approved_files/`. A schema change shows up as a failing diff against the baseline file, which then has to be reviewed and re-approved — the standing rule is that baselines live alongside the tests and are updated only when output changes intentionally, after reviewing the diff (see [[Local Development]]). This is why `tests/test_fetch/approved_files/` and `tests/test_process/approved_files/` hold ~20 `.approved.txt` snapshot files that graphify picks up as semantic communities of their own — after the 2026-09-09 rebuild they fragment across several per-domain communities such as [[_COMMUNITY_Utility Approval Snapshots]], [[_COMMUNITY_Members Baselines]] and [[_COMMUNITY_Member Funds Baselines]] — they're not incidental fixtures, they're the actual test oracle.

## `tests/test_utility_functions/` — its own `conftest.py`

Separate fixture set for testing `utils/utility_functions.py` in isolation: synthetic `datetime_dataframe()`/`fix_dataframe()`/`values_dataframe()` fixtures, plus `tmp_gz_files()`/`tmp_parquet_files()` that materialise real temp files on disk (gzip'd CSVs, parquet files with charges-style naming) rather than mocking the filesystem — meaning these tests exercise real I/O (`get_csv_from_zip()`, `csv_to_parquet()`) end-to-end rather than stubbing it out.

## Design intent

Structure-only verification (dtypes/shape, not cell values) is a deliberate choice given the data volumes involved (millions of rows in some domains per [[Projects/Databricks/Pipelines/Historical Services Bronze Pipeline|Historical Services Bronze Pipeline]]) — a full-content golden-file comparison wouldn't be practical here. The trade-off: these tests catch schema drift (a column renamed, a dtype changed) but not value-level regressions in the transform logic itself (e.g. a bug in `create_histology_nodes()`'s cost-centre matching wouldn't fail any test unless it also changed a column's dtype or shape).

## See also

- [[verify_dataframe_structure()]], [[printer_dataframe()]], [[printer_multiple_dataframe_column_data_types()]] — generated node notes
- [[_COMMUNITY_Test Fixtures & Printers]]
- [[Shared DataFrame Utilities]] — what `tests/test_utility_functions/` exercises
- **Derived layer — test files and fixtures** (`graphify/`, never hand-edited): [[tests__init__.py]], [[testsconftest.py]], [[test_utility_functionsconftest.py]], [[test_utility_functions.py]], [[test_fetch_file.py]], [[test_fetchtest_file_structure.py]], [[test_processtest_file_structure.py]], [[test_process_survey.py]], [[test_services_preprocess.py]], [[datetime_dataframe()]], [[fix_dataframe()]], [[values_dataframe()]], [[tmp_gz_files()]], [[tmp_parquet_files()]], [[printer_column_data_types()]], [[_COMMUNITY_tests package]], [[_COMMUNITY_test_fetch package]], [[_COMMUNITY_Services Tests]], [[_COMMUNITY_Survey Tests]]
