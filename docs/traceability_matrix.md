# End-to-End Traceability Matrix

**Course:** ETL (G01) — Faculty of Engineering and Basic Sciences  
**Academic Program:** Data Engineering and Artificial Intelligence  
**Institution:** Universidad Autónoma de Occidente (UAO)  
**Project:** Workshop-2: Building a Reliable Batch Data Pipeline  

---

## Traceability Chain Definition

Every implementation decision follows an unbroken reasoning chain:
$$\text{Analytical Requirement} \longrightarrow \text{Required Data} \longrightarrow \text{Quality Risk} \longrightarrow \text{DQ Rule} \longrightarrow \text{GX Check} \longrightarrow \text{Transformation} \longrightarrow \text{DW Element} \longrightarrow \text{KPI / Dashboard}$$

---

## Traceability Matrix

| Requirement | Required Data | Quality Risk | DQ Rule | GX Expectation | Transformation | DW Element | KPI / Visualization |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-01:** Grammy Popularity Premium & Audio Profile | Spotify: `popularity`, `danceability`, `energy`, `track_genre`; Grammy: `artist`, `winner`. | Out-of-bounds audio scores or unlinked artists corrupt comparative averages. | **RULE-RAW-SPOTIFY-02**, **RULE-RAW-SPOTIFY-03** | `ExpectColumnValuesToBeBetween(0.0, 1.0)` on audio metrics. | Tokenize artists; normalize names; match performers across sources; flag `is_grammy_recognized`. | `fact_track_performance`, `dim_genre` | **KPI 1:** Grammy Popularity Premium by Genre (`kpi_1_grammy_popularity_premium.png`) |
| **REQ-02:** Artist Career Recognition Tier vs. Catalog Reach | Spotify: `primary_artist`, `popularity`, `explicit`; Grammy: historical `year`, `artist`, `winner`. | Diacritic/accent discrepancies create duplicate artist records (`André Previn` vs `Andre Previn`). | **RULE-PREPARED-02**, **RULE-RAW-SPOTIFY-07** | `ExpectColumnValuesToBeUnique(artist_id)` on `dim_artist`. | Unicode NFD normalization; strip accents; aggregate career wins; assign tiers (Elite 3+, Recognized 1-2, Emerging). | `dim_artist`, `dim_track`, `fact_track_performance` | **KPI 2:** Average Popularity & Audio Metrics by Artist Tier (`kpi_2_artist_tier_popularity.png`) |
| **REQ-03:** Historical Eras & Award Taxonomy Shift | Grammy: `year`, `category`, `nominee`; Spotify: `valence`, `energy`, `danceability`. | Invalid future years or missing award categories invalidate temporal era groupings. | **RULE-RAW-GRAMMY-01**, **RULE-RAW-GRAMMY-02** | `ExpectColumnValuesToBeBetween(1958, 2026)`, `ExpectColumnValuesToNotBeNull(category)` | Classify into 3 historical eras; harmonize 630 categories into 10 standard category groups. | `dim_time`, `dim_award_category`, `fact_grammy_awards` | **KPI 3:** Era-to-Era Award Taxonomy & Mood Trends (`kpi_3_temporal_era_taxonomy.png`) |
