-- ==============================================================================
-- Analytical Data Warehouse KPI Queries
-- Academic Program: Data Engineering & Artificial Intelligence (UAO)
-- Course: ETL (G01) - Workshop 2
-- All queries query the dimensional Data Warehouse (music_dw)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- REQ-01: GRAMMY POPULARITY PREMIUM & AUDIO SIGNATURE BY GENRE
-- Objective: Evaluate whether Grammy-recognized tracks hold a popularity advantage
-- and demonstrate distinct acoustic/energy characteristics across genres.
-- ------------------------------------------------------------------------------
SELECT 
    g.genre_name,
    COUNT(f.fact_track_id) AS total_genre_tracks,
    COUNT(CASE WHEN f.is_grammy_recognized = 1 THEN 1 END) AS grammy_recognized_tracks,
    ROUND(AVG(CASE WHEN f.is_grammy_recognized = 1 THEN f.popularity ELSE NULL END), 2) AS avg_pop_grammy,
    ROUND(AVG(CASE WHEN f.is_grammy_recognized = 0 THEN f.popularity ELSE NULL END), 2) AS avg_pop_non_grammy,
    ROUND(AVG(CASE WHEN f.is_grammy_recognized = 1 THEN f.popularity ELSE NULL END) - 
          AVG(CASE WHEN f.is_grammy_recognized = 0 THEN f.popularity ELSE NULL END), 2) AS grammy_popularity_premium,
    ROUND(AVG(CASE WHEN f.is_grammy_recognized = 1 THEN f.danceability ELSE NULL END), 3) AS avg_danceability_grammy,
    ROUND(AVG(CASE WHEN f.is_grammy_recognized = 0 THEN f.danceability ELSE NULL END), 3) AS avg_danceability_non_grammy,
    ROUND(AVG(CASE WHEN f.is_grammy_recognized = 1 THEN f.energy ELSE NULL END), 3) AS avg_energy_grammy,
    ROUND(AVG(CASE WHEN f.is_grammy_recognized = 0 THEN f.energy ELSE NULL END), 3) AS avg_energy_non_grammy
FROM fact_track_performance f
JOIN dim_genre g ON f.genre_id = g.genre_id
GROUP BY g.genre_name
HAVING COUNT(CASE WHEN f.is_grammy_recognized = 1 THEN 1 END) >= 15
ORDER BY grammy_popularity_premium DESC;

-- ------------------------------------------------------------------------------
-- REQ-02: ARTIST CAREER RECOGNITION TIER VS. CATALOG POPULARITY
-- Objective: Correlate cumulative Grammy recognition with commercial track reach
-- and explicit content distribution in the streaming catalog.
-- ------------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN a.total_grammy_wins >= 3 THEN 'Elite (3+ Grammy Wins)'
        WHEN a.total_grammy_wins >= 1 THEN 'Recognized (1-2 Wins)'
        ELSE 'Unawarded / Emerging'
    END AS artist_recognition_tier,
    COUNT(DISTINCT a.artist_id) AS unique_artists,
    COUNT(f.fact_track_id) AS total_catalog_tracks,
    ROUND(AVG(f.popularity), 2) AS avg_track_popularity,
    ROUND(AVG(f.danceability), 3) AS avg_danceability,
    ROUND(AVG(f.energy), 3) AS avg_energy,
    ROUND(AVG(f.acousticness), 3) AS avg_acousticness,
    ROUND(SUM(CASE WHEN t.explicit = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(f.fact_track_id), 2) AS explicit_percentage
FROM fact_track_performance f
JOIN dim_artist a ON f.artist_id = a.artist_id
JOIN dim_track t ON f.track_id = t.track_id
GROUP BY artist_recognition_tier
ORDER BY avg_track_popularity DESC;

-- ------------------------------------------------------------------------------
-- REQ-03: TEMPORAL EVOLUTION OF AWARD TAXONOMY & MUSICAL MOOD
-- Objective: Trace historical shift across eras in Grammy category groups and
-- audio characteristics (valence & energy).
-- ------------------------------------------------------------------------------
SELECT 
    t.era,
    c.category_group,
    COUNT(g.fact_grammy_id) AS total_awards,
    SUM(CASE WHEN g.is_spotify_matched = 1 THEN 1 ELSE 0 END) AS spotify_matched_awards,
    ROUND(SUM(CASE WHEN g.is_spotify_matched = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(g.fact_grammy_id), 1) AS match_coverage_pct,
    ROUND(AVG(trk.valence), 3) AS avg_track_valence,
    ROUND(AVG(trk.energy), 3) AS avg_track_energy,
    ROUND(AVG(trk.danceability), 3) AS avg_track_danceability
FROM fact_grammy_awards g
JOIN dim_time t ON g.award_year = t.year
JOIN dim_award_category c ON g.category_id = c.category_id
LEFT JOIN dim_track trk ON g.track_id = trk.track_id
GROUP BY t.era, c.category_group
ORDER BY t.era, total_awards DESC;
