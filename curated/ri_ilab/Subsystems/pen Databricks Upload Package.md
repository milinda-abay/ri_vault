# pen Databricks Upload Package

`pen/` — two files: `__init__.py` (table-name constants + `CREATE TABLE` SQL strings, wrapped in an `Upload` enum pairing each table name with its schema) and `adb_mace.py` (the upload script itself — see [[Post-Processing & Orchestration]] for what it does). Not part of `main.py`'s pipeline; runs separately, inside a Databricks notebook context.

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: the communities in See also. One change since this was written: the two `AMBIGUOUS` README edges resolved below are no longer in the graph — see that section. The `Upload` enum and DDL details come from reading `pen/`.

## What it depends on

Nothing from the rest of the repo — `pen/__init__.py` is self-contained schema text, and `adb_mace.py` reads `OUTPUT_DATA_PATH` (from `settings`) plus ambient Databricks globals (`spark`, `dbutils`) that only exist when run inside a Databricks notebook.

## Design intent: one enum member per target table

`Upload` pairs a table name with its full `CREATE TABLE IF NOT EXISTS` DDL as a tuple — e.g. `Upload.CHARGES_MASTER = ("ilab_master", create_ilab_charges)`. This is a hand-maintained schema registry: 20 tables' worth of column definitions live here as raw SQL strings, covering both the pipelines this repo produces (`labs`, `members`, `services`, `facility`, `ilab_master`, `external_institutes`) and several **not otherwise present anywhere in this codebase** — `RAM_*`/`RIM_*`/`ROPM_*` tables (award/funding/research-output reference data, judging by column names like `award_holder_count`, `journal_impact_factor_2_year`, `research_indicator`) and `ilab_award_funding_income`. These look like tables produced by a separate process (or a prior version of this pipeline) that `pen/` still knows the shape of, even though nothing in `ilab_ilab/`, `research_income/`, or `research_output/` writes them.

**One incomplete entry**: `create_members_funds = "x"` — a placeholder string, not real DDL, wired into `Upload.MEMBERS_FUND`. If this enum member is ever exercised, it will fail (or silently create a malformed table) rather than create `members_funds` properly. Worth fixing or removing before this path is used for real.

## Resolving two AMBIGUOUS edges the graph flagged

graphify's semantic extraction flagged two low-confidence edges from the root `README.md`, both worth a definitive answer rather than leaving them open. Neither edge is in the export at `1ac3015`: the `pen/readme.md` node is gone, and `requirements.txt Dependencies` has no connections. The resolutions rest on the files themselves, so they still stand:

1. **`README.md` → `pen/readme.md`** (tagged AMBIGUOUS, "references"). The root README describes `pen/` as *"Databricks table name constants and SQL schemas"*; `pen/readme.md` itself says *"Contains scripts to upload files to Monash's Databricks environment."* These aren't actually contradictory — they're describing the package's two different files: `__init__.py` (constants/schemas) and `adb_mace.py` (upload scripts). The graph correctly spotted a description mismatch; the resolution is that both descriptions are true of different halves of the same small package.
2. **`README.md` → `requirements.txt`** (tagged AMBIGUOUS, "conceptually_related_to"). The README states dependencies are managed via `pyproject.toml` — and both files genuinely exist. `pyproject.toml` (modified 2026-06-17) lists a superset of what's in `requirements.txt` (modified 2026-04-10, older) — e.g. `black`, `databricks-connect==16.4.15`, and pinned versions throughout are only in `pyproject.toml`. This isn't ambiguous so much as **stale**: `requirements.txt` looks like a pre-`pyproject.toml` leftover that should probably be deleted rather than kept in sync, unless something outside this repo (a deploy step, a Docker image) still installs from it directly — worth checking before removing.

## See also

- `pen Module README` *(no node since export `1ac3015`)*, [[pen__init__.py]], [[adb_mace.py]] — generated node notes
- [[_COMMUNITY_pen Upload Enum]] — `pen/__init__.py`'s community as of the `ri_ilab` export at `1ac3015` (2026-09-19), renamed from `Upload Type Enum`. `adb_mace.py` now forms a community of its own, [[_COMMUNITY_Databricks Upload (adb_mace)]]. It paired with [[Core SFTP Connector]] in the 2026-09-08 rebuild, then clustered into `Reference Data Pipelines` in the 2026-09-09 one
- [[Post-Processing & Orchestration]] — what `adb_mace.py` actually does when run
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[Upload]], [[upload_to_table()]], [[upload_to_volume()]], [[create_table_from_volume()]]
