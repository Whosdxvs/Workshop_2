# Reliability Evidence Register

**Course:** ETL (G01) — Faculty of Engineering and Basic Sciences  
**Academic Program:** Data Engineering and Artificial Intelligence  
**Institution:** Universidad Autónoma de Occidente (UAO)  
**Project:** Workshop-2: Building a Reliable Batch Data Pipeline  

---

## Complete Evidence Register

| Evidence ID | Run / Stage | Artifact Path | What It Proves | Related Policy / Rule |
| :--- | :--- | :--- | :--- | :--- |
| **EVID-SRC-01** | Source Preparation | `docs/evidence/source_reconciliation.json` | 4,810 records loaded from `the_grammy_awards.csv` into MySQL `source_grammy_awards` table with exact 100% row-count reconciliation. | Section 4.3 & 6.2 |
| **EVID-PROF-01** | Data Profiling | `notebooks/data_profiling.ipynb` | Fully reproducible, executable notebook evaluating 7 profiling dimensions (Structure, Completeness, Uniqueness, Categorical, Numerical, Temporal, Consistency). | Section 6.3 |
| **EVID-PROF-02** | Data Profiling | `docs/evidence/profiling/completeness_analysis.png` | Empirical visualization of missing value rates in Grammy and Spotify datasets. | Section 6.3 |
| **EVID-PROF-03** | Data Profiling | `docs/evidence/profiling/numerical_distributions.png` | Distribution histograms for danceability, energy, valence, popularity, and acousticness verifying domain bounds. | Section 6.3 |
| **EVID-PROF-04** | Data Profiling | `docs/evidence/profiling/cross_source_overlap.png` | Entity resolution evidence proving 500+ direct artist matches and 700+ song title overlaps between sources. | Section 6.3 |
| **EVID-GX-01** | Raw Validation (Test A) | `docs/evidence/gx_reports/spotify_raw_validation.json` | Great Expectations evaluation of 114,000 raw Spotify records across 7 rules; 100% critical rules passed. | `RULE-RAW-SPOTIFY-01` to `07` |
| **EVID-GX-02** | Raw Validation (Test A) | `docs/evidence/gx_reports/grammy_raw_validation.json` | Great Expectations evaluation of 4,810 raw Grammy records extracted from MySQL table; 100% critical rules passed. | `RULE-RAW-GRAMMY-01` to `04` |
| **EVID-GX-03** | Prepared Validation (Test A)| `docs/evidence/gx_reports/prepared_data_validation.json` | Pre-load validation gate confirming uniqueness of track and artist PKs, foreign key referential integrity, and domain bounds. | `RULE-PREPARED-01` to `04` |
| **EVID-RECON-01**| Transformation | `docs/evidence/integration_reconciliation.json` | Dimensional transformation audit: 113,999 clean Spotify tracks integrated with 4,810 Grammy awards; 10,174 recognized track instances. | Section 6.8 |
| **EVID-TESTA-01**| Test A - Success | `docs/evidence/test_a_success/test_a_results.json` | Full end-to-end execution of both extraction branches, dual validation gates, transformation, and target load with status PASSED. | Section 7.1 |
| **EVID-TESTB-01**| Test B - Failure | `docs/evidence/test_b_controlled_failure/test_b_results.json` | Injected invalid `danceability = 99.5` triggered `QualityGateFailureError` at raw validation gate; blocked all downstream tasks. | Section 7.2 |
| **EVID-TESTB-02**| Test B - Failure | `docs/evidence/test_b_controlled_failure/gx_controlled_failure_report.json` | Machine-readable Great Expectations validation failure report detailing unexpected count and violating values. | `RULE-RAW-SPOTIFY-02` |
| **EVID-TESTC-01**| Test C - Safe Rerun | `docs/evidence/test_c_safe_rerun/safe_rerun_evidence.json` | Before/after comparison verifying net growth of exactly 0 rows across all DW tables and identical measure aggregates. | Section 7.3 |
| **EVID-TESTC-02**| Test C - Safe Rerun | `docs/evidence/test_c_safe_rerun/safe_rerun_report.md` | Executive comparative report proving transactional idempotence and zero duplicate generation. | Section 7.3 |
| **EVID-DASH-01** | Analytics & DW | `docs/evidence/dashboard/interactive_dashboard.html` | Interactive executive HTML dashboard querying the Data Warehouse with KPI ribbons, charts, and data tables. | Section 8.1 |
| **EVID-DASH-02** | Analytics & DW | `docs/evidence/dashboard/kpi_1_grammy_popularity_premium.png` | KPI 1 Visualization: Grammy popularity premium across top genres. | REQ-01 |
| **EVID-DASH-03** | Analytics & DW | `docs/evidence/dashboard/kpi_2_artist_tier_popularity.png` | KPI 2 Visualization: Average track popularity and audio profile by artist recognition tier. | REQ-02 |
| **EVID-DASH-04** | Analytics & DW | `docs/evidence/dashboard/kpi_3_temporal_era_taxonomy.png` | KPI 3 Visualization: Award taxonomy distribution across historical eras. | REQ-03 |
