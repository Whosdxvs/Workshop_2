# Failure Handling, Retries & Observability Policy

**Course:** ETL (G01) — Faculty of Engineering and Basic Sciences  
**Academic Program:** Data Engineering and Artificial Intelligence  
**Institution:** Universidad Autónoma de Occidente (UAO)  
**Project:** Workshop-2: Building a Reliable Batch Data Pipeline  

---

## 1. Engineering Principles

> **IMPORTANT:** A blanket policy such as `retries=3` everywhere is not evidence of reliability. Retries must be selectively applied to transient operational failures, while deterministic data quality failures must stop execution and surface actionable diagnostic evidence.

---

## 2. Failure Policy Register

| Condition / Event | Failure Class | Severity | Pipeline Response | Retry? | Retry Parameters | Technical Justification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Operational Source DB Connection Glitch** | Transient Operational | Operational High | Pause and retry query | **YES** | `retries=3`, `delay=15s`, exponential backoff | Network blips, connection pool saturation, or brief database restarts can resolve automatically without modifying code or input data. |
| **Target Data Warehouse Deadlock / Lock Wait** | Transient Operational | Operational Medium | Rollback transaction and retry batch load | **YES** | `retries=2`, `delay=15s`, fixed delay | Database lock contention is transient; retrying the atomic transaction after a short pause typically succeeds. |
| **Raw Schema Mismatch / Missing Required Column** | Deterministic Contract | Critical | Stop task, produce fatal log, halt downstream | **NO** | `retries=0` | Missing structural columns cannot be cured by repeating the same query on the same schema. Repetition merely wastes compute and delays alerting. |
| **Critical Raw Quality Failure (e.g. Out-of-bounds Audio or Invalid Year)** | Deterministic Data Quality | Critical | Halt validation task, generate diagnostic GX JSON, block transformation | **NO** | `retries=0` | Input data violates physical/domain rules. Repeating the validation will produce the exact same failure. Requires human review or upstream quarantine. |
| **Minor Missing Metadata (e.g. Single Null Artist / Album)** | Minor Data Defect | Warning | Log diagnostic warning; apply imputation | **NO** | `retries=0` | Handled deterministically in transformation via `fillna('Unknown Artist')` under documented tolerance threshold (&le; 0.01%). |
| **Prepared Validation Gate Failure (Referential Integrity Violation)** | Deterministic Invariant | Critical | Block `load_dw` task, preserve prepared files in staging | **NO** | `retries=0` | Loading corrupted foreign keys violates Data Warehouse referential integrity. Downstream analytical loading is strictly prevented. |

---

## 3. Observability and Logging Standards

Every Airflow task logs structured, actionable context answering the core observability questions:

1. **What ran?** DAG run ID, task identifier, input file paths, source table name.
2. **When?** UTC timestamps recorded at task start, extraction completion, validation completion, and commit.
3. **Did it succeed?** Boolean status, evaluated record count, validation percentage.
4. **Where did it fail?** Exact task name and line number, isolated downstream state (e.g. `transform_and_integrate: BLOCKED`).
5. **Why?** Specific Rule ID (`RULE-RAW-SPOTIFY-02`), violating column, observed value vs. expected interval, and link to machine-readable Great Expectations JSON report.
6. **What happened next?** Downstream dependency isolation, transaction rollback, and alert logging.
