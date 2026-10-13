"""
Extraction Module: Spotify CSV and Grammy Relational Database Extraction
Course: ETL (UAO) - Workshop 2
Principle: Operational extraction from relational database for Grammy data.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from src.config import (
    SPOTIFY_CSV_PATH, RAW_DATA_DIR, EVIDENCE_DIR
)
from src.db import get_source_engine

logger = logging.getLogger("extract")

def extract_spotify(source_csv: Path = SPOTIFY_CSV_PATH, output_dir: Path = RAW_DATA_DIR) -> dict:
    """
    Extracts Spotify catalog data from CSV source file without premature cleaning.
    """
    logger.info(f"Extracting Spotify data from file source: {source_csv}")
    if not Path(source_csv).exists():
        raise FileNotFoundError(f"Spotify source CSV not found at: {source_csv}")

    df = pd.read_csv(source_csv)
    row_count = len(df)
    
    # Save uncleaned raw extraction
    output_path = output_dir / "spotify_raw.csv"
    df.to_csv(output_path, index=False)

    metadata = {
        "source": "spotify_csv",
        "source_path": str(source_csv),
        "raw_output_path": str(output_path),
        "row_count": row_count,
        "extracted_columns": list(df.columns),
        "extracted_at": datetime.utcnow().isoformat() + "Z"
    }
    logger.info(f"Spotify raw extraction complete. {row_count} records saved to {output_path}")
    return metadata

def extract_grammys(output_dir: Path = RAW_DATA_DIR) -> dict:
    """
    Extracts Grammy awards data directly from the relational source database table (source_grammy_awards).
    Demonstrates compliance with Section 4.3 requirement.
    """
    logger.info("Extracting Grammy data from relational operational source database...")
    engine = get_source_engine()

    query = "SELECT year, title, published_at, updated_at, category, nominee, artist, workers, img, winner FROM source_grammy_awards"
    df = pd.read_sql_query(query, con=engine)
    row_count = len(df)

    output_path = output_dir / "grammy_raw.csv"
    df.to_csv(output_path, index=False)

    metadata = {
        "source": "relational_database",
        "source_table": "source_grammy_awards",
        "database_type": engine.name,
        "raw_output_path": str(output_path),
        "row_count": row_count,
        "extracted_columns": list(df.columns),
        "extracted_at": datetime.utcnow().isoformat() + "Z"
    }
    logger.info(f"Grammy raw relational extraction complete. {row_count} records saved to {output_path}")
    return metadata

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    s_meta = extract_spotify()
    g_meta = extract_grammys()
    print("Spotify extraction metadata:", json.dumps(s_meta, indent=2))
    print("Grammy extraction metadata:", json.dumps(g_meta, indent=2))
