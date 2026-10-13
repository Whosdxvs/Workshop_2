# System Architecture & Pipeline Design

**Course:** ETL (G01) — Faculty of Engineering and Basic Sciences  
**Academic Program:** Data Engineering and Artificial Intelligence  
**Institution:** Universidad Autónoma de Occidente (UAO)  
**Project:** Workshop-2: Building a Reliable Batch Data Pipeline  

---

## 1. High-Level Architecture Overview

The system implements a reliable, dual-gate batch data pipeline orchestrated by **Apache Airflow 3.1.8** using the modern **TaskFlow API** (`from airflow.sdk import dag, task`). It integrates two heterogeneous data sources:
1. **Spotify Streaming Catalog:** Provided as a semi-structured CSV dataset (114,000 track-genre entries).
2. **Grammy Awards History:** Extracted from a relational operational source table (`source_grammy_awards` in MySQL) rather than directly from CSV, satisfying the Section 4.3 engineering scenario requirement.

The analytical product is a trusted dimensional **Data Warehouse (Star Schema)** supporting executive KPIs and dashboards.

```mermaid
flowchart TD
    subgraph Sources["1. Heterogeneous Data Sources"]
        S_CSV[("Spotify Catalog (CSV)<br/>spotify_dataset.csv")]
        G_SRC[("Grammy Operational Relational DB<br/>source_grammy_awards (MySQL)")]
    end

    subgraph Extraction["2. Operational Extraction"]
        E_SPOT["extract_spotify<br/>(Reads CSV to staging)"]
        E_GRAM["extract_grammys<br/>(SQL Query against Relational Source)"]
    end

    subgraph RawGates["3. Raw Validation Gates (Great Expectations)"]
        V_SPOT["validate_spotify_raw<br/>(spotify_raw_suite)"]
        V_GRAM["validate_grammys_raw<br/>(grammy_raw_suite)"]
    end

    subgraph Processing["4. Transformation, Integration & Harmonization"]
        TRANS["transform_and_integrate<br/>• Entity Resolution & String Normalization<br/>• Accent & Case Harmonization<br/>• Dimensional Modeling (Kimball)<br/>• Star Schema Generation"]
    end

    subgraph PreparedGate["5. Prepared Validation Gate (Great Expectations)"]
        V_PREP["validate_prepared<br/>(prepared_data_master_suite)<br/>• Referential Integrity<br/>• Primary Key Uniqueness<br/>• Domain Boundaries"]
    end

    subgraph Loading["6. Idempotent Target Load"]
        LOAD["load_dw<br/>• Atomic Transactional Reload<br/>• Zero-Duplicate Guarantee"]
    end

    subgraph TargetDW["7. Analytical Data Warehouse (music_dw)"]
        DT[("dim_time")]
        DC[("dim_award_category")]
        DG[("dim_genre")]
        DA[("dim_artist")]
        DTRK[("dim_track")]
        FT[("fact_track_performance")]
        FG[("fact_grammy_awards")]
    end

    subgraph Analytics["8. Analytics & Dashboards"]
        DASH["KPI Dashboard & Visualizations<br/>(Direct SQL on Data Warehouse)"]
    end

    S_CSV --> E_SPOT
    G_SRC --> E_GRAM

    E_SPOT --> V_SPOT
    E_GRAM --> V_GRAM

    V_SPOT -->|Critical Pass| TRANS
    V_GRAM -->|Critical Pass| TRANS
    V_SPOT -.->|Critical Fail| STOP1["HALT / ISOLATE"]
    V_GRAM -.->|Critical Fail| STOP2["HALT / ISOLATE"]

    TRANS --> V_PREP
    V_PREP -->|Pass| LOAD
    V_PREP -.->|Fail| STOP3["BLOCK DW LOAD"]

    LOAD --> TargetDW
    TargetDW --> Analytics
```

---

## 2. Core Architectural Principles

### Separation of Concerns
1. **Orchestration Logic (`dags/`):** Exposes task dependencies, execution flow, retry semantics, and DAG-level failure handling. It does NOT contain monolith business logic.
2. **Business & Quality Logic (`src/`):** Reusable, testable Python modules (`extract.py`, `validation.py`, `transform.py`, `load.py`).
3. **Data Quality Layer (`src/validation.py` & `gx/`):** Great Expectations suites enforce boundary conditions independently of pipeline flow.
4. **Relational Schemas (`sql/`):** Declarative SQL scripts (`source_setup.sql`, `dw_schema.sql`, `kpi_queries.sql`).

### Task Interfaces & Memory Hygiene
Tasks communicate solely by exchanging compact metadata objects (JSON dictionaries containing file paths, execution timestamps, row counts, and audit digests). Bulk DataFrames are never passed across the Airflow metadata database (XCom), guaranteeing high performance and horizontal scalability.

### Dual Validation Gate Pattern
- **Raw Validation Gate:** Verifies incoming source data safety *before* transformation logic touches it. Prevents malformed or toxic batches from entering compute cycles.
- **Prepared Validation Gate:** Verifies processed dimensions and facts *before* the Data Warehouse loader touches target storage. Ensures that schema invariants, foreign key referential integrity, and primary key uniqueness are strictly maintained.
