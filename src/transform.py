"""
Data Transformation and Integration Engine
Implements Section 6.8: Cleaning, Standardization, Harmonization,
Cross-Source Entity Resolution, and Dimensional Modeling.
Course: ETL (UAO) - Workshop 2
"""
import re
import json
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
from src.config import RAW_DATA_DIR, PREPARED_DATA_DIR, EVIDENCE_DIR

logger = logging.getLogger("transform")

import unicodedata

def normalize_text(text_val: str) -> str:
    """Strips accents, special characters, extra spaces, and lowercases for canonical matching."""
    if pd.isna(text_val):
        return "unknown"
    text_val = unicodedata.normalize("NFD", str(text_val))
    text_val = "".join(c for c in text_val if unicodedata.category(c) != "Mn")
    text_val = re.sub(r"[^\w\s]", " ", text_val)
    text_val = re.sub(r"\s+", " ", text_val).strip().lower()
    return text_val if text_val else "unknown"

def categorize_grammy_field(cat_name: str) -> str:
    """Classifies granular Grammy award categories into high-level analytical category groups."""
    c = str(cat_name).lower()
    if any(k in c for k in ["record of the year", "album of the year", "song of the year", "best new artist"]):
        return "General Field"
    elif "pop" in c:
        return "Pop"
    elif "rock" in c or "metal" in c or "alternative" in c:
        return "Rock & Alternative"
    elif "rap" in c or "hip-hop" in c or "hip hop" in c:
        return "Rap & Hip-Hop"
    elif "r&b" in c or "rhythm and blues" in c or "urban" in c:
        return "R&B / Soul"
    elif "country" in c or "bluegrass" in c or "americana" in c:
        return "Country & Roots"
    elif "jazz" in c:
        return "Jazz"
    elif "classical" in c or "opera" in c or "orchestral" in c:
        return "Classical"
    elif "latin" in c:
        return "Latin"
    elif "dance" in c or "electronic" in c:
        return "Dance & Electronic"
    else:
        return "Specialized & Craft"

def extract_artist_from_grammy_row(row) -> str:
    """
    Harmonizes missing artist values by extracting performer names
    from workers or nominee fields when artist column is null.
    """
    if pd.notna(row["artist"]) and str(row["artist"]).strip():
        return str(row["artist"]).strip()
    
    # Check workers e.g. "Taylor Swift, songwriter (Taylor Swift)"
    workers = str(row["workers"]) if pd.notna(row["workers"]) else ""
    if "(" in workers and ")" in workers:
        match = re.search(r"\(([^)]+)\)", workers)
        if match:
            return match.group(1).strip()
            
    # If nominee looks like an artist (e.g. Best New Artist categories)
    nominee = str(row["nominee"]) if pd.notna(row["nominee"]) else ""
    return nominee.strip() if nominee else "Unknown Artist"

