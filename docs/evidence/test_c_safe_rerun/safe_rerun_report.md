# Test C: Repeatability and Safe Rerun Evidence

## Engineering Principle
> **A rerun must not silently corrupt the analytical target.**

## Safe Rerun Strategy
- **Approach:** Transactional Idempotent Reload with Foreign Key Constraint Management.
- **Guarantee:** Full ACID transaction isolation. In case of mid-run failures, the transaction rolls back cleanly without partial corruption. When rerun with identical batches, zero duplicate rows are created.

## Row Count Verification Before vs. After Rerun
| Table Name | Count Before Rerun | Count After Rerun | Net Change (Duplicates) | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| `dim_time` | 69 | 69 | 0 | **PASSED (0 Duplicates)** |
| `dim_award_category` | 584 | 584 | 0 | **PASSED (0 Duplicates)** |
| `dim_genre` | 114 | 114 | 0 | **PASSED (0 Duplicates)** |
| `dim_artist` | 19,699 | 19,699 | 0 | **PASSED (0 Duplicates)** |
| `dim_track` | 89,740 | 89,740 | 0 | **PASSED (0 Duplicates)** |
| `fact_track_performance` | 113,999 | 113,999 | 0 | **PASSED (0 Duplicates)** |
| `fact_grammy_awards` | 4,810 | 4,810 | 0 | **PASSED (0 Duplicates)** |

## Key Measures Verification Before vs. After Rerun
| Measure / Metric | Value Before Rerun | Value After Rerun | Consistency |
| :--- | :--- | :--- | :--- |
| **Track Catalog Count** | 113,999 | 113,999 | **IDENTICAL** |
| **Average Popularity** | 33.2388 | 33.2388 | **IDENTICAL** |
| **Average Danceability** | 0.5668 | 0.5668 | **IDENTICAL** |
| **Grammy Recognized Tracks** | 10,174 | 10,174 | **IDENTICAL** |
| **Total Grammy Awards** | 4,810 | 4,810 | **IDENTICAL** |

## Conclusion
The rerun demonstration conclusively satisfies Section 7.3. Rerunning identical or subsequent batches maintains data warehouse integrity with mathematical consistency.
