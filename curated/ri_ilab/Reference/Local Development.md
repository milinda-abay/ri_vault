# Local Development

How to run and test the `ri_ilab` repo locally. Absorbed from the repo's `CLAUDE.md` on **2026-09-08**, when that file was reduced to a pointer at this vault. Python 3.12+.

## Python interpreter

Use the venv interpreter directly:

```
C:\Users\maba0001\projects\ri_ilab\.venv\Scripts\python.exe
```

The bare `python` command is **not** on PATH in this environment — it resolves to the Windows Store alias and fails. From PowerShell, invoke via the call operator:

```powershell
& "C:\Users\maba0001\projects\ri_ilab\.venv\Scripts\python.exe" main.py
```

## Commands

| Task | Command |
|---|---|
| Run all tests | `pytest` |
| Run one file or directory | `pytest tests/test_fetch/test_fetch_file.py` / `pytest tests/test_process/` |
| Run one test by name | `pytest -k test_name` |
| Run with coverage | `pytest --cov` |
| Format code | `black .` |
| Run the full pipeline | `python main.py` (via the venv interpreter above) |

Tests use `pytest` with `pytest-approvaltests`; `tests/conftest.py` holds the shared DataFrame comparison helpers. Approval baselines live alongside the tests and must be updated when output changes intentionally — **review the diff before approving**. See [[Test Suite & Approval Testing]] for what these tests do and don't catch.

## Environment variables

All twelve are required:

| Variable | Used for |
|---|---|
| `DATABRICKS_SERVER_HOSTNAME` | Databricks connection |
| `DATABRICKS_HTTP_PATH` | Databricks connection |
| `DATABRICKS_TOKEN` | Databricks connection |
| `ELSEVIER_APIKEY` | Elsevier API ([[Research Income & Research Output Pipelines]]) |
| `ELSEVIER_INSTOKEN` | Elsevier API |
| `ILAB_SFTP_HOST` | iLab SFTP ([[Core SFTP Connector]]) |
| `ILAB_SFTP_USERNAME` | iLab SFTP |
| `ILAB_SFTP_PASSWORD` | iLab SFTP — **see caveat below** |
| `ILAB_SFTP_PRIVATE_KEY_LOCATION` | iLab SFTP (Ed25519 key auth) |
| `GRC_EMAIL` | GRC institutional data system |
| `GRC_PASSWORD` | GRC |
| `COMPUTER` | Environment/host switch |

Loaded by `settings/__init__.py`; folder path constants live in `settings/folders.py`.

> [!warning] `ILAB_SFTP_PASSWORD` may be vestigial
> `ConnectSFTP` only ever reads the private-key path — the password variable is never used on that code path. Either it is a leftover from a prior auth method or something outside this repo consumes it. Confirm before assuming it is dead. See [[Core SFTP Connector]].

## Data storage

- **Databricks** — the primary warehouse; connection comes from the environment variables above.
- **Azure Blob Storage** — intermediate storage, via `azure-identity` / `azure-storage-blob`.
- **Local** — `data/input/`, `data/preprocess/`, `data/output/` for local development runs.

## Databricks configuration

`databricks.yml` defines the asset bundle for deployment. Local development uses `databricks-connect`, pinned to **16.4.15** in `pyproject.toml` — the cluster's runtime version must match this exactly.

> [!note] `requirements.txt` is stale
> `pyproject.toml` is the real dependency manifest and carries the pinned versions; `requirements.txt` looks like a pre-`pyproject.toml` leftover. See [[pen Databricks Upload Package]].

## See also

- [[Projects/Databricks/Reference/Databricks Conventions|Databricks Conventions]] — standing rules for tables and notebooks in `pen_research_infrastructure_insights_prd`
- [[Test Suite & Approval Testing]] — how the approval-test oracle works
- [[Core SFTP Connector]] — the SFTP auth path and its environment variables
- [[Overview|RI iLab]]
- **Derived layer** (`graphify/`, never hand-edited): `RI Insights README` *(no node since export `1ac3015`; the README's node is now [[RI Insights]])*, `Environment and Path Configuration` *(no node since export `1ac3015`)*, [[requirements.txt Dependencies]], [[_COMMUNITY_Requirements]], [[_COMMUNITY_settings package]], [[settings__init__.py]], [[folders.py]], [[_COMMUNITY_Devcontainer Setup]], [[_COMMUNITY_Devcontainer Config]], [[ri_ilab Databricks Asset Bundle]], [[ConnectSFTP]]