def transform_and_integrate(
    spotify_raw_file: Path = None,
    grammy_raw_file: Path = None,
    output_dir: Path = PREPARED_DATA_DIR,
    batch_id: str = None
) -> dict:
    """
    Executes full transformation and cross-source integration.
    Produces dimensional star schema datasets ready for validation and DW loading.
    """
    batch_id = batch_id or f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    spot_file = spotify_raw_file or (RAW_DATA_DIR / "spotify_raw.csv")
    gram_file = grammy_raw_file or (RAW_DATA_DIR / "grammy_raw.csv")

    logger.info(f"Starting transformation. Spotify: {spot_file}, Grammy: {gram_file}")
    df_spot = pd.read_csv(spot_file)
    df_gram = pd.read_csv(gram_file)

    initial_spotify_rows = len(df_spot)
    initial_grammy_rows = len(df_gram)

    # ---------------------------------------------------------
    # 1. SPOTIFY CLEANING & STANDARDIZATION
    # ---------------------------------------------------------
    # Impute missing string fields
    df_spot["artists"] = df_spot["artists"].fillna("Unknown Artist").astype(str).str.strip()
    df_spot["album_name"] = df_spot["album_name"].fillna("Unknown Album").astype(str).str.strip()
    df_spot["track_name"] = df_spot["track_name"].fillna("Unknown Track").astype(str).str.strip()

    # Duration normalization: drop or filter invalid durations <= 0
    df_spot = df_spot[df_spot["duration_ms"] > 0].copy()
    df_spot["duration_min"] = (df_spot["duration_ms"] / 60000.0).round(2)
    df_spot["explicit"] = df_spot["explicit"].astype(bool)

    # Clean text columns for integration
    df_spot["primary_artist"] = df_spot["artists"].apply(lambda a: a.split(";")[0].strip())
    df_spot["norm_artist"] = df_spot["primary_artist"].apply(normalize_text)
    df_spot["norm_track"] = df_spot["track_name"].apply(normalize_text)

    # ---------------------------------------------------------
    # 2. GRAMMY CLEANING & STANDARDIZATION
    # ---------------------------------------------------------
    df_gram["effective_artist"] = df_gram.apply(extract_artist_from_grammy_row, axis=1)
    df_gram["nominee_title"] = df_gram["nominee"].fillna("Unknown Nominee").astype(str).str.strip()
    df_gram["winner"] = df_gram["winner"].astype(bool)
    df_gram["category"] = df_gram["category"].astype(str).str.strip()
    df_gram["category_group"] = df_gram["category"].apply(categorize_grammy_field)

    df_gram["norm_artist"] = df_gram["effective_artist"].apply(normalize_text)
    df_gram["norm_track"] = df_gram["nominee_title"].apply(normalize_text)

    # ---------------------------------------------------------
    # 3. DIMENSION 1: dim_time
    # ---------------------------------------------------------
    min_year = int(min(df_gram["year"].min(), 1958))
    max_year = int(max(df_gram["year"].max(), 2026))
    time_rows = []
    for y in range(min_year, max_year + 1):
        decade = f"{(y // 10) * 10}s"
        if y < 1980:
            era = "Golden Vinyl Era (1958-1979)"
        elif y < 2000:
            era = "Cassette & CD Era (1980-1999)"
        else:
            era = "Digital & Streaming Era (2000-Present)"
        time_rows.append({"year": y, "decade": decade, "era": era})
    dim_time = pd.DataFrame(time_rows)

    # ---------------------------------------------------------
    # 4. DIMENSION 2: dim_award_category (Case-Harmonized)
    # ---------------------------------------------------------
    df_gram["norm_cat"] = df_gram["category"].apply(normalize_text)
    # Group by lowercase category to eliminate spelling/case duplicates like 'OR' vs 'Or'
    canonical_cats = (
        df_gram.groupby("norm_cat")
        .agg(
            category_name=("category", "first"),
            category_group=("category_group", "first")
        )
        .reset_index()
        .sort_values("category_name")
        .reset_index(drop=True)
    )
    canonical_cats["category_id"] = range(1, len(canonical_cats) + 1)
    dim_award_category = canonical_cats[["category_id", "category_name", "category_group"]]

    cat_map = dict(zip(canonical_cats["norm_cat"], canonical_cats["category_id"]))

    # ---------------------------------------------------------
    # 5. DIMENSION 3: dim_genre
    # ---------------------------------------------------------
    unique_genres = pd.DataFrame({"genre_name": sorted(df_spot["track_genre"].unique())})
    unique_genres["genre_id"] = range(1, len(unique_genres) + 1)
    dim_genre = unique_genres[["genre_id", "genre_name"]]
    genre_map = dict(zip(dim_genre["genre_name"], dim_genre["genre_id"]))

    # ---------------------------------------------------------
    # 6. DIMENSION 4: dim_artist & CROSS-SOURCE AGGREGATION (Case-Harmonized)
    # ---------------------------------------------------------
    # Aggregate Grammy recognition per normalized artist
    grammy_winners = df_gram[df_gram["winner"] == True]
    artist_wins = grammy_winners.groupby("norm_artist").agg(
        total_wins=("winner", "count"),
        first_win=("year", "min"),
        last_win=("year", "max")
    ).reset_index()
    artist_wins_map = artist_wins.set_index("norm_artist").to_dict("index")

    # Collect distinct artists across Spotify and Grammy with canonical casing
    all_artists_df = pd.concat([
        pd.DataFrame({"raw_name": ["Unknown Artist"], "norm_name": ["unknown"]}),
        pd.DataFrame({"raw_name": df_spot["primary_artist"], "norm_name": df_spot["norm_artist"]}),
        pd.DataFrame({"raw_name": df_gram["effective_artist"], "norm_name": df_gram["norm_artist"]})
    ]).drop_duplicates(subset=["raw_name"])

    # Harmonize case by grouping on normalized name
    canonical_artists = (
        all_artists_df.groupby("norm_name")
        .agg(artist_name=("raw_name", "first"))
        .reset_index()
        .sort_values("artist_name")
        .reset_index(drop=True)
    )
    canonical_artists["artist_id"] = range(1, len(canonical_artists) + 1)

    artist_records = []
    for _, row in canonical_artists.iterrows():
        norm_a = str(row["norm_name"])[:250].strip()
        a_id = int(row["artist_id"])
        a_name = str(row["artist_name"])[:250].strip()
        g_info = artist_wins_map.get(row["norm_name"])
        is_winner = bool(g_info)
        tot_wins = int(g_info["total_wins"]) if g_info else 0
        first_yr = int(g_info["first_win"]) if g_info else None
        last_yr = int(g_info["last_win"]) if g_info else None

        artist_records.append({
            "artist_id": a_id,
            "artist_name": a_name,
            "normalized_name": norm_a,
            "is_grammy_winner": is_winner,
            "total_grammy_wins": tot_wins,
            "first_win_year": first_yr,
            "last_win_year": last_yr
        })
    dim_artist = pd.DataFrame(artist_records).drop_duplicates(subset=["artist_name"]).drop_duplicates(subset=["normalized_name"])
    # Re-index artist_id to be cleanly contiguous
    dim_artist["artist_id"] = range(1, len(dim_artist) + 1)
    norm_artist_id_map = dict(zip(dim_artist["normalized_name"], dim_artist["artist_id"]))
    unknown_artist_id = norm_artist_id_map.get("unknown", 1)

    # ---------------------------------------------------------
    # 7. DIMENSION 5: dim_track
    # ---------------------------------------------------------
    # Deduplicate tracks by track_id
    track_dedup = df_spot.drop_duplicates(subset=["track_id"]).copy()
    dim_track = pd.DataFrame({
        "track_id": track_dedup["track_id"],
        "track_name": track_dedup["track_name"].str.slice(0, 500),
        "album_name": track_dedup["album_name"].str.slice(0, 500),
        "explicit": track_dedup["explicit"],
        "duration_ms": track_dedup["duration_ms"],
        "duration_min": track_dedup["duration_min"],
        "danceability": track_dedup["danceability"],
        "energy": track_dedup["energy"],
        "key_signature": track_dedup["key"],
        "loudness": track_dedup["loudness"],
        "mode_flag": track_dedup["mode"],
        "speechiness": track_dedup["speechiness"],
        "acousticness": track_dedup["acousticness"],
        "instrumentalness": track_dedup["instrumentalness"],
        "liveness": track_dedup["liveness"],
        "valence": track_dedup["valence"],
        "tempo": track_dedup["tempo"],
        "time_signature": track_dedup["time_signature"]
    })

    # Track title to track_id map for Grammy integration
    track_id_by_norm_title = dict(zip(track_dedup["norm_track"], track_dedup["track_id"]))

    # ---------------------------------------------------------
    # 8. FACT 1: fact_track_performance
    # ---------------------------------------------------------
    mapped_artist_ids = df_spot["norm_artist"].map(norm_artist_id_map).fillna(unknown_artist_id).astype(int)
    fact_track = pd.DataFrame({
        "track_id": df_spot["track_id"],
        "artist_id": mapped_artist_ids,
        "genre_id": df_spot["track_genre"].map(genre_map).astype(int),
        "popularity": df_spot["popularity"],
        "duration_ms": df_spot["duration_ms"],
        "danceability": df_spot["danceability"],
        "energy": df_spot["energy"],
        "valence": df_spot["valence"],
        "acousticness": df_spot["acousticness"],
        "is_grammy_recognized": df_spot["norm_artist"].isin(artist_wins_map),
        "batch_id": batch_id,
        "loaded_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })
    fact_track["fact_track_id"] = range(1, len(fact_track) + 1)
    # Order columns
    fact_track = fact_track[[
        "fact_track_id", "track_id", "artist_id", "genre_id",
        "popularity", "duration_ms", "danceability", "energy",
        "valence", "acousticness", "is_grammy_recognized", "batch_id", "loaded_at"
    ]]

    # ---------------------------------------------------------
    # 9. FACT 2: fact_grammy_awards
    # ---------------------------------------------------------
    fact_grammy = pd.DataFrame({
        "award_year": df_gram["year"],
        "category_id": df_gram["norm_cat"].map(cat_map),
        "artist_id": df_gram["norm_artist"].map(norm_artist_id_map),
        "track_id": df_gram["norm_track"].map(track_id_by_norm_title),
        "nominee_title": df_gram["nominee_title"],
        "is_winner": df_gram["winner"],
        "batch_id": batch_id,
        "loaded_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })
    fact_grammy["is_spotify_matched"] = fact_grammy["artist_id"].notna() | fact_grammy["track_id"].notna()
    fact_grammy["fact_grammy_id"] = range(1, len(fact_grammy) + 1)
    fact_grammy = fact_grammy[[
        "fact_grammy_id", "award_year", "category_id", "artist_id", "track_id",
        "nominee_title", "is_winner", "is_spotify_matched", "batch_id", "loaded_at"
    ]]

    # ---------------------------------------------------------
    # 10. SAVE PREPARED DATASETS
    # ---------------------------------------------------------
    output_dir.mkdir(parents=True, exist_ok=True)
    dim_time.to_csv(output_dir / "dim_time.csv", index=False)
    dim_award_category.to_csv(output_dir / "dim_award_category.csv", index=False)
    dim_genre.to_csv(output_dir / "dim_genre.csv", index=False)
    dim_artist.to_csv(output_dir / "dim_artist.csv", index=False)
    dim_track.to_csv(output_dir / "dim_track.csv", index=False)
    fact_track.to_csv(output_dir / "fact_track_performance.csv", index=False)
    fact_grammy.to_csv(output_dir / "fact_grammy_awards.csv", index=False)

    # ---------------------------------------------------------
    # 11. RECORD INTEGRATION RECONCILIATION EVIDENCE
    # ---------------------------------------------------------
    reconciliation = {
        "batch_id": batch_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_spotify_rows": initial_spotify_rows,
        "input_grammy_rows": initial_grammy_rows,
        "clean_spotify_rows": len(df_spot),
        "clean_grammy_rows": len(df_gram),
        "prepared_counts": {
            "dim_time": len(dim_time),
            "dim_award_category": len(dim_award_category),
            "dim_genre": len(dim_genre),
            "dim_artist": len(dim_artist),
            "dim_track": len(dim_track),
            "fact_track_performance": len(fact_track),
            "fact_grammy_awards": len(fact_grammy)
        },
        "integration_metrics": {
            "spotify_tracks_with_grammy_artist": int(fact_track["is_grammy_recognized"].sum()),
            "spotify_tracks_grammy_percentage": round(float(fact_track["is_grammy_recognized"].mean()) * 100, 2),
            "grammy_awards_matched_to_spotify": int(fact_grammy["is_spotify_matched"].sum()),
            "grammy_match_percentage": round(float(fact_grammy["is_spotify_matched"].mean()) * 100, 2)
        }
    }

    recon_file = EVIDENCE_DIR / "integration_reconciliation.json"
    with open(recon_file, "w", encoding="utf-8") as f:
        json.dump(reconciliation, f, indent=2)

    logger.info(f"Transformation complete. Reconciliation written to: {recon_file}")
    return reconciliation

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    res = transform_and_integrate()
    print("Transformation Reconciliation:\n", json.dumps(res, indent=2))
