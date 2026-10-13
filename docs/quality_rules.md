# Data Quality Rules & Great Expectations Design

**Course:** ETL (G01) — Faculty of Engineering and Basic Sciences  
**Academic Program:** Data Engineering and Artificial Intelligence  
**Institution:** Universidad Autónoma de Occidente (UAO)  
**Project:** Workshop-2: Building a Reliable Batch Data Pipeline  

---

## 1. Quality Policy Framework

Every rule adheres to a strict engineering severity policy:

| Severity Level | Operational Meaning | Policy Action |
| :--- | :--- | :--- |
| **Critical** | The violation invalidates data semantics or makes downstream processing/loading unsafe. | **Immediately blocks** execution of downstream tasks; raises `QualityGateFailureError`; produces diagnostic audit logs. |
| **Warning** | The issue signals unexpected metadata gaps or edge anomalies that can be safely imputed or monitored without invalidating the batch. | Records diagnostic warning; continues processing under documented imputation policy. |
| **Informational** | Provides trend, volume, or statistical distribution signals for observability. | Records telemetry for interpretation; does not alter pipeline execution. |

---

## 2. Complete Quality Rules Register

| Rule ID | Dataset / Layer | Attribute(s) | Quality Dimension | Quality Rule Statement | Metric / Threshold | Severity | Related Requirement | Pipeline Response |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RULE-RAW-SPOTIFY-01** | Raw Spotify | `track_id` | Completeness & Uniqueness | Primary identifier must not be null and must be non-empty string. | Missing values = 0% | **Critical** | REQ-01, REQ-02 | Block pipeline if nulls found. |
| **RULE-RAW-SPOTIFY-02** | Raw Spotify | `danceability` | Validity (Domain Range) | Audio physical/algorithmic metric must strictly fall within interval $[0.0, 1.0]$. | 100% in $[0.0, 1.0]$ | **Critical** | REQ-01, REQ-03 | Block downstream transformation. |
| **RULE-RAW-SPOTIFY-03** | Raw Spotify | `energy` | Validity (Domain Range) | Perceptual audio intensity metric must fall within interval $[0.0, 1.0]$. | 100% in $[0.0, 1.0]$ | **Critical** | REQ-01, REQ-03 | Block downstream transformation. |
| **RULE-RAW-SPOTIFY-04** | Raw Spotify | `valence` | Validity (Domain Range) | Musical positiveness metric must fall within interval $[0.0, 1.0]$. | 100% in $[0.0, 1.0]$ | **Critical** | REQ-01, REQ-03 | Block downstream transformation. |
| **RULE-RAW-SPOTIFY-05** | Raw Spotify | `acousticness` | Validity (Domain Range) | Acoustic probability measure must fall within interval $[0.0, 1.0]$. | 100% in $[0.0, 1.0]$ | **Critical** | REQ-01, REQ-02 | Block downstream transformation. |
| **RULE-RAW-SPOTIFY-06** | Raw Spotify | `popularity` | Validity | Spotify commercial popularity score must be integer in $[0, 100]$. | 100% in $[0, 100]$ | **Warning** | REQ-01, REQ-02 | Warn and log anomalies; continue. |
| **RULE-RAW-SPOTIFY-07** | Raw Spotify | `artists` | Completeness | Performer string must be non-null. | Non-null rate &ge; 99.99% | **Warning** | REQ-01, REQ-02 | Warn and impute with 'Unknown Artist'. |
| **RULE-RAW-GRAMMY-01** | Raw Grammy | `year` | Validity & Timeliness | Award conferral year must fall within historical Grammy span $[1958, 2026]$. | 100% in $[1958, 2026]$ | **Critical** | REQ-03 | Block pipeline if out-of-range year detected. |
| **RULE-RAW-GRAMMY-02** | Raw Grammy | `category` | Completeness | Award classification title must not be null or blank string. | Missing values = 0% | **Critical** | REQ-03 | Block pipeline if category is missing. |
| **RULE-RAW-GRAMMY-03** | Raw Grammy | `winner` | Validity | Award resolution must be boolean representation (`True`, `False`, `1`, `0`). | 100% valid boolean set | **Warning** | REQ-01, REQ-02 | Warn and coerce to boolean; continue. |
| **RULE-PREPARED-01** | Prepared Data (`dim_track`) | `track_id` | Uniqueness & Completeness | Track dimension primary key must be unique across all catalog records. | 100% unique; 0 nulls | **Critical** | REQ-01, REQ-02 | Block Data Warehouse load. |
| **RULE-PREPARED-02** | Prepared Data (`dim_artist`) | `artist_id` | Uniqueness & Completeness | Artist surrogate primary key must be non-null and unique. | 100% unique; 0 nulls | **Critical** | REQ-01, REQ-02 | Block Data Warehouse load. |
| **RULE-PREPARED-03** | Prepared Data (`fact_track_perf`) | `artist_id`, `genre_id` | Referential Integrity | Foreign key references must not be null and must resolve to dimension keys. | 100% non-null valid foreign keys | **Critical** | REQ-01, REQ-02, REQ-03 | Block Data Warehouse load. |
| **RULE-PREPARED-04** | Prepared Data (`fact_grammy_awards`) | `award_year`, `category_id` | Referential Integrity | Dimension references in awards fact table must resolve cleanly. | 100% non-null | **Critical** | REQ-03 | Block Data Warehouse load. |

---

## 3. Great Expectations Implementation Architecture

Each rule is bound to a concrete Great Expectations expectation class evaluated inside an explicit **Expectation Suite**:

### Suite 1: `spotify_raw_suite`
- `gx.expectations.ExpectColumnValuesToNotBeNull(column="track_id")`
- `gx.expectations.ExpectColumnValuesToBeBetween(column="danceability", min_value=0.0, max_value=1.0)`
- `gx.expectations.ExpectColumnValuesToBeBetween(column="energy", min_value=0.0, max_value=1.0)`
- `gx.expectations.ExpectColumnValuesToBeBetween(column="valence", min_value=0.0, max_value=1.0)`
- `gx.expectations.ExpectColumnValuesToBeBetween(column="acousticness", min_value=0.0, max_value=1.0)`
- `gx.expectations.ExpectColumnValuesToBeBetween(column="popularity", min_value=0, max_value=100)`
- `gx.expectations.ExpectColumnValuesToNotBeNull(column="artists", mostly=0.9999)`

### Suite 2: `grammy_raw_suite`
- `gx.expectations.ExpectColumnValuesToBeBetween(column="year", min_value=1958, max_value=2026)`
- `gx.expectations.ExpectColumnValuesToNotBeNull(column="category")`
- `gx.expectations.ExpectColumnValuesToBeInSet(column="winner", value_set=[True, False, 1, 0, "True", "False"])`
- `gx.expectations.ExpectColumnValuesToNotBeNull(column="nominee", mostly=0.99)`

### Suite 3: `prepared_data_master_suite`
- Evaluates `prepared_dim_track_suite`, `prepared_dim_artist_suite`, `prepared_fact_track_suite`, and `prepared_fact_grammy_suite`.
- Enforces strict referential integrity matching between fact foreign keys and dimension primary keys before issuing approval for the target DW loader.
