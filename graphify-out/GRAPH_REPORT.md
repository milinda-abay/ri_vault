# Graph Report - ri_vault  (2026-09-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1254 nodes · 1981 edges · 102 communities (58 shown, 30 thin omitted)
- Extraction: 90% EXTRACTED · 9% INFERRED · 1% AMBIGUOUS · INFERRED: 180 edges (avg confidence: 0.79)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6099bfc9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 23
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101

## God Nodes (most connected - your core abstractions)
1. `RI Capability Master List (shared cross-repo reference table)` - 69 edges
2. `DIM_FACILITY (shared reference / capability hub)` - 62 edges
3. `RLS gates all access via dim_ri_master_list` - 50 edges
4. `dim_ri_master_list.ILAB_CAPABILITY_ID` - 47 edges
5. `dim_ilab_services.facility_id` - 47 edges
6. `dim_ri_master_list` - 44 edges
7. `dim_ri_master_list.capability_code` - 29 edges
8. `FACT_SURVEY (survey response fact)` - 29 edges
9. `ConnectSFTP` - 25 edges
10. `fix_df()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `fetch()` --calls--> `ConnectSFTP`  [EXTRACTED]
  ilab/labs/fetch.py → core/base_connector.py
- `fetch()` --calls--> `ConnectSFTP`  [EXTRACTED]
  ilab/members/fetch.py → core/base_connector.py
- `fetch()` --calls--> `ConnectSFTP`  [EXTRACTED]
  ilab/services/fetch.py → core/base_connector.py
- `post_fetch()` --calls--> `delete_files()`  [INFERRED]
  ilab/pi_fund/preprocess.py → utils/utility_functions.py
- `post_fetch()` --calls--> `fix_df()`  [INFERRED]
  ilab/pi_fund/preprocess.py → utils/utility_functions.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Databricks MACE live source feeding all Production query-group tables** — ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_expressions_databricks_mace, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_expressions_get_table_from_mace, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_fact_application_fact_application, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_expressions_ri_master_list, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_dim_ri_master_list_dim_ri_master_list [EXTRACTED 0.90]
- **Databricks (MACE) -> Power BI data lineage** — ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_expressions_databricks_mace, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_expressions_get_table_from_mace, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_expressions_ri_master_list, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_tables_fact_finance_forecast_budget_actuals, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_tables_dim_ri_master_list [EXTRACTED 0.90]
- **Rating scale normalization across survey dimension tables** — ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_expressions_satisfaction_rating, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_expressions_likelyhood_rating, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_expressions_timely_rating, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_expressions_effective_rating, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_tables_dim_c_staff_interaction, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_tables_dim_e_training, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_tables_dim_service_completion, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_tables_dim_s_sl_service_satisfaction [EXTRACTED 0.90]
- **RLS row-filter mechanism on shared dim_ri_master_list** — ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_tables_dim_ri_master_list, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_roles_cdco, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_roles_mcem, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_roles_central_admin, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_roles_flow_clayton [EXTRACTED 0.90]
- **Survey data pipeline (Databricks base_ri_survey + master-list base_facility)** — ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_expressions_base_ri_survey, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_expressions_base_facility, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_expressions_ri_master_list, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_tables_fact_survey, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_tables_fact_comments, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_tables_dim_facility [EXTRACTED 0.95]
- **RI iLab utilisation star schema (fact_ilab + 4 dims + measures)** — ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_tables_fact_ilab, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_tables_dim_ri_master_list, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_tables_dim_ilab_lab, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_tables_dim_ilab_services, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_tables_calendar, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_tables_key_measures [EXTRACTED 1.00]
- **RLS filter flow via dim_ri_master_list** — ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_dim_ri_master_list, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_dim_ri_master_list_ilab_capability_id, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_dim_ri_master_list_node_id, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_roles_bcif, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_roles_eng_dce, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_roles_mmic_hmst, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_roles_dvcre_admin [EXTRACTED 1.00]
- **RLS roles filtering DIM_FACILITY (platform via SURVEY_CAPABILITY_ID, faculty via CAPABILITY_GOVERNANCE)** — ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_tables_dim_facility, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_madp, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_cryo, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_bcif, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_marp, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_merc, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_mhp, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_feng_dce, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_mgbp_bi, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_mmic, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_mmi_ara, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_sobs, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_soc, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_central_admin, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_mips_admin, ri_pbi_production::ri_pbi_survey_ri_survey_semanticmodel_definition_roles_mnhs_admin [EXTRACTED 1.00]
- **Awards & income star schema** — ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_fact_research_award_funding, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_fact_research_income, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_fact_ilab, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_dim_awards, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_dim_research_funding_category, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_dim_research_funding_scheme, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_dim_external_organisation, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_dim_finance_fund, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_dim_finance_fund_centre, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_dim_researcher [EXTRACTED 1.00]
- **Asset-cost star schema (fact + dimensions + measures)** — ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_fact_sap_asset_gl_mapping, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_key_measures, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_dim_ri_master_list, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_dim_gl_code, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_dim_cost_centre, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_dim_finance_fund_centre, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_dim_asset, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_dim_asset_class, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_dim_age, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_dim_acquisition_value, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_calendar [INFERRED 0.75]
- **Time Intelligence calculation group over the calendar table** — ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_time_intelligence_time_intelligence, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_calendar_calendar, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_expressions_startdate, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_expressions_enddate [INFERRED 0.75]
- **Databricks MACE cross-repo data sourcing (ri_lakehouse / ri_ilab / ri_research_dashboard)** — ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_expressions_get_table_from_mace, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_expressions_databricks_mace, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_expressions_ri_lakehouse_schema, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_expressions_ri_ilab_schema, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_expressions_ri_research_dashboard_schema [INFERRED 0.80]
- **Publication quality KPI family (app vs pure, peer-reviewed, Q1, collaboration)** — ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_tables_key_measures_unique_publications_app, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_tables_key_measures_peer_reviewed_publications, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_tables_key_measures_peer_reviewed_rate, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_tables_key_measures_unique_publications_q1_app, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_tables_key_measures_q1_pct, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_tables_key_measures_international_collaboration_rate [INFERRED 0.80]
- **Star schema: fact_application joined to 9 dimension tables** — ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_fact_application_fact_application, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_dim_upm_application_dim_upm_application, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_dim_applicant_role_dim_applicant_role, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_dim_external_organisation_dim_external_organisation, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_dim_org_type_dim_org_type, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_calendar_calendar, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_dim_research_organisation_dim_research_organisation, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_dim_upm_award_dim_upm_award, ri_pbi_production::ri_pbi_non_ilab_utilisation_semanticmodel_definition_tables_dim_researcher_dim_researcher [INFERRED 0.85]
- **Finance star/snowflake schema: two facts joined to shared dims** — ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_tables_fact_finance_forecast_budget_actuals, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_tables_fact_fund_management_financial_summary, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_tables_dim_ri_master_list, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_tables_calendar, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_tables_dim_finance_cost_element, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_tables_dim_finance_fund_centre, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_tables_dim_finance_commitment_item, ri_pbi_production::ri_pbi_finance_ri_finance_semanticmodel_definition_tables_dim_finance_value_type_lookup [INFERRED 0.85]
- **GL-account-filtered cost measures** — ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_key_measures_total_cost, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_key_measures_maintenance_cost, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_key_measures_other_assets_auc, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_key_measures_other_equipment, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_dim_gl_code [INFERRED 0.85]
- **Research-income time-intelligence analysis** — ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_fact_research_income, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_calendar, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_time_intelligence, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_keymeasures_research_income, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_keymeasures_actual_amount, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_keymeasures_monash_income, ri_pbi_production::ri_pbi_awards_semanticmodel_definition_tables_keymeasures_pro_rata_amount [INFERRED 0.85]
- **Residual risk rating breakdown measures (all derive from Total Risks)** — ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_tables_keymeasures_total_risks, ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_tables_keymeasures_high_risks, ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_tables_keymeasures_medium_risks, ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_tables_keymeasures_low_risks, ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_tables_keymeasures_extreme_risks [INFERRED 0.85]
- **RI capability usage backbone (fact tables join shared RI master list)** — ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_tables_dim_ri_master_list_dim_ri_master_list, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_tables_fact_ilab_charges_award_researcher_fact_ilab_charges_award_researcher, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_tables_fact_pure_fact_pure, ri_pbi_production::ri_pbi_publication_ri_publication_semanticmodel_definition_tables_fact_research_output_fact_research_output [INFERRED 0.85]
- **RLS facility governance layer (roles filter master_list / services / fact)** — ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_roles_bcif, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_roles_mmic, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_roles_mnhs_admin, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_tables_dim_ri_master_list, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_tables_dim_ilab_services, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_tables_fact_ilab [INFERRED 0.85]
- **RLS propagation chain (roles -> master list -> fact)** — ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_roles_mbi_mbi, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_roles_mcem_mcem, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_roles_pvcri_admin_pvcri_admin, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_dim_ri_master_list, ri_pbi_production::ri_pbi_asset_ri_asset_semanticmodel_definition_tables_fact_sap_asset_gl_mapping [INFERRED 0.85]
- **MACE Databricks data lineage (catalog ri_lakehouse -> fact + master list)** — ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_expressions_databricks_mace, ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_expressions_get_table_from_mace, ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_expressions_ri_grc_risk_register, ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_expressions_ri_lakehouse_ri_master_list, ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_tables_fact_risk_register_fact_risk_register, ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_tables_dim_ri_master_list_dim_ri_master_list [INFERRED 0.90]
- **Risk matrix (likelihood x impact -> colour)** — ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_tables_dim_likelihood_dim_likelihood, ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_tables_dim_impact_dim_impact, ri_pbi_production::ri_pbi_risk_ri_risk_semanticmodel_definition_tables_dim_likelihood_impact_dim_likelihood_impact [INFERRED 0.90]
- **Databricks MACE source pipeline (ilab_3y + ri_lakehouse)** — ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_expressions_get_table_from_mace, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_expressions_databricks_mace, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_expressions_ri_master_list, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_expressions_ilab_award_income_researcher, ri_pbi_production::ri_pbi_ilab_utilisation_ri_ilab_utilisation_semanticmodel_definition_expressions_source_services_adb [INFERRED 0.95]

## Communities (102 total, 30 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (64): RLS role ADA (filter dim_ri_master_list CAPABILITY_CODE=ADA), RLS role AQUA (filter dim_ri_master_list CAPABILITY_CODE=AQUA), RLS role ART (filter dim_ri_master_list CAPABILITY_CODE=ART), RLS role BCIF (filter dim_ri_master_list CAPABILITY_CODE=BCIF), RLS role BDI (filter dim_ri_master_list CAPABILITY_CODE=BDI), RLS role BLTB (filter dim_ri_master_list CAPABILITY_CODE=BLTB), RLS role BUSECO (filter dim_ri_master_list CAPABILITY_CODE=BUSECO), RLS role CDCO (filter dim_ri_master_list CAPABILITY_CODE=CDCO) (+56 more)

### Community 1 - "Community 1"
Cohesion: 0.13
Nodes (25): CaptureFixture, printer_dataframe(), datetime_dataframe(), fix_dataframe(), fixture, Two parquet files using charges-style naming for convert_and_combine_dataframes., Two .gz files each containing a CSV with known content., tmp_gz_files() (+17 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (22): fetch(), _load_historical_source(), _load_sftp_services(), preprocess(), DataFrame, Load and deduplicate SFTP services data., Combine historical and SFTP services data., Load, normalise, and deduplicate a single historical source. (+14 more)

### Community 3 - "Community 3"
Cohesion: 0.14
Nodes (15): post_fetch(), Convert fetched CSV to parquet., post_fetch(), fetch(), post_fetch(), preprocess(), DataFrame, Combine member parquet files. (+7 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (11): ConnectSFTP, Path, fetch(), fetch(), Path, rename_charge_report_files(), fetch(), fetch() (+3 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (17): fetch(), DataFrame, preprocess(), DataFrame, process(), DataFrame, fetch(), DataFrame (+9 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (7): post_fetch(), preprocess(), DataFrame, Convert Research Income CSV file to parquet., process(), DataFrame, Check that services input files have column dtypes matching the output table.

### Community 7 - "Community 7"
Cohesion: 0.17
Nodes (14): main(), run_charge_ack(), run_charges(), run_external_institutes(), run_labs(), run_member_funds(), run_members(), run_pi_fund() (+6 more)

### Community 8 - "Community 8"
Cohesion: 0.17
Nodes (15): post_fetch(), preprocess(), DataFrame, Convert charge report CSV files to parquet., Combine charge parquet files and filter test institutes., clean_payment_information(), create_histology_nodes(), fix_customer_cols() (+7 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (11): claimants, fs, { parseFrontmatter }, path, claimed, fs, { parseFrontmatter }, path (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.22
Nodes (4): fixture, skip, survey_files(), test_clean_survey_handles_missing_values()

### Community 11 - "Community 11"
Cohesion: 0.25
Nodes (5): ALL_CLAIM, facts, fs, NUMBER_WORDS, path

### Community 12 - "Community 12"
Cohesion: 0.47
Nodes (5): classify(), main(), parse_issns(), Classify journals in journal_list.csv as Nature or Science publications. Adds a…, Return a list of uppercase-normalised ISSNs from a comma-separated string.

### Community 13 - "Community 13"
Cohesion: 0.70
Nodes (4): die(), emit_manifest(), say(), export-graph.sh script

### Community 14 - "Community 14"
Cohesion: 0.60
Nodes (3): main(), run_a(), run_c()

### Community 15 - "Community 15"
Cohesion: 0.70
Nodes (4): main(), run_a(), run_b(), run_c()

### Community 17 - "Community 17"
Cohesion: 0.67
Nodes (3): fetch_token(), main(), Run a graphify LLM-backed subcommand against Monash's private Azure AI Foundry…

### Community 27 - "Community 27"
Cohesion: 0.09
Nodes (27): RuntimeError, arg(), build(), cell(), fmt_rows(), main(), Build RI_Delivery_Matrix.html. Usage: python build_matrix.py [--data-only]…, parse_filter_values() (+19 more)

### Community 28 - "Community 28"
Cohesion: 0.05
Nodes (62): Cross-repo dim_ri_master_list join, Databricks_MACE connection, dim_env_awards (fetch), finance_fund (fetch), finance_fund_centre (fetch), get_table_from_mace(), ilab_award_income_researcher (fetch), research_income_fact (fetch) (+54 more)

### Community 29 - "Community 29"
Cohesion: 0.10
Nodes (53): balanced(), buildModel(), by(), callout(), captureExpr(), catFileBatch(), cmp(), collect() (+45 more)

### Community 30 - "Community 30"
Cohesion: 0.03
Nodes (59): RLS role: BCIF, RLS role: BDI-INF, RLS role: BDI-OP, RLS role: BLTB, RLS role: CDCO, RLS role: CENTRAL-ADMIN, RLS role: CRYO, RLS role: DSAIP (+51 more)

### Community 31 - "Community 31"
Cohesion: 0.06
Nodes (57): Summary page, User Feedback for Services page, User Feedback for Equipment page, base_ri_survey (Databricks fetch, survey.ri_survey), effective_rating (rating list), EndDate (parameter), legend (function), likelyhood_rating (rating list) (+49 more)

### Community 32 - "Community 32"
Cohesion: 0.35
Nodes (10): fetch_token(), main(), Run a graphify LLM-backed subcommand against Monash's private Azure AI Foundry…, find_definition_dir(), main(), Path, Build one cross-repo graphify graph scoped to the two things that make the 8…, stage_copy() (+2 more)

### Community 33 - "Community 33"
Cohesion: 0.07
Nodes (52): RLS role BCIF, RLS role BDI-INF, RLS role BDI-OP, RLS role BLTB, RLS role CDCO, RLS role CRYO, RLS role DDP, RLS role DSAIP (+44 more)

### Community 34 - "Community 34"
Cohesion: 0.08
Nodes (48): RLS gates all access via dim_ri_master_list, BCIF (RLS role), BDI-INF (RLS role), BDI-OP (RLS role), BLTB (RLS role), CRYO (RLS role), DSAIP (RLS role), ENG-DCE (RLS role) (+40 more)

### Community 35 - "Community 35"
Cohesion: 0.60
Nodes (5): conf_value(), die(), emit_manifest(), say(), export-graph.sh script

### Community 36 - "Community 36"
Cohesion: 0.83
Nodes (3): hook_file(), installed(), install-hooks.sh script

### Community 47 - "Community 47"
Cohesion: 0.06
Nodes (46): Databricks_MACE (Databricks connection), EndDate (parameter = 2026-12-31), get_table_from_mace (table loader function), ri_master_list (source query, ri_lakehouse), StartDate (parameter = 2000-01-01), fact_application.APPLICANT_EXT_ORG_ID -> dim_external_organisation.EXTERNAL_ORGANISATION_ID, fact_application.APPLICANT_INT_ORG_ID -> dim_research_organisation.RESEARCH_ORGANISATION_ID, fact_application.APPLICATION_DATE -> calendar.cal_date (+38 more)

### Community 48 - "Community 48"
Cohesion: 0.06
Nodes (40): RLS role CDCO - dim_ri_master_list[CAPABILITY_CODE] IN {CDCO}, RLS role CENTRAL_ADMIN - dim_ri_master_list[CAPABILITY_GOVERNANCE] IN {CENTRAL}, RLS role CRYO - dim_ri_master_list[CAPABILITY_CODE] IN {CRYO}, RLS role DVCRE_ADMIN - (no row filter / unrestricted read), RLS role ENG_ADMIN - dim_ri_master_list[CAPABILITY_GOVERNANCE] IN {ENG}, RLS role FLOW_ARA - dim_ri_master_list[NODE_ID] IN {FLOW-ARA}, RLS role FLOW_CLAYTON - dim_ri_master_list[NODE_ID] IN {FLOW-CLAYTON}, RLS role FLOW_MHTP - dim_ri_master_list[NODE_ID] IN {FLOW-MHTP} (+32 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (34): Report page: Asset Report, Report page: Summary, Databricks MACE data source, Relationship: fact.acquisition_value_100K -> dim_acquisition_value.acquisition_value_100K, Relationship: fact.age_5y -> dim_age.age_5y, Relationship: fact.AssetClass -> dim_asset_class.AssetClass, Relationship: fact.AssetNumber -> dim_asset.AssetNumber, Relationship: fact.CapitalizationDate -> calendar.cal_date (+26 more)

### Community 50 - "Community 50"
Cohesion: 0.08
Nodes (34): calendar.cal_year, calendar.quarter, dim_ilab_lab.institution_type_lvl_1, dim_ilab_lab.institution_type_lvl_3, dim_ilab_services.serviceorequipmentid, dim_ilab_services.type, fact_ilab.asset_id, fact_ilab.asset_tat (+26 more)

### Community 51 - "Community 51"
Cohesion: 0.07
Nodes (31): Shared RI capability master list (dim_ri_master_list) across sibling RI PBI repos, base_ilab_award_income_researcher (preprocess, adds asset_tat), base_ilab_lab (splits faculty, joins MHP customer groups), base_services_adb (adds serviceorequipmentid key/search), Databricks_MACE (pen_research_infrastructure_insights_prd / ilab_3y connection), EndDate (calendar upper bound, 2026-12-31), get_table_from_mace (Databricks catalog connector function), ilab_award_income_researcher (source, ilab_3y) (+23 more)

### Community 52 - "Community 52"
Cohesion: 0.22
Nodes (20): printer_column_data_types(), printer_multiple_dataframe_column_data_types(), DataFrame, verify_dataframe_structure(), skip, test_charge_ack_columns(), test_external_institutes_columns(), test_facility_columns() (+12 more)

### Community 53 - "Community 53"
Cohesion: 0.10
Nodes (23): bim_env_finance_value_type_lookup (fetch), bim_env_fund_management_financial_summary (fetch), Databricks_MACE (connection config), process_fund_management_financial_summary (transform), process_ri_lakehouse_finance_forecast_budget_actuals (transform), ri_lakehouse_finance_forecast_budget_actuals (fetch), rel: fact_fund_management_financial_summary.FUND_CENTRE_CODE -> dim_finance_fund_centre.FUND_CENTRE_CODE, rel: fact_fund_management_financial_summary.FINANCIAL_YEAR -> Calendar.cal_year (many) (+15 more)

### Community 54 - "Community 54"
Cohesion: 0.09
Nodes (23): RLS role CDCO, RLS role CRYO, RLS role FLOW, RLS umbrella-code convention (FLOW/MBI/MMI are umbrella codes vs site-level in other repos), RLS role MADP, RLS role MARP, RLS role MBI, RLS role MCAM (+15 more)

### Community 55 - "Community 55"
Cohesion: 0.13
Nodes (20): Databricks_MACE (connection: catalog pen_research_infrastructure_insights_prd), get_table_from_mace (MACE/Databricks fetch function), ilab_charges_award_researcher (MACE fetch: ri_ilab.ilab_charges_award_researcher), pure_publication (MACE fetch: ri_lakehouse.fact_pure_publication), rapm_research_award (MACE fetch: ri_research_dashboard.rapm_research_award), research_organisation (MACE fetch: ri_lakehouse.dim_research_organisation), research_output (MACE fetch: ri_ilab.research_output), ri_ilab (Databricks schema / sibling-repo source) (+12 more)

### Community 56 - "Community 56"
Cohesion: 0.15
Nodes (13): fetch(), preprocess(), DataFrame, Combine lab parquet files., process(), DataFrame, process(), DataFrame (+5 more)

### Community 57 - "Community 57"
Cohesion: 0.18
Nodes (17): rel: fact_ilab_charges_award_researcher.researcher_id -> dim_researcher.RESEARCHER_ID, rel: fact_ilab_charges_award_researcher.core_name -> dim_ri_master_list.ILAB_CORE_NAME, rel: fact_pure.managing_organisation_id -> dim_research_organisation.RESEARCH_ORGANISATION_ID, rel: fact_research_output.managing_organisation_id -> dim_research_organisation.RESEARCH_ORGANISATION_ID, rel: fact_research_output.researcher_id -> dim_researcher.RESEARCHER_ID, dim_research_organisation (research organisation dimension), dim_researcher (researcher dimension), fact_ilab_charges_award_researcher (iLab charges fact) (+9 more)

### Community 58 - "Community 58"
Cohesion: 0.17
Nodes (16): account_finance_cost_element (CUSTOM_CATEGORY categorization), bim_account_finance_cost_element (fetch), rel: fact_finance_forecast_budget_actuals.ACCOUNT_CODE -> dim_finance_cost_element.ACCOUNT_CODE, dim_finance_cost_element, budget_expenditure, budget_monthly_2026, budget_operating_result, budget_revenue (+8 more)

### Community 59 - "Community 59"
Cohesion: 0.15
Nodes (16): MARP governance transition (MNHS->CENTRAL at 2026-01-01), RLS role BUSECO-ADMIN, RLS role CENTRAL-ADMIN, RLS role ENG-ADMIN, RLS role ENG-DMAE, RLS role MIPS-ADMIN, RLS role MNHS-ADMIN, RLS role SCI-ADMIN (+8 more)

### Community 60 - "Community 60"
Cohesion: 0.17
Nodes (16): ri_publication.Report (Fabric report -> semantic model), rel: fact_ilab_charges_award_researcher.completion_date -> Calendar.cal_date, rel: fact_pure.output_year -> Calendar.cal_year, rel: fact_pure.equipment_id -> dim_ri_master_list.PURE_FACILITY_ID, rel: fact_research_output.output_year -> Calendar.cal_year, Calendar (date dimension), fact_pure (PURE publication fact), key_measures (DAX measure container) (+8 more)

### Community 61 - "Community 61"
Cohesion: 0.25
Nodes (13): _ack_date_from_filename(), _clean(), _load_historical_data(), _load_sftp_data(), preprocess(), DataFrame, Path, Read all .gz files from input folder into a single DataFrame. (+5 more)

### Community 62 - "Community 62"
Cohesion: 0.27
Nodes (12): Series, test_get_csv_from_zip(), convert_and_combine_dataframes(), convert_col_to_datetime(), convert_to_date(), convert_to_utc(), create_file_attr_col(), get_csv_from_zip() (+4 more)

### Community 63 - "Community 63"
Cohesion: 0.19
Nodes (14): Relationship (inactive): fact_risk_register.INHERENT_RISK_RATING -> dim_risk_rating.Risk rating, Relationship: fact_risk_register.RESIDUAL_RISK_RATING -> dim_risk_rating.Risk rating, dim_risk_rating (rating scale), Active Risks, Archived Risks, Eliminated Risks, Extreme Risks, % High Residual Risk (+6 more)

### Community 64 - "Community 64"
Cohesion: 0.21
Nodes (12): Risk Register (report page), Summary (report page), Relationship (many-to-one): fact_risk_register.CAPABILITY_CODE -> dim_ri_master_list.CAPABILITY_CODE, fact_risk_register (risk register fact), SCD versioning (fact row versioning via _START/_EXPIRATION_TIMESTAMP, _ROW_ACTIVE_FLAG), Avg Inherent Risk Score, Avg Residual Risk Score, Avg Risk Reduction (+4 more)

### Community 65 - "Community 65"
Cohesion: 0.18
Nodes (12): data_path/StartDate/EndDate (leftover equipment/ATR project parameters), Databricks_MACE (MACE lakehouse connection: catalog pen_research_infrastructure_insights_prd, db ri_lakehouse), get_table_from_mace (MACE Databricks.Catalogs fetch function), ri_grc_risk_register (fetches risk_register from MACE), ri_lakehouse_ri_master_list (fetches ri_master_list from MACE), risk_category (category dimension source: distinct RISK_CATEGORY/RISK_SUB_CATEGORY), risk_register (fact source query: join with risk_category), risk_status (status dimension source: distinct RISK_STATUS) (+4 more)

### Community 66 - "Community 66"
Cohesion: 0.24
Nodes (6): post_fetch(), preprocess(), DataFrame, Convert Research Output CSV file to parquet., process(), DataFrame

### Community 67 - "Community 67"
Cohesion: 0.25
Nodes (11): actuals_expenditure, actuals_monthly, actuals_revenue, Cost recoveries, External Revenue, Internal Monash Allocation, Internal User Revenue, monash_actuals_operating_result (+3 more)

### Community 68 - "Community 68"
Cohesion: 0.24
Nodes (11): Relationship (inactive): fact_risk_register.LIKELIHOOD_AFTER_MITIGATION -> dim_likelihood.Likelihood, Relationship: fact_risk_register.IMPACT -> dim_impact.Impact, Relationship (inactive): fact_risk_register.IMPACT_AFTER_MITIGATION -> dim_impact.Impact, Relationship: dim_likelihood_impact.Likelihood -> dim_likelihood.Likelihood, Relationship: fact_risk_register.LIKELIHOOD -> dim_likelihood.Likelihood, Relationship: dim_likelihood_impact.Impact -> dim_impact.Impact, dim_impact (impact scale), dim_likelihood (likelihood scale) (+3 more)

### Community 69 - "Community 69"
Cohesion: 0.36
Nodes (9): rel: fact_pure.output_id -> dim_research_output.OUTPUT_ID, rel: fact_research_output.output_id -> dim_research_output.OUTPUT_ID, dim_research_output (research output dimension), external_collaboration_rate, International Collaboration Rate, peer_reviewed_publications, Peer-Reviewed Rate, publication_external_collaboration (+1 more)

### Community 70 - "Community 70"
Cohesion: 0.32
Nodes (5): preprocess(), DataFrame, Combine member funds parquet files., process(), DataFrame

### Community 71 - "Community 71"
Cohesion: 0.33
Nodes (6): Relationship: fact_risk_register.CREATETIME -> Calendar.cal_date, Australian fiscal year (Calendar fiscal_year / fy_label, July start), Calendar (date dimension), PY YTD (calc item), Time intelligence (calculation group), YTD (calc item)

### Community 72 - "Community 72"
Cohesion: 0.40
Nodes (6): base_facility (pre_process, from ri_master_list), Databricks_MACE (warehouse config record), get_table_from_mace (function), ri_lakehouse_ri_master_list (Databricks fetch, ilab.ri_master_list), ri_master_list (MACE fetch, ri_lakehouse.ri_master_list), RLS design: row-level security over DIM_FACILITY (not dim_ri_master_list)

### Community 73 - "Community 73"
Cohesion: 0.50
Nodes (3): Path, upload_to_table(), upload_to_volume()

### Community 74 - "Community 74"
Cohesion: 0.40
Nodes (5): ropm_research_journal (MACE fetch: ri_research_dashboard.ropm_research_journal), rel: fact_pure.journal_id -> dim_journal.JOURNAL_ID, rel: fact_research_output.journal_id -> dim_journal.JOURNAL_ID, dim_journal (journal dimension), journal_list (Nature/Science journal classifier)

### Community 75 - "Community 75"
Cohesion: 0.50
Nodes (4): rel: fact_fund_management_financial_summary.COMMITMENT_ITEM_CODE -> dim_finance_commitment_item.COMMITMENT_ITEM_CODE, dim_finance_commitment_item, raw_capex_amount, raw_commitment_amount

### Community 76 - "Community 76"
Cohesion: 0.50
Nodes (4): RLS role DVCRE-ADMIN, RLS role PVCRI-ADMIN, RLS deny-all roles (TESTING/DVCRE-ADMIN/PVCRI-ADMIN have no tablePermission), RLS role TESTING

### Community 77 - "Community 77"
Cohesion: 0.67
Nodes (3): get_table_from_mace (Databricks catalog fetch), process_ri_master_list (transform), ri_master_list (fetch from ri_lakehouse)

## Ambiguous Edges - Review These
- `dim_ri_master_list (shared RI reference table)` → `RLS role: PVCRI-ADMIN (unrestricted admin)`  [AMBIGUOUS]
  /home/mjaby/Projects/ri_pbi_production/ri_pbi_asset/ri_asset.SemanticModel/definition/roles/PVCRI-ADMIN.tmdl · relation: references
- `fact_research_income` → `fact_ilab.payment_information_cleaned -> fact_research_income.FUND_CENTRE_FUND (inactive,bothDirections,many)`  [AMBIGUOUS]
  /home/mjaby/Projects/ri_pbi_production/ri_pbi_awards/ri_pbi_awards.SemanticModel/definition/relationships.tmdl · relation: shares_data_with
- `dim_finance_cost_centre` → `fact_finance_forecast_budget_actuals`  [AMBIGUOUS]
  /home/mjaby/Projects/ri_pbi_production/ri_pbi_finance/ri_finance.SemanticModel/definition/tables/dim_finance_cost_centre.tmdl · relation: shares_data_with
- `dim_finance_cost_centre` → `fact_fund_management_financial_summary`  [AMBIGUOUS]
  /home/mjaby/Projects/ri_pbi_production/ri_pbi_finance/ri_finance.SemanticModel/definition/tables/dim_finance_cost_centre.tmdl · relation: shares_data_with
- `dim_ri_master_list` → `RLS role DVCRE_ADMIN - (no row filter / unrestricted read)`  [AMBIGUOUS]
  /home/mjaby/Projects/ri_pbi_production/ri_pbi_finance/ri_finance.SemanticModel/definition/roles/DVCRE_ADMIN.tmdl · relation: references
- `dim_ri_master_list` → `RLS role PVCRI_ADMIN - (no row filter / unrestricted read)`  [AMBIGUOUS]
  /home/mjaby/Projects/ri_pbi_production/ri_pbi_finance/ri_finance.SemanticModel/definition/roles/PVCRI_ADMIN.tmdl · relation: references
- `dim_ri_master_list` → `RLS role TESTING - (no row filter / unrestricted read)`  [AMBIGUOUS]
  /home/mjaby/Projects/ri_pbi_production/ri_pbi_finance/ri_finance.SemanticModel/definition/roles/TESTING.tmdl · relation: references
- `fact_ilab.core_name` → `dim_ri_master_list.ilab_core_name`  [AMBIGUOUS]
  /home/mjaby/Projects/ri_pbi_production/ri_pbi_ilab_utilisation/ri_ilab_utilisation.SemanticModel/definition/relationships.tmdl · relation: references
- `fact_application (fact table / hub)` → `dim_ri_master_list (shared RI reference table)`  [AMBIGUOUS]
  /home/mjaby/Projects/ri_pbi_production/ri_pbi_non_ilab_utilisation/ri_pbi_non_ilab_utilisation.SemanticModel/definition/relationships.tmdl · relation: conceptually_related_to
- `MNHS PUBLICATIONS` → `RLS role MNHS (filter dim_ri_master_list CAPABILITY_CODE=MNHS)`  [AMBIGUOUS]
  /home/mjaby/Projects/ri_pbi_production/ri_pbi_publication/ri_publication.SemanticModel/definition/tables/key_measures.tmdl · relation: conceptually_related_to
- `Databricks_MACE (MACE lakehouse connection: catalog pen_research_infrastructure_insights_prd, db ri_lakehouse)` → `data_path/StartDate/EndDate (leftover equipment/ATR project parameters)`  [AMBIGUOUS]
  /home/mjaby/Projects/ri_pbi_production/ri_pbi_risk/ri_risk.SemanticModel/definition/expressions.tmdl · relation: conceptually_related_to

## Knowledge Gaps
- **306 isolated node(s):** `ALL_CLAIM`, `facts`, `fs`, `NUMBER_WORDS`, `path` (+301 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 422 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `dim_ri_master_list (shared RI reference table)` and `RLS role: PVCRI-ADMIN (unrestricted admin)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `fact_research_income` and `fact_ilab.payment_information_cleaned -> fact_research_income.FUND_CENTRE_FUND (inactive,bothDirections,many)`?**
  _Edge tagged AMBIGUOUS (relation: shares_data_with) - confidence is low._
- **What is the exact relationship between `dim_finance_cost_centre` and `fact_finance_forecast_budget_actuals`?**
  _Edge tagged AMBIGUOUS (relation: shares_data_with) - confidence is low._
- **What is the exact relationship between `dim_finance_cost_centre` and `fact_fund_management_financial_summary`?**
  _Edge tagged AMBIGUOUS (relation: shares_data_with) - confidence is low._
- **What is the exact relationship between `dim_ri_master_list` and `RLS role DVCRE_ADMIN - (no row filter / unrestricted read)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `dim_ri_master_list` and `RLS role PVCRI_ADMIN - (no row filter / unrestricted read)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `dim_ri_master_list` and `RLS role TESTING - (no row filter / unrestricted read)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._