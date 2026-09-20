# Shared DataFrame Utilities

`utils/utility_functions.py` — the pure-pandas utility layer everything else sits on top of. No dependency on any other module in this repo; 4 of the graph's top 10 god nodes live here: [[fix_df()]] (24 edges), [[csv_to_parquet()]] (21 edges), [[convert_and_combine_dataframes()]] (16 edges), [[convert_col_to_datetime()]] (11 edges).

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: the four edge counts, and all four functions' place in the top 10 non-file nodes (`convert_col_to_datetime()` is 9th). One change since this was written: `fix_df()` now has four `INFERRED` call edges, not two — see Design intent. The TODO line numbers and function behaviour come from reading `utils/utility_functions.py`.

## What it does

- **[[fix_df()]]** — the universal post-fetch cleanup step: normalise column names (`fix_column_names()`/`lower_underscore()`), uppercase+strip every string/object column (`fix_values()`), sort columns alphabetically (`sort_columns_by_name()`), then `convert_dtypes()`. Every domain's `preprocess()` funnels through this at least once.
- **[[csv_to_parquet()]]** — asserts *exactly one* CSV matches a glob mask, converts it to parquet, deletes the source CSV. The one-file assertion is a deliberate guard: it fails loudly if a fetch produced zero or multiple files instead of silently picking one.
- **[[convert_and_combine_dataframes()]]** — reads multiple parquet files, auto-detects and converts any column with `"date"` in its name, runs `fix_df()`, drops all-null columns, de-duplicates.
- Date-handling pair **[[convert_to_utc()]]** / **[[convert_to_date()]]** — parses to UTC with `errors="coerce"` (bad dates become `NaT` rather than raising), then truncates to a bare date.
- File-status helpers **[[identify_latest_data_rows()]]** / **[[remove_file_status_columns()]]** — mark rows from the most-recently-fetched file as `"ACTIVE"` vs `"INACTIVE"` rather than dropping older rows outright, so downstream tables can distinguish current vs superseded snapshot rows.

## Design intent

`fix_df()`'s ubiquity is *why* it's a graph god node — nearly every domain's `preprocess.py` calls it, directly or via `convert_and_combine_dataframes()`/`csv_to_parquet()`. A prior graphify query traced this: two callers (`facility/preprocess.py`, `external_institutes/preprocess.py`) import via the package re-export `from utils import fix_df` rather than `from utils.utility_functions import fix_df`, which is why graphify's AST extractor marked those two call edges `INFERRED` instead of `EXTRACTED` — a blind spot in the extractor (it doesn't follow `__init__.py`'s `from .utility_functions import *`), not a real code issue. Any function reached only through the package-level import will show the same gap. As of the export at `1ac3015`, two more `fix_df()` call edges are `INFERRED`: from `post_fetch()` in `ilab/pi_fund/preprocess.py` and from `process()` in `external_institutes/process.py`. Whether the import style is the cause there too isn't visible in the export.

## Two open TODOs, left in place

- **L23, inside `fix_df()`**: `# TODO: verify and implement alternative method`, followed by three commented-out lines that would re-implement the same uppercase/strip logic `fix_values()` already does live, just inline instead of via a helper call. Reads like an unfinished refactor attempt that was abandoned mid-way rather than reverted.
- **L78, inside `fix_column_names()`**: `# TODO make this a test` — the duplicate-column-name check is currently a bare `assert all(conditions), "Duplicated columns found"` inside the function itself; the TODO flags that this should be pulled out into proper test coverage instead of living as a runtime assertion.

Neither affects behaviour today, but both are signals of unfinished work rather than settled design — don't assume the commented block or the inline assert is intentional final-state.

## See also

- [[iLab Domain Pipelines]] — the seven domains that call into this layer
- [[Core SFTP Connector]] — the other cross-cutting dependency every domain shares
- [[iLab Silver Layer Migration]] — where `fix_df()`/`identify_latest_data_rows()` would need a Spark equivalent
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[utility_functions.py]], [[fix_column_names()]], [[fix_values()]], [[lower_underscore()]], [[sort_columns_by_name()]]
