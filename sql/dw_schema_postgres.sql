-- ==============================================================================
-- Dimensional Data Warehouse Schema (PostgreSQL Dialect)
-- Academic Program: Data Engineering & Artificial Intelligence (UAO)
-- Course: ETL (G01) - Workshop 2
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS data_warehouse;
SET search_path TO data_warehouse, public;

CREATE TABLE IF NOT EXISTS dim_time (
    year INT PRIMARY KEY,
    decade VARCHAR(20) NOT NULL,
    era VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_genre (
    genre_id SERIAL PRIMARY KEY,
    genre_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_award_category (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL,
    category_group VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_artist (
    artist_id SERIAL PRIMARY KEY,
    artist_name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    is_grammy_winner BOOLEAN NOT NULL DEFAULT FALSE,
    total_grammy_wins INT NOT NULL DEFAULT 0,
    first_win_year INT NULL REFERENCES dim_time(year) ON DELETE SET NULL,
    last_win_year INT NULL REFERENCES dim_time(year) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS dim_track (
    track_id VARCHAR(64) PRIMARY KEY,
    track_name TEXT NOT NULL,
    album_name TEXT NULL,
    explicit BOOLEAN NOT NULL DEFAULT FALSE,
    duration_ms INT NOT NULL,
    duration_min FLOAT NOT NULL,
    danceability FLOAT NOT NULL,
    energy FLOAT NOT NULL,
    key_signature INT NOT NULL,
    loudness FLOAT NOT NULL,
    mode_flag INT NOT NULL,
    speechiness FLOAT NOT NULL,
    acousticness FLOAT NOT NULL,
    instrumentalness FLOAT NOT NULL,
    liveness FLOAT NOT NULL,
    valence FLOAT NOT NULL,
    tempo FLOAT NOT NULL,
    time_signature INT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_track_performance (
    fact_track_id BIGSERIAL PRIMARY KEY,
    track_id VARCHAR(64) NOT NULL REFERENCES dim_track(track_id) ON DELETE CASCADE,
    artist_id INT NOT NULL REFERENCES dim_artist(artist_id) ON DELETE CASCADE,
    genre_id INT NOT NULL REFERENCES dim_genre(genre_id) ON DELETE CASCADE,
    popularity INT NOT NULL,
    duration_ms INT NOT NULL,
    danceability FLOAT NOT NULL,
    energy FLOAT NOT NULL,
    valence FLOAT NOT NULL,
    acousticness FLOAT NOT NULL,
    is_grammy_recognized BOOLEAN NOT NULL DEFAULT FALSE,
    batch_id VARCHAR(100) NOT NULL,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fact_track_artist ON fact_track_performance(artist_id);
CREATE INDEX IF NOT EXISTS idx_fact_track_genre ON fact_track_performance(genre_id);
CREATE INDEX IF NOT EXISTS idx_fact_track_popularity ON fact_track_performance(popularity);
CREATE INDEX IF NOT EXISTS idx_fact_track_grammy ON fact_track_performance(is_grammy_recognized);

CREATE TABLE IF NOT EXISTS fact_grammy_awards (
    fact_grammy_id BIGSERIAL PRIMARY KEY,
    award_year INT NOT NULL REFERENCES dim_time(year) ON DELETE RESTRICT,
    category_id INT NOT NULL REFERENCES dim_award_category(category_id) ON DELETE CASCADE,
    artist_id INT NULL REFERENCES dim_artist(artist_id) ON DELETE SET NULL,
    track_id VARCHAR(64) NULL REFERENCES dim_track(track_id) ON DELETE SET NULL,
    nominee_title VARCHAR(500) NOT NULL,
    is_winner BOOLEAN NOT NULL DEFAULT TRUE,
    is_spotify_matched BOOLEAN NOT NULL DEFAULT FALSE,
    batch_id VARCHAR(100) NOT NULL,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fact_grammy_year ON fact_grammy_awards(award_year);
CREATE INDEX IF NOT EXISTS idx_fact_grammy_artist ON fact_grammy_awards(artist_id);
CREATE INDEX IF NOT EXISTS idx_fact_grammy_category ON fact_grammy_awards(category_id);
CREATE INDEX IF NOT EXISTS idx_fact_grammy_matched ON fact_grammy_awards(is_spotify_matched);
