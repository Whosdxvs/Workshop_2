# Workshop 2: Building a Reliable Batch Data Pipeline

**Faculty of Engineering and Basic Sciences**  
**Academic Program:** Data Engineering and Artificial Intelligence  
**Course:** ETL (G01) — 2026-2  
**Institution:** Universidad Autónoma de Occidente (UAO)  
**Authors:** Data Engineering Team  

---

> ### Engineering Principles
> 1. **"A Data Engineer does not build scripts. A Data Engineer designs systems."**
> 2. **"Reliable data pipelines do not assume that data is correct. They verify it."**
> 3. **"Reliable does not mean that nothing fails. Reliable means that failures are anticipated, controlled, and observable."**

---

## Table of Contents
1. [Problem and Analytical Objective](#1-problem-and-analytical-objective)
2. [Analytical Requirements & Scope](#2-analytical-requirements--scope)
3. [Data Sources & Scenario](#3-data-sources--scenario)
4. [Pipeline Architecture](#4-pipeline-architecture)
5. [Data Profiling Findings](#5-data-profiling-findings)
6. [Quality Risks & Explicit Quality Rules](#6-quality-risks--explicit-quality-rules)
7. [Great Expectations Validation Design](#7-great-expectations-validation-design)
8. [Transformation and Integration Strategy](#8-transformation-and-integration-strategy)
9. [Dimensional Model Design (Star Schema)](#9-dimensional-model-design-star-schema)
10. [Airflow DAG Design (TaskFlow API)](#10-airflow-dag-design-taskflow-api)
11. [Failure and Selective Retry Policy](#11-failure-and-selective-retry-policy)
12. [Successful Execution Evidence (Test A)](#12-successful-execution-evidence-test-a)
13. [Controlled Failure Evidence (Test B)](#13-controlled-failure-evidence-test-b)
14. [Repeatability and Safe Rerun Strategy (Test C)](#14-repeatability-and-safe-rerun-strategy-test-c)
15. [Dashboard and Analytical Outputs](#15-dashboard-and-analytical-outputs)
16. [Setup and Execution Instructions](#16-setup-and-execution-instructions)
17. [Assumptions and Limitations](#17-assumptions-and-limitations)

---

## 1. Problem and Analytical Objective
Modern music streaming platforms manage vast catalogs of audio recordings and user behavioral data. However, commercial track success and cultural artistic prestige originate from distinct sources. This project addresses the challenge of integrating **Spotify streaming catalog data** (audio physical features, genre tags, and track popularity) with **Grammy Awards history** (prestigious peer-reviewed nominations and awards across decades) to evaluate:
- The quantifiable commercial and acoustic premium enjoyed by Grammy-recognized music across genres.
- The impact of cumulative career recognition on artist catalog depth and listener reach.
- The historical evolution of musical taxonomy, mood, and award distributions across eras.

To achieve this, we design and implement a production-grade, containerized batch data pipeline orchestrated by **Apache Airflow 3.1.8**, secured by **Great Expectations** automated validation gates at raw and prepared stages, and backed by a dimensional **Data Warehouse (Star Schema)**.

---

## 2. Analytical Requirements & Scope

| ID | Analytical Requirement | Required Data | Source(s) | Expected KPI(s) | Required Level of Detail |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | **Grammy Popularity Premium & Audio Profile Analysis:** Evaluate whether Grammy-recognized tracks exhibit higher Spotify popularity and distinct acoustic/energy balances across genres. | `popularity`, `danceability`, `energy`, `valence`, `acousticness`, `track_genre` from Spotify; `artist`, `nominee`, `winner` from Grammy. | Spotify CSV & Operational Grammy Relational DB | **KPI 1:** Grammy Popularity Premium by Genre (`avg_pop_grammy - avg_pop_standard`).<br>**KPI 2:** Audio Signature Index. | Track level, aggregated by musical genre and award recognition flag. |
| **REQ-02** | **Artist Career Recognition Tier vs. Catalog Reach:** Correlate cumulative lifetime Grammy recognition with artist streaming catalog depth, mean popularity, and explicit content distribution. | `primary_artist`, `popularity`, `explicit` from Spotify; historical `year`, `artist`, `winner` from Grammy. | Spotify CSV & Operational Grammy Relational DB | **KPI 3:** Tier-Based Catalog Mean Popularity (Elite 3+ Wins vs. Recognized 1-2 vs. Emerging).<br>**KPI 4:** Explicit Content Ratio. | Artist level, segmented into 3 recognition tiers. |
| **REQ-03** | **Temporal Evolution of Award Taxonomy & Mood:** Trace historical shifts across award eras in Grammy category groups and musical mood characteristics (valence and energy). | `year`, `category`, `nominee` from Grammy; `valence`, `energy`, `danceability` from Spotify. | Operational Grammy Relational DB & Spotify CSV | **KPI 5:** Award Distribution by Category Group across Eras.<br>**KPI 6:** Mood (Valence & Energy) Decadal Trajectory. | Historical era level (Golden Vinyl 1958-1979, Cassette/CD 1980-1999, Digital/Streaming 2000-Present) and category group. |

---

## 3. Data Sources & Scenario

### 1. Spotify Catalog (`spotify_dataset.csv`)
- **Format:** CSV file (`114,000` rows, `21` columns).
- **Attributes:** Identifiers (`track_id`), metadata (`artists`, `album_name`, `track_name`), commercial metrics (`popularity`), audio physics features (`danceability`, `energy`, `valence`, `tempo`, `loudness`, `acousticness`, `instrumentalness`, `liveness`, `duration_ms`), and taxonomy (`track_genre`).
- **Pipeline Source:** Extracted as an external file source into staging.

### 2. Grammy Awards (`source_grammy_awards`)
- **Operational Source:** Relational Database Table (`source_grammy_awards` in MySQL).
- **Source Preparation (Section 4.3):** The provided `the_grammy_awards.csv` (`4,810` rows) is loaded into the operational relational database during environment setup (`src/setup_source_db.py`).
- **Reconciliation Evidence:** Documented in [source_reconciliation.json](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/source_reconciliation.json) verifying exact row-count equality: `CSV=4810, DB=4810`.
- **Operational Extraction:** The pipeline extracts Grammy data via SQL query from the database, satisfying the Section 4.3 engineering scenario.

---

## 4. Pipeline Architecture

```
[ SPOTIFY CSV ]                                [ GRAMMY RELATIONAL DB ]
       │                                                   │
  extract_spotify                                    extract_grammys
       │                                                   │
validate_spotify_raw                               validate_grammys_raw
 (GX Raw Gate 1)                                    (GX Raw Gate 2)
       │                                                   │
       └─────────────────┬─────────────────────────────────┘
                         │ (Both Validated Branches Converge)
                         ▼
              transform_and_integrate
                         │
                 validate_prepared
                  (GX Prepared Gate)
                         │
                      load_dw
                         │
               [ DATA WAREHOUSE ] (Star Schema)
                         │
             [ ANALYTICS & DASHBOARD ]
```

The detailed architecture specification and diagrams are documented in [docs/architecture.md](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/architecture.md).

---

## 5. Data Profiling Findings

Data profiling was conducted without altering the source data. The complete reproducible Jupyter Notebook is located at [notebooks/data_profiling.ipynb](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/notebooks/data_profiling.ipynb) with summary statistics in [docs/evidence/profiling/profiling_report.md](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/profiling/profiling_report.md).

### Key Evidence-Based Findings:
1. **Structural & Grain Analysis:**
   - Spotify contains `114,000` rows but only `89,741` unique `track_id` values (`24,259` duplicate rows). Multi-genre tracks appear multiple times (e.g. acoustic and folk). The source grain is `(track_id, track_genre)`.
   - In our dimensional model, `dim_track` is deduplicated to unique `track_id` (`89,740` rows), while `fact_track_performance` preserves the `(track_id, genre_id)` performance grain.
2. **Completeness:**
   - Spotify: Exactly 1 record missing `artists`, `album_name`, and `track_name` (row index 65900). Handled via imputation with `'Unknown Artist'`, `'Unknown Album'`, `'Unknown Track'`.
   - Grammy: `artist` is missing in `38.3%` of records (`1,840` rows). This occurs in craft/songwriting categories (Song of the Year) where the performer is recorded inside `workers` or `nominee`. Resolved via multi-field entity extraction in `src/transform.py`.
3. **Categorical Case & Diacritic Variations:**
   - Grammy categories had 638 raw strings but only 630 case-insensitive values (e.g., `'... OR Soloists ...'` vs `'... Or Soloists ...'`).
   - Artist names had accent variations (`'André Previn'` vs `'Andre Previn'`). Handled via Unicode NFD normalization and diacritic removal.
4. **Numerical Content:**
   - All audio features (`danceability`, `energy`, `valence`, `acousticness`) are bounded within $[0.0, 1.0]$.
   - `popularity` is bounded within $[0, 100]$.
   - Exactly 1 record had `duration_ms = 0`, filtered during cleaning.
5. **Cross-Source Entity Overlap:**
   - `500+` artists match directly between Spotify and Grammy.
   - `700+` track titles overlap directly.
   - Over `10,100` Spotify track instances were performed by Grammy Award recipients.

---

## 6. Quality Risks & Explicit Quality Rules

| Rule ID | Layer | Attribute | Quality Dimension | Quality Rule Statement | Threshold | Severity | Related Req. |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RULE-RAW-SPOTIFY-01** | Raw Spotify | `track_id` | Completeness | Primary identifier must not be null. | 100% non-null | **Critical** | REQ-01, REQ-02 |
| **RULE-RAW-SPOTIFY-02** | Raw Spotify | `danceability` | Validity | Metric must strictly fall within $[0.0, 1.0]$. | 100% in $[0.0, 1.0]$ | **Critical** | REQ-01, REQ-03 |
| **RULE-RAW-SPOTIFY-03** | Raw Spotify | `energy` | Validity | Metric must strictly fall within $[0.0, 1.0]$. | 100% in $[0.0, 1.0]$ | **Critical** | REQ-01, REQ-03 |
| **RULE-RAW-SPOTIFY-04** | Raw Spotify | `valence` | Validity | Metric must strictly fall within $[0.0, 1.0]$. | 100% in $[0.0, 1.0]$ | **Critical** | REQ-01, REQ-03 |
| **RULE-RAW-SPOTIFY-05** | Raw Spotify | `acousticness` | Validity | Metric must strictly fall within $[0.0, 1.0]$. | 100% in $[0.0, 1.0]$ | **Critical** | REQ-01, REQ-02 |
| **RULE-RAW-SPOTIFY-06** | Raw Spotify | `popularity` | Validity | Popularity must fall within $[0, 100]$. | 100% in $[0, 100]$ | **Warning** | REQ-01, REQ-02 |
| **RULE-RAW-SPOTIFY-07** | Raw Spotify | `artists` | Completeness | Artist string must not be null. | &ge; 99.99% non-null | **Warning** | REQ-01, REQ-02 |
| **RULE-RAW-GRAMMY-01** | Raw Grammy | `year` | Validity | Award year must fall within $[1958, 2026]$. | 100% in $[1958, 2026]$ | **Critical** | REQ-03 |
| **RULE-RAW-GRAMMY-02** | Raw Grammy | `category` | Completeness | Award category title must not be null. | 100% non-null | **Critical** | REQ-03 |
| **RULE-PREPARED-01** | Prepared Data | `track_id` | Uniqueness | `dim_track` PK must be unique and non-null. | 100% unique | **Critical** | REQ-01, REQ-02 |
| **RULE-PREPARED-02** | Prepared Data | `artist_id` | Uniqueness | `dim_artist` PK must be unique and non-null. | 100% unique | **Critical** | REQ-01, REQ-02 |
| **RULE-PREPARED-03** | Prepared Data | `artist_id`, `genre_id` | Referential Integrity | Fact table FKs must match dimension keys. | 100% referential integrity | **Critical** | REQ-01, REQ-02 |

Full details in [docs/quality_rules.md](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/quality_rules.md).

---

## 7. Great Expectations Validation Design
Implemented in [src/validation.py](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/src/validation.py) using the modern **Great Expectations 1.x API** (`get_context`, `ExpectationSuite`, `ValidationDefinition`, and `run`):
- **Raw Validation Gates:**
  - `spotify_raw_suite`: Evaluates all 7 Spotify raw rules.
  - `grammy_raw_suite`: Evaluates all 4 Grammy raw rules.
  - Generates diagnostic reports in `docs/evidence/gx_reports/`.
- **Prepared Validation Gate:**
  - `prepared_data_master_suite`: Runs sub-suites on `dim_track`, `dim_artist`, `fact_track_performance`, and `fact_grammy_awards`.
  - Enforces that `load_dw` is strictly gated: any Critical failure raises `QualityGateFailureError` and blocks target database insertion.

---

## 8. Transformation and Integration Strategy
Implemented in [src/transform.py](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/src/transform.py) following a unified engineering pipeline:
1. **Cleaning:** Trims whitespace, handles null values via deterministic imputation, removes zero-duration audio anomalies, derives `duration_min`.
2. **Standardization & Harmonization:** Applies Unicode NFD accent removal and case normalization to reconcile artist names across datasets (`André Previn` &rarr; `andre previn`).
3. **Category Taxonomy Classification:** Groups 630 granular award titles into 10 high-level analytical categories (`General Field`, `Pop`, `Rock & Alternative`, `Rap & Hip-Hop`, `R&B / Soul`, `Country & Roots`, `Jazz`, `Classical`, `Latin`, `Specialized & Craft`).
4. **Integration Contract:**
   - **Keys:** Normalized artist names (`norm_artist`) and track/nominee titles (`norm_track`).
   - **Cardinality:** One-to-many (an artist performs multiple tracks; an artist wins multiple Grammys across years).
   - **Unmatched Handling:** Unmatched tracks are retained in `fact_track_performance` with `is_grammy_recognized = False`. Unmatched Grammy awards are retained in `fact_grammy_awards` with `is_spotify_matched = False`.
   - **Audit Report:** Generated at [docs/evidence/integration_reconciliation.json](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/integration_reconciliation.json).

---

## 9. Dimensional Model Design (Star Schema)

### Schema DDL Files:
- MySQL 8.0+: [sql/dw_schema.sql](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/sql/dw_schema.sql)
- PostgreSQL 15+: [sql/dw_schema_postgres.sql](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/sql/dw_schema_postgres.sql)

```
                    ┌─────────────────┐
                    │    dim_time     │
                    ├─────────────────┤
                    │ year (PK)       │
                    │ decade          │
                    │ era             │
                    └────────┬────────┘
                             │
                             │ FK: award_year
                             ▼
┌──────────────────┐       ┌────────────────────────┐       ┌─────────────────────┐
│dim_award_category│       │   fact_grammy_awards   │       │     dim_artist      │
├──────────────────┤       ├────────────────────────┤       ├─────────────────────┤
│ category_id (PK) │◄──────┤ category_id (FK)       │       │ artist_id (PK)      │
│ category_name    │       │ artist_id (FK)         ├──────►│ artist_name         │
│ category_group   │       │ track_id (FK)          │       │ normalized_name     │
└──────────────────┘       │ nominee_title          │       │ is_grammy_winner    │
                           │ is_winner              │       │ total_grammy_wins   │
                           │ is_spotify_matched     │       │ first_win_year      │
                           └────────────────────────┘       │ last_win_year       │
                                                            └──────────┬──────────┘
                                                                       │
                                      ┌────────────────────────────────┘
                                      │ FK: artist_id
                                      ▼
┌──────────────────┐       ┌────────────────────────┐       ┌─────────────────────┐
│    dim_genre     │       │ fact_track_performance │       │      dim_track      │
├──────────────────┤       ├────────────────────────┤       ├─────────────────────┤
│ genre_id (PK)    │◄──────┤ genre_id (FK)          │       │ track_id (PK)       │
│ genre_name       │       │ artist_id (FK)         │       │ track_name          │
└──────────────────┘       │ track_id (FK)          ├──────►│ album_name          │
                           │ popularity             │       │ explicit            │
                           │ danceability           │       │ duration_ms         │
                           │ energy                 │       │ duration_min        │
                           │ valence                │       │ danceability        │
                           │ acousticness           │       │ energy              │
                           │ is_grammy_recognized   │       │ valence             │
                           └────────────────────────┘       └─────────────────────┘
```

- **Fact Table 1 (`fact_track_performance`):** Grain is one row per unique track and genre classification (`113,999` rows).
- **Fact Table 2 (`fact_grammy_awards`):** Grain is one row per Grammy award event (`4,810` rows).

---

## 10. Airflow DAG Design (TaskFlow API)
Implemented in [dags/reliable_music_pipeline.py](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/dags/reliable_music_pipeline.py):
- Authorship uses the modern **Airflow 3.1.8 TaskFlow API** (`from airflow.sdk import dag, task`).
- Clean separation of tasks:
  1. `extract_spotify` (retries: 2, retry_delay: 10s)
  2. `validate_spotify_raw` (retries: 0)
  3. `extract_grammys` (retries: 3, retry_delay: 15s)
  4. `validate_grammys_raw` (retries: 0)
  5. `transform_and_integrate` (retries: 0)
  6. `validate_prepared` (retries: 0)
  7. `load_dw` (retries: 2, retry_delay: 15s)

---

## 11. Failure and Selective Retry Policy
Detailed in [docs/failure_policy.md](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/failure_policy.md):
- **Transient Operational Errors (Network, DB connection glitches):** Configured with selective retries (2-3 retries, 10-15s delay) because intermittent issues resolve without code or data modifications.
- **Deterministic Data Quality & Contract Errors (GX failures, schema violations):** Configured with `retries = 0`. Rerunning with identical invalid input will deterministically reproduce the same failure. The pipeline immediately halts and records actionable error evidence.

---

## 12. Successful Execution Evidence (Test A)
Executed via `src/run_mandatory_tests.py`:
- **Result:** Status **PASSED**. Both extraction branches, dual validation gates, transformation, and Data Warehouse loading executed successfully.
- **Audit File:** [docs/evidence/test_a_success/test_a_results.json](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/test_a_success/test_a_results.json).

---

## 13. Controlled Failure Evidence (Test B)
Executed via `src/run_mandatory_tests.py`:
- **Injected Anomaly:** Spotify batch with impossible `danceability = 99.5` (violating `RULE-RAW-SPOTIFY-02`, bounded in $[0.0, 1.0]$).
- **System Response:**
  - `extract_spotify`: SUCCESS.
  - `validate_spotify_raw`: **FAILED (Controlled)**. Raised `QualityGateFailureError`.
  - `transform_and_integrate`: **BLOCKED** (Not executed).
  - `validate_prepared`: **BLOCKED** (Not executed).
  - `load_dw`: **BLOCKED** (Not executed; 0 dirty records entered the Data Warehouse).
- **Diagnostic Reports:**
  - Machine-readable GX Report: [docs/evidence/test_b_controlled_failure/gx_controlled_failure_report.json](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/test_b_controlled_failure/gx_controlled_failure_report.json).
  - Explanation: [docs/evidence/test_b_controlled_failure/controlled_failure_explanation.md](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/test_b_controlled_failure/controlled_failure_explanation.md).

---

## 14. Repeatability and Safe Rerun Strategy (Test C)
Executed via `src/run_mandatory_tests.py`:
- **Strategy:** Transactional Idempotent Reload (`DELETE FROM table` within atomic transaction `with engine.begin():`).
- **Evidence Comparison (Before vs. After Rerun):**

| Table Name | Count Before Rerun | Count After Rerun | Net Change (Duplicates) | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| `dim_time` | 69 | 69 | **0** | **PASSED** |
| `dim_award_category` | 584 | 584 | **0** | **PASSED** |
| `dim_genre` | 114 | 114 | **0** | **PASSED** |
| `dim_artist` | 19,699 | 19,699 | **0** | **PASSED** |
| `dim_track` | 89,740 | 89,740 | **0** | **PASSED** |
| `fact_track_performance` | 113,999 | 113,999 | **0** | **PASSED** |
| `fact_grammy_awards` | 4,810 | 4,810 | **0** | **PASSED** |

- **Measure Verification:** `avg_popularity` (`33.24`), `avg_danceability` (`0.5668`), and `total_awards` (`4810`) remained mathematically identical before and after rerun.
- **Evidence Report:** [docs/evidence/test_c_safe_rerun/safe_rerun_report.md](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/test_c_safe_rerun/safe_rerun_report.md).

---

## 15. Dashboard and Analytical Outputs
Executed in [src/analytics_dashboard.py](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/src/analytics_dashboard.py) executing direct SQL queries against `music_dw`:
1. **Interactive Executive Dashboard:** Open [docs/evidence/dashboard/interactive_dashboard.html](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/dashboard/interactive_dashboard.html) in any browser.
2. **KPI 1: Grammy Popularity Premium by Genre:**
   - Visual: [docs/evidence/dashboard/kpi_1_grammy_popularity_premium.png](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/dashboard/kpi_1_grammy_popularity_premium.png).
   - Finding: Grammy recognition delivers up to **+25 to +40 popularity points** premium in genres like *pop-film*, *alt-rock*, and *indie-pop*.
3. **KPI 2: Artist Career Recognition Tier vs. Catalog Reach:**
   - Visual: [docs/evidence/dashboard/kpi_2_artist_tier_popularity.png](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/dashboard/kpi_2_artist_tier_popularity.png).
   - Finding: Elite artists (&ge; 3 Grammy wins) average **62.4** popularity, compared to **31.2** for emerging artists.
4. **KPI 3: Award Taxonomy Distribution across Historical Eras:**
   - Visual: [docs/evidence/dashboard/kpi_3_temporal_era_taxonomy.png](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/dashboard/kpi_3_temporal_era_taxonomy.png).
   - Finding: Classical and Jazz dominated the Vinyl era (1958-1979); Pop, Rap, and Specialized Craft dominate the Digital era.

---

## 16. Setup and Execution Instructions

### Prerequisites
- Python 3.11+
- MySQL 8.0+ or PostgreSQL 15+ (or Docker / Docker Compose)

### 1. Clone and Install Dependencies
```bash
git clone <repository_url>
cd Workshop_2
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and configure your database credentials:
```bash
cp .env.example .env
```

### 3. Initialize Source Relational Database
Populate MySQL with the operational Grammy dataset:
```bash
python -m src.setup_source_db
```

### 4. Run Data Profiling
```bash
python -m src.profile_data
python -m src.build_notebook
```

### 5. Execute Mandatory Reliability Tests (Test A, B, C)
```bash
python -m src.run_mandatory_tests
```

### 6. Generate Analytics & Dashboard
```bash
python -m src.analytics_dashboard
```

### 7. Run Containerized Airflow Environment (Docker Compose)
```bash
docker compose up -d
```
Access the Airflow Web UI at `http://localhost:8080` (Username: `airflow`, Password: `airflow`) and trigger the DAG `reliable_music_pipeline`.

---

## 17. Assumptions and Limitations
1. **Entity Resolution:** Artist matching uses Unicode NFD canonical normalization. Collaborative billing with non-standard syntax (e.g., `'Artist A with special guest Artist B'`) is tokenized on the primary credit.
2. **Temporal Coverage:** The Grammy awards dataset covers through 2019; Spotify catalog represents modern snapshots. Historical Grammy tracks not distributed on Spotify are preserved in `fact_grammy_awards` with `is_spotify_matched = False`.
3. **Collation Standards:** MySQL `utf8mb4_0900_ai_ci` treats diacritics as identical in unique constraints; the pipeline handles this via surrogate keys (`artist_id`) and canonical display deduplication.

---

## Reliability Evidence Register Index
The complete index of all 18 evidence artifacts is available in [docs/evidence_register.md](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence_register.md).
