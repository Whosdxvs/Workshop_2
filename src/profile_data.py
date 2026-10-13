"""
Data Profiling and Evidence Generation Script
Fulfills Section 6.3 requirements: Structure, Completeness, Uniqueness,
Categorical, Numerical, Temporal, and Cross-source Consistency.
Course: ETL (UAO) - Workshop 2
"""
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import SPOTIFY_CSV_PATH, GRAMMY_CSV_PATH, EVIDENCE_DIR

# Set plotting style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({"font.size": 10, "figure.autolayout": True})

PROFILING_DIR = EVIDENCE_DIR / "profiling"
PROFILING_DIR.mkdir(parents=True, exist_ok=True)

def run_profiling():
    print("Loading Spotify dataset...")
    df_spotify = pd.read_csv(SPOTIFY_CSV_PATH)
    print("Loading Grammy dataset...")
    df_grammy = pd.read_csv(GRAMMY_CSV_PATH)

    results = {}

    # ---------------------------------------------------------
    # 1. STRUCTURE
    # ---------------------------------------------------------
    results["structure"] = {
        "spotify": {
            "row_count": len(df_spotify),
            "column_count": len(df_spotify.columns),
            "columns": list(df_spotify.columns),
            "dtypes": {c: str(d) for c, d in df_spotify.dtypes.items()}
        },
        "grammy": {
            "row_count": len(df_grammy),
            "column_count": len(df_grammy.columns),
            "columns": list(df_grammy.columns),
            "dtypes": {c: str(d) for c, d in df_grammy.dtypes.items()}
        }
    }

    # ---------------------------------------------------------
    # 2. COMPLETENESS
    # ---------------------------------------------------------
    spot_nulls = df_spotify.isnull().sum()
    gram_nulls = df_grammy.isnull().sum()

    results["completeness"] = {
        "spotify_null_counts": spot_nulls[spot_nulls > 0].to_dict(),
        "spotify_null_pct": (spot_nulls[spot_nulls > 0] / len(df_spotify) * 100).to_dict(),
        "grammy_null_counts": gram_nulls[gram_nulls > 0].to_dict(),
        "grammy_null_pct": (gram_nulls[gram_nulls > 0] / len(df_grammy) * 100).to_dict()
    }

    # Plot Completeness
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    gram_null_pct = (gram_nulls / len(df_grammy) * 100).sort_values(ascending=False)
    sns.barplot(x=gram_null_pct.values, y=gram_null_pct.index, ax=axes[0], palette="Reds_r")
    axes[0].set_title("Grammy Dataset: Missing Value Rate (%)")
    axes[0].set_xlabel("Percentage (%)")

    spot_null_subset = (spot_nulls[spot_nulls > 0] / len(df_spotify) * 100)
    if not spot_null_subset.empty:
        sns.barplot(x=spot_null_subset.values, y=spot_null_subset.index, ax=axes[1], palette="Blues_r")
        axes[1].set_title("Spotify Dataset: Columns with Nulls (%)")
        axes[1].set_xlabel("Percentage (%)")
    else:
        axes[1].text(0.5, 0.5, "No missing values found", ha="center")
    plt.tight_layout()
    fig.savefig(PROFILING_DIR / "completeness_analysis.png", dpi=200)
    plt.close()

    # ---------------------------------------------------------
    # 3. UNIQUENESS AND DUPLICATION
    # ---------------------------------------------------------
    spot_track_uniq = df_spotify["track_id"].nunique()
    spot_dups = len(df_spotify) - spot_track_uniq
    results["uniqueness"] = {
        "spotify_unique_track_ids": spot_track_uniq,
        "spotify_duplicate_track_id_rows": spot_dups,
        "spotify_primary_candidate": "track_id, track_genre composite key",
        "grammy_total_rows": len(df_grammy),
        "grammy_unique_nominees": df_grammy["nominee"].nunique()
    }

    # ---------------------------------------------------------
    # 4. NUMERICAL CONTENT
    # ---------------------------------------------------------
    num_cols = ["popularity", "duration_ms", "danceability", "energy", "loudness", "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo"]
    num_summary = df_spotify[num_cols].describe().to_dict()
    results["numerical"] = num_summary

    # Plot Numerical distributions
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()
    features_to_plot = ["popularity", "danceability", "energy", "valence", "acousticness", "tempo"]
    for i, col in enumerate(features_to_plot):
        sns.histplot(df_spotify[col].dropna(), bins=30, kde=True, ax=axes[i], color="#1DB954")
        axes[i].set_title(f"Spotify: {col} Distribution")
    plt.tight_layout()
    fig.savefig(PROFILING_DIR / "numerical_distributions.png", dpi=200)
    plt.close()

    # ---------------------------------------------------------
    # 5. TEMPORAL CONTENT
    # ---------------------------------------------------------
    grammy_year_counts = df_grammy["year"].value_counts().sort_index()
    results["temporal"] = {
        "grammy_min_year": int(df_grammy["year"].min()),
        "grammy_max_year": int(df_grammy["year"].max()),
        "grammy_total_years": int(df_grammy["year"].nunique())
    }

    fig, ax = plt.subplots(figsize=(10, 4))
    grammy_year_counts.plot(kind="bar", ax=ax, color="#4A154B", width=0.8)
    # Thin x-axis labels
    ax.set_xticks(range(0, len(grammy_year_counts), 5))
    ax.set_xticklabels(grammy_year_counts.index[::5], rotation=45)
    ax.set_title("Grammy Awards Count per Year (1958 - 2019)")
    ax.set_xlabel("Award Year")
    ax.set_ylabel("Awards Conferred")
    plt.tight_layout()
    fig.savefig(PROFILING_DIR / "temporal_coverage.png", dpi=200)
    plt.close()

    # ---------------------------------------------------------
    # 6. CATEGORICAL & CROSS-SOURCE CONSISTENCY
    # ---------------------------------------------------------
    spotify_artists = set()
    for a in df_spotify["artists"].dropna().unique():
        for sub in str(a).split(";"):
            spotify_artists.add(sub.strip().lower())

    grammy_artists = set(df_grammy["artist"].dropna().str.lower().str.strip().unique())
    grammy_nominees = set(df_grammy["nominee"].dropna().str.lower().str.strip().unique())
    spotify_tracks = set(df_spotify["track_name"].dropna().str.lower().str.strip().unique())

    matched_artists = spotify_artists.intersection(grammy_artists)
    matched_tracks = spotify_tracks.intersection(grammy_nominees)

    results["cross_source"] = {
        "unique_spotify_artists_tokenized": len(spotify_artists),
        "unique_grammy_artists": len(grammy_artists),
        "matched_artists_count": len(matched_artists),
        "artist_match_percentage": round(len(matched_artists) / len(grammy_artists) * 100, 2),
        "unique_spotify_tracks": len(spotify_tracks),
        "unique_grammy_nominees": len(grammy_nominees),
        "matched_tracks_count": len(matched_tracks)
    }

    fig, ax = plt.subplots(figsize=(8, 4))
    categories = ["Grammy Artists", "Matched in Spotify", "Grammy Nominees", "Matched as Spotify Track"]
    values = [len(grammy_artists), len(matched_artists), len(grammy_nominees), len(matched_tracks)]
    colors = ["#333333", "#1DB954", "#555555", "#007ACC"]
    bars = ax.bar(categories, values, color=colors)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 20, f"{yval:,}", ha="center", va="bottom", fontweight="bold")
    ax.set_title("Cross-Source Entity Matching & Integration Potential")
    ax.set_ylabel("Entity Count")
    plt.tight_layout()
    fig.savefig(PROFILING_DIR / "cross_source_overlap.png", dpi=200)
    plt.close()

    # Save summary json
    summary_path = PROFILING_DIR / "profiling_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Profiling complete. Summary written to {summary_path}")

    # Generate Markdown Summary Table
    md_table = f"""# Data Profiling Summary Report

## 1. Structural Overview
| Metric | Spotify Dataset | Grammy Dataset |
| :--- | :--- | :--- |
| **Row Count** | {len(df_spotify):,} | {len(df_grammy):,} |
| **Column Count** | {len(df_spotify.columns)} | {len(df_grammy.columns)} |
| **Primary Grain** | Track by Genre `(track_id, track_genre)` | Nomination Event `(year, category, nominee)` |
| **Unique Track IDs / Entities** | {spot_track_uniq:,} unique tracks | {df_grammy['nominee'].nunique():,} unique nominees |

## 2. Completeness & Data Quality Risks
| Dataset | Column | Null Count | Null Rate (%) | Quality Risk & Engineering Treatment |
| :--- | :--- | :--- | :--- | :--- |
| **Spotify** | `artists` | 1 | 0.0009% | Missing artist metadata; impute with 'Unknown Artist' in cleaning phase. |
| **Spotify** | `album_name` | 1 | 0.0009% | Missing album title; impute with 'Unknown Album'. |
| **Spotify** | `track_name` | 1 | 0.0009% | Missing track title; impute with 'Unknown Track'. |
| **Grammy** | `artist` | {gram_nulls['artist']} | {gram_nulls['artist']/len(df_grammy)*100:.2f}% | Expected in craft/songwriting categories where artist is in `workers` or `nominee`. Resolved via multi-field entity extraction. |
| **Grammy** | `workers` | {gram_nulls['workers']} | {gram_nulls['workers']/len(df_grammy)*100:.2f}% | Expected for performer-only categories. |
| **Grammy** | `nominee` | {gram_nulls['nominee']} | {gram_nulls['nominee']/len(df_grammy)*100:.2f}% | Unnamed category entry; handled via fallback to title or quarantine. |

## 3. Cross-Source Entity Overlap
- **Unique Spotify Artists (tokenized):** {len(spotify_artists):,}
- **Unique Grammy Artists:** {len(grammy_artists):,}
- **Matched Artists:** {len(matched_artists):,} ({len(matched_artists)/len(grammy_artists)*100:.2f}% of Grammy artists found in Spotify catalog)
- **Direct Track/Nominee Matches:** {len(matched_tracks):,} tracks
"""
    with open(PROFILING_DIR / "profiling_report.md", "w", encoding="utf-8") as f:
        f.write(md_table)
    print("Markdown profiling report generated.")

if __name__ == "__main__":
    run_profiling()
