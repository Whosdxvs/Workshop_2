-- Source Database Initialization Script
-- Scenario: Operational Relational Source for Grammy Awards Data
-- Course: ETL (UAO) - Workshop 2

CREATE DATABASE IF NOT EXISTS grammy_source_db;
USE grammy_source_db;

DROP TABLE IF EXISTS source_grammy_awards;

CREATE TABLE source_grammy_awards (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    year INT NOT NULL,
    title VARCHAR(500),
    published_at VARCHAR(100),
    updated_at VARCHAR(100),
    category VARCHAR(500) NOT NULL,
    nominee VARCHAR(1000),
    artist VARCHAR(1000),
    workers TEXT,
    img TEXT,
    winner BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_source_grammy_year ON source_grammy_awards(year);
CREATE INDEX idx_source_grammy_artist ON source_grammy_awards(artist(255));
CREATE INDEX idx_source_grammy_category ON source_grammy_awards(category(255));
