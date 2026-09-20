# iLab Domain Pipelines

Seven near-identical domains under `ilab/`: `charges`, `labs`, `members`, `member_funds`, `services`, `charge_ack`, `pi_fund`. Each follows `fetch.py` → `preprocess.py` → `process.py` — except `charge_ack` and `pi_fund`, which stop at `preprocess.py` and write parquet directly (no separate `process.py`). All fetch via [[Core SFTP Connector|ConnectSFTP]], all clean via [[Shared DataFrame Utilities|fix_df()/csv_to_parquet()]].

> [!note] Reconciled against the `ri_ilab` export at `1ac3015` (2026-09-19)
> Checked against the export: `main()` calls exactly the eight `run_*()` functions listed below, all seven `ilab/*/fetch.py` import `ConnectSFTP`, and the services clustering in See also holds. The remap dictionaries and per-domain rationale come from reading the code.

## 8 of 11 pipelines run automatically (as of commit `2b2419e`)

`main.py`'s `main()` currently calls eight of the eleven `run_*()` domain functions automatically — `run_charges()`, `run_labs()`, `run_members()`, `run_member_funds()`, `run_services()`, `run_charge_ack()`, `run_pi_fund()`, `run_external_institutes()` — followed by `run_pipeline()`. Three remain commented out: `run_research_income()`, `run_research_output()`, `run_facility()`. Verified directly against the working tree on 2026-09-02 (`git status` shows a clean `main.py`, matching commit `2b2419e`).

**History**: at commit `2b2419e` ("Update test approval and commented non-ilab processes") these three were commented out. A prior version of this vault claimed a 2026-08-29 *uncommitted* working-tree change had re-enabled all three — that change existed briefly but was never committed, and `2b2419e`'s own commit message confirms it re-commented them. Treat any future claim that every domain pipeline runs automatically as needing re-verification against `main.py` directly (`node tools/vault-lint/derive-facts.js main.py`), not against this note's history.

An earlier version of this note additionally claimed `run_labs()`, `run_charge_ack()`, and `run_pi_fund()` were disabled — that was **incorrect**; both the current working tree and every commit checked show all three as always-active calls in `main()`. Corrected here after re-verifying directly against the file rather than relying on the prior note's claim.

## Institutional data-quality patching lives in `ilab/config.py`

Three remap dictionaries, hand-maintained, not derived from any source system:

- `REMAP_CORE_NAME_DICT` — renames facilities to their current display name (e.g. `FLOWCORE` → `FLOWCORE CLAYTON`, `MICROMON` → `MONASH GENOMICS & BIOINFORMATICS PLATFORM (MICROMON GENOMICS)`). Encodes facility renames/mergers over time that iLab's own export doesn't retroactively update. This overlaps with the governed `remap_core_name` Delta table — see [[Projects/Databricks/Tables/Standalone Remap Tables Reference|Standalone Remap Tables Reference]] — but the two are not reconciled or wired together.
- `REMAP_CUSTOMER_INSTITUTE_DICT` — merges duplicate institute records, several explicitly marked in the source data itself as `"(DUPLICATE - DO NOT USE)"` or `"(OBSOLETE_DONOTUSE)"`.
- `REMAP_CUSTOMER_LAB_DICT` — fixes typo'd/whitespace-mangled lab names (double spaces, stray tabs, trailing `&NBSP;`) and marks some labs `"DO NOT USE - ..."` outright.

These are living patches against real-world data drift in an external system (iLab) that this pipeline doesn't control — expect this list to need periodic additions whenever a facility renames or a duplicate institute record surfaces, not a one-time cleanup.

## Per-domain rationale worth knowing before touching the code

