# Core SFTP Connector

`core/base_connector.py` — a single class, [[ConnectSFTP]], wrapping `paramiko` SFTP access behind `connect()` / `get_files()` / `close()` and a context-manager (`__enter__`/`__exit__`). It's the busiest function or class node in the whole codebase (25 edges; only three file-level nodes have more) because every one of the seven `ilab/*` domains' `fetch.py` imports and calls it.

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: `ConnectSFTP`'s 25 edges and its place as the busiest non-file node, its imports from all seven `ilab/*/fetch.py`, and the community in See also. The auth, `get_files()` and `connect()` behaviour come from reading `core/base_connector.py`, which the export doesn't carry.

## What it depends on

- `settings` for `ILAB_SFTP_HOST`, `ILAB_SFTP_USERNAME`, `ILAB_SFTP_PRIVATE_KEY_LOCATION` (Ed25519 key auth, not password — despite `ILAB_SFTP_PASSWORD` being listed as a required env var in [[Local Development]], this class only ever reads the private-key path).
- `paramiko.Transport` / `paramiko.SFTPClient` directly — no higher-level SFTP wrapper library.

## Design intent

Centralising SFTP auth in one class is why every `ilab/*/fetch.py` looks identical: `with ConnectSFTP() as conn: conn.get_files(...)`. `get_files()` also tolerates being called *without* an active context manager — it checks `self._is_connected`, auto-connects if needed, and auto-closes afterward (the `auto` flag in `get_files()`) — so callers don't have to choose between the context-manager style and a one-shot call.

`connect()` deliberately calls `self.close()` and re-raises on any exception rather than leaving a half-open transport around — a defensive pattern worth keeping if this class is ever touched, since a leaked `paramiko.Transport` on a retry loop would silently exhaust connections.

## Gotcha

`ILAB_SFTP_PASSWORD` is listed as a required environment variable (see [[Local Development]]), but the code path never reads it — only the private-key variables are used. Either the password variable is vestigial (a leftover from a prior auth method) or it's consumed somewhere outside this repo. Worth confirming before assuming it's dead.

## See also

- [[ConnectSFTP]] — the generated node note (full call-site list)
- [[_COMMUNITY_SFTP Connector]] — the community graphify clustered around this class (as of the 2026-09-09 rebuild; also now includes `ilab/services/fetch.py`)
- [[iLab Domain Pipelines]] — the seven pipelines that all depend on this connector
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[_COMMUNITY_core package]], [[base_connector.py]]
