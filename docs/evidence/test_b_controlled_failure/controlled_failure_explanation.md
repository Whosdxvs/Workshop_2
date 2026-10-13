# Test B: Controlled Critical Quality Failure Evidence

## Objective
Demonstrate that the raw validation gate anticipates, detects, and isolates severe data defects, halting downstream transformation before corrupting the analytical target.

## Injected Anomaly
- **Target Dataset:** Spotify Raw Catalog Batch
- **Attribute:** `danceability`
- **Injected Value:** `99.5` (Impossible physics/signal measurement; domain is $[0.0, 1.0]$)
- **Target Quality Rule:** `RULE-RAW-SPOTIFY-02`
- **Severity Level:** **Critical**

## Pipeline Behavior & Downstream Isolation
| Pipeline Stage | State | Action Taken |
| :--- | :--- | :--- |
| `extract_spotify` | **SUCCESS** | Extracted operational batch to staging. |
| `validate_spotify_raw` | **FAILED (Controlled)** | Great Expectations detected out-of-bounds records. Raised `QualityGateFailureError`. |
| `transform_and_integrate` | **BLOCKED (Not Run)** | Upstream dependency failed; task skipped/blocked. |
| `validate_prepared` | **BLOCKED (Not Run)** | Task blocked. |
| `load_dw` | **BLOCKED (Not Run)** | Task blocked; zero corrupted records loaded into Data Warehouse. |

## Actionable Failure Log
```
CRITICAL QUALITY FAILURE in Spotify Raw Gate! Violating rule: RULE-RAW-SPOTIFY-02. Pipeline execution blocked.
```

## Great Expectations Diagnostic Evidence
Validation report saved to: `docs/evidence/test_b_controlled_failure/gx_controlled_failure_report.json`