- **`charges/process.py`**: `create_histology_nodes()` splits one iLab "MHP" core into `MONASH HISTOLOGY PLATFORM - MHTP/ARA/CLAYTON` sub-nodes by matching specific `revenue_cost_centre_fund` values, with an explicit documented fallback — `# All unmatched cost centres bin to "CLAYTON"`.
- **`charges/process.py`** also carries a **live but commented-out** business rule: `# drop asset_id 336572 or 336573 per email from MXP 27 Apr 2026`. This is the clearest evidence in the whole repo that ad hoc data corrections arrive by email and get encoded directly into the pipeline as code, with the email itself as the only record of *why* — there's no ticket or ADR trail beyond this one-line comment, and it's currently disabled.
- **`charges/process.py`**: `# HACK - Check and remove after 1/12/23` sits directly above a hardcoded override (`customer_lab == "MCEM (ADMIN) LAB"` → force `customer_department` to `"MONASH TECHNOLOGY RESEARCH PLATFORM"`). That removal date is nearly three years in the past — this is stale technical debt nobody has revisited, not a recent decision. Worth checking whether the underlying data issue still exists before removing it.
- **`services/preprocess.py`**: folds three non-standard-named historical CSV sources (`monash_equipment`, `monash_services`, `au_animal_module_asset_id_charge_name`) into the same shape as the live SFTP export, via a `HISTORICAL_SOURCES` config list with per-source date formats. This is a Python-side echo of the same problem [[Projects/Databricks/Pipelines/Historical Services Bronze Pipeline|the Databricks-side historical-services work]] solves — heterogeneous historical exports needing schema reconciliation — but it's a separate, independent implementation against local CSVs, not shared code.
- **`charge_ack/preprocess.py`**: combines three sources (live SFTP `.gz` files, a one-time historical CSV cached to parquet on first read, and the pipeline's own prior output parquet), then filters to `ack_date >= "2024-07-15"` — a fixed cutover date embedded directly in code (`FILTER_DATE`), not read from config.
- **`pi_fund/preprocess.py`**: `post_fetch()` deliberately raises a `FileNotFoundError` with an explicit message ("ensure a parquet file exists before running post_fetch") if `monash_pi_funds.parquet` doesn't already exist, rather than creating it from scratch. This pipeline is designed to be seeded once manually, then incrementally merged — it cannot bootstrap itself from nothing.

## See also

- [[_COMMUNITY_SFTP Connector]], [[_COMMUNITY_Charges Pipeline]] — two of the communities graphify split this domain set into. `ilab/services/*` itself no longer forms one community: as of the 2026-09-09 rebuild, and still at `1ac3015` (2026-09-19), its `preprocess()`/`process()` logic clusters into [[_COMMUNITY_Charge Ack Pipeline]], `fetch()` into [[_COMMUNITY_SFTP Connector]], and its historical-CSV conversion into [[_COMMUNITY_CSV-to-Parquet Post-Fetch]]
- [[chargesprocess.py]], [[chargespreprocess.py]], [[servicespreprocess.py]], [[charge_ackpreprocess.py]], [[pi_fundpreprocess.py]] — generated node notes for the specific files discussed above
- [[Core SFTP Connector]], [[Shared DataFrame Utilities]] — what every domain here depends on
- [[Post-Processing & Orchestration]] — where `main.py`'s dormant-pipeline wiring and the charges/award merge live
- [[iLab Silver Layer Migration]] — the planned Databricks-native port of this pipeline's cleaning logic
- **Derived layer — entry points and per-domain modules** (`graphify/`, never hand-edited): [[run_labs()]], [[run_members()]], [[run_services()]], [[run_charges()]], [[run_charge_ack()]], [[run_member_funds()]], [[run_pi_fund()]], [[create_histology_nodes()]], [[ilabconfig.py]], [[servicesconfig.py]], [[labsfetch.py]], [[labspreprocess.py]], [[labsprocess.py]], [[membersfetch.py]], [[memberspreprocess.py]], [[membersprocess.py]], [[servicesfetch.py]], [[servicesprocess.py]], [[chargesfetch.py]], [[charge_ackfetch.py]], [[member_fundsfetch.py]], [[member_fundspreprocess.py]], [[member_fundsprocess.py]], [[pi_fundfetch.py]], [[_COMMUNITY_ilab package]]
