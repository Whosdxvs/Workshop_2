-- ==============================================================================
-- Dimensional Data Warehouse Schema (Star Schema)
-- Academic Program: Data Engineering & Artificial Intelligence (UAO)
-- Course: ETL (G01) - Workshop 2
-- Target Database: MySQL 8.0+ / PostgreSQL 15+
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. DIMENSION TABLES
-- ------------------------------------------------------------------------------

-- Dimension: Time / Award Calendar
CREATE TABLE IF NOT EXISTS dim_time (
    year INT PRIMARY KEY,
    decade VARCHAR(20) NOT NULL,
    era VARCHAR(50) NOT NULL
);

-- Dimension: Musical Genre
CREATE TABLE IF NOT EXISTS dim_genre (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name VARCHAR(100) NOT NULL UNIQUE
);

-- Dimension: Award Category
CREATE TABLE IF NOT EXISTS dim_award_category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL,
    category_group VARCHAR(100) NOT NULL,
    INDEX idx_dim_category_name (category_name)
);

-- Dimension: Artist
CREATE TABLE IF NOT EXISTS dim_artist (
    artist_id INT AUTO_INCREMENT PRIMARY KEY,
    artist_name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    is_grammy_winner BOOLEAN NOT NULL DEFAULT FALSE,
    total_grammy_wins INT NOT NULL DEFAULT 0,
    first_win_year INT NULL,
    last_win_year INT NULL,
    INDEX idx_dim_artist_name (artist_name),
    INDEX idx_dim_artist_norm (normalized_name),
    FOREIGN KEY (first_win_year) REFERENCES dim_time(year) ON DELETE SET NULL,
    FOREIGN KEY (last_win_year) REFERENCES dim_time(year) ON DELETE SET NULL
);

-- Dimension: Track
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

-- ------------------------------------------------------------------------------
-- 2. FACT TABLES
-- ------------------------------------------------------------------------------

-- Fact: Track Performance & Musical Attributes
-- Grain: One row per unique track and genre classification
CREATE TABLE IF NOT EXISTS fact_track_performance (
    fact_track_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    track_id VARCHAR(64) NOT NULL,
    artist_id INT NOT NULL,
    genre_id INT NOT NULL,
    popularity INT NOT NULL,
    duration_ms INT NOT NULL,
    danceability FLOAT NOT NULL,
    energy FLOAT NOT NULL,
    valence FLOAT NOT NULL,
    acousticness FLOAT NOT NULL,
    is_grammy_recognized BOOLEAN NOT NULL DEFAULT FALSE,
    batch_id VARCHAR(100) NOT NULL,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES dim_track(track_id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES dim_artist(artist_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES dim_genre(genre_id) ON DELETE CASCADE,
    INDEX idx_fact_track_artist (artist_id),
    INDEX idx_fact_track_genre (genre_id),
    INDEX idx_fact_track_popularity (popularity),
    INDEX idx_fact_track_grammy (is_grammy_recognized)
);

-- Fact: Grammy Awards Recognition
-- Grain: One row per Grammy nomination / winning event
CREATE TABLE IF NOT EXISTS fact_grammy_awards (
    fact_grammy_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    award_year INT NOT NULL,
    category_id INT NOT NULL,
    artist_id INT NULL,
    track_id VARCHAR(64) NULL,
    nominee_title VARCHAR(500) NOT NULL,
    is_winner BOOLEAN NOT NULL DEFAULT TRUE,
    is_spotify_matched BOOLEAN NOT NULL DEFAULT FALSE,
    batch_id VARCHAR(100) NOT NULL,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (award_year) REFERENCES dim_time(year) ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES dim_award_category(category_id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES dim_artist(artist_id) ON DELETE SET NULL,
    FOREIGN KEY (track_id) REFERENCES dim_track(track_id) ON DELETE SET NULL,
    INDEX idx_fact_grammy_year (award_year),
    INDEX idx_fact_grammy_artist (artist_id),
    INDEX idx_fact_grammy_category (category_id),
    INDEX idx_fact_grammy_matched (is_spotify_matched)
);
