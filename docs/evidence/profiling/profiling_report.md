# Data Profiling Summary Report

## 1. Structural Overview
| Metric | Spotify Dataset | Grammy Dataset |
| :--- | :--- | :--- |
| **Row Count** | 114,000 | 4,810 |
| **Column Count** | 21 | 10 |
| **Primary Grain** | Track by Genre `(track_id, track_genre)` | Nomination Event `(year, category, nominee)` |
| **Unique Track IDs / Entities** | 89,741 unique tracks | 4,131 unique nominees |

## 2. Completeness & Data Quality Risks
| Dataset | Column | Null Count | Null Rate (%) | Quality Risk & Engineering Treatment |
| :--- | :--- | :--- | :--- | :--- |
| **Spotify** | `artists` | 1 | 0.0009% | Missing artist metadata; impute with 'Unknown Artist' in cleaning phase. |
| **Spotify** | `album_name` | 1 | 0.0009% | Missing album title; impute with 'Unknown Album'. |
| **Spotify** | `track_name` | 1 | 0.0009% | Missing track title; impute with 'Unknown Track'. |
| **Grammy** | `artist` | 1840 | 38.25% | Expected in craft/songwriting categories where artist is in `workers` or `nominee`. Resolved via multi-field entity extraction. |
| **Grammy** | `workers` | 2190 | 45.53% | Expected for performer-only categories. |
| **Grammy** | `nominee` | 6 | 0.12% | Unnamed category entry; handled via fallback to title or quarantine. |

## 3. Cross-Source Entity Overlap
- **Unique Spotify Artists (tokenized):** 29,811
- **Unique Grammy Artists:** 1,656
- **Matched Artists:** 524 (31.64% of Grammy artists found in Spotify catalog)
- **Direct Track/Nominee Matches:** 706 tracks
