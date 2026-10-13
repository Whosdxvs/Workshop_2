"""
Data Warehouse Loading Engine (Idempotent Dimensional Loader)
Implements Sections 6.10, 6.11, 7.3: Safe Reruns, Idempotence, Audit Metrics.
Course: ETL (UAO) - Workshop 2
"""
import json
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from src.config import PREPARED_DATA_DIR, EVIDENCE_DIR
from src.db import get_dw_engine, init_dw_tables, DW_DB_TYPE

logger = logging.getLogger("load")

def get_table_counts(engine) -> dict:
    """Retrieves current row counts from all Data Warehouse tables."""
    tables = [
        "dim_time", "dim_award_category", "dim_genre",
        "dim_artist", "dim_track", "fact_track_performance", "fact_grammy_awards"
    ]
    counts = {}
    with engine.connect() as conn:
        for t in tables:
            try:
                res = conn.execute(text(f"SELECT COUNT(*) FROM {t}"))
                counts[t] = res.scalar()
            except Exception:
                counts[t] = 0
    return counts

def get_measure_aggregates(engine) -> dict:
    """Computes key analytical measure aggregates to verify data consistency across reruns."""
    measures = {}
    with engine.connect() as conn:
        try:
            res1 = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_tracks,
                    AVG(popularity) as avg_popularity,
                    AVG(danceability) as avg_danceability,
                    AVG(energy) as avg_energy,
                    SUM(CASE WHEN is_grammy_recognized = 1 THEN 1 ELSE 0 END) as grammy_tracks
                FROM fact_track_performance
            """)).mappings().first()
            measures["fact_track"] = dict(res1) if res1 else {}
        except Exception as e:
            measures["fact_track"] = str(e)

        try:
            res2 = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_awards,
                    SUM(CASE WHEN is_winner = 1 THEN 1 ELSE 0 END) as total_winners,
                    SUM(CASE WHEN is_spotify_matched = 1 THEN 1 ELSE 0 END) as matched_awards
                FROM fact_grammy_awards
            """)).mappings().first()
            measures["fact_grammy"] = dict(res2) if res2 else {}
        except Exception as e:
            measures["fact_grammy"] = str(e)
            
    return measures

def load_data_warehouse(
    prepared_dir: Path = PREPARED_DATA_DIR,
    output_audit: Path = None,
    batch_id: str = None
) -> dict:
    """
    Loads prepared dimensional tables into the Data Warehouse.
    Employs an idempotent transactional reload strategy with before/after audit tracking.
    """
    logger.info("Initializing Data Warehouse tables and checking connection...")
    init_dw_tables()
    engine = get_dw_engine()

    before_counts = get_table_counts(engine)
    before_measures = get_measure_aggregates(engine)
    logger.info(f"Row counts prior to load: {before_counts}")

    # Load prepared CSV files
    dim_time = pd.read_csv(prepared_dir / "dim_time.csv")
    dim_award_category = pd.read_csv(prepared_dir / "dim_award_category.csv")
    dim_genre = pd.read_csv(prepared_dir / "dim_genre.csv")
    dim_artist = pd.read_csv(prepared_dir / "dim_artist.csv")
    dim_track = pd.read_csv(prepared_dir / "dim_track.csv")
    fact_track = pd.read_csv(prepared_dir / "fact_track_performance.csv")
    fact_grammy = pd.read_csv(prepared_dir / "fact_grammy_awards.csv")

    logger.info("Executing transactional idempotent Data Warehouse load...")
    with engine.begin() as conn:
        # Disable foreign key checks for clean truncation and insertion
        if DW_DB_TYPE == "mysql":
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        else:
            conn.execute(text("SET CONSTRAINTS ALL DEFERRED;"))

        # Truncate tables in target
        for tbl in ["fact_grammy_awards", "fact_track_performance", "dim_track", "dim_artist", "dim_genre", "dim_award_category", "dim_time"]:
            conn.execute(text(f"DELETE FROM {tbl};"))

        logger.info("Writing dimension tables...")
        dim_time.to_sql("dim_time", con=conn, if_exists="append", index=False, chunksize=1000)
        dim_award_category.to_sql("dim_award_category", con=conn, if_exists="append", index=False, chunksize=1000)
        dim_genre.to_sql("dim_genre", con=conn, if_exists="append", index=False, chunksize=1000)
        dim_artist.to_sql("dim_artist", con=conn, if_exists="append", index=False, chunksize=1000)
        dim_track.to_sql("dim_track", con=conn, if_exists="append", index=False, chunksize=2000)

        logger.info("Writing fact tables...")
        fact_track.to_sql("fact_track_performance", con=conn, if_exists="append", index=False, chunksize=5000)
        fact_grammy.to_sql("fact_grammy_awards", con=conn, if_exists="append", index=False, chunksize=2000)

        if DW_DB_TYPE == "mysql":
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

    after_counts = get_table_counts(engine)
    after_measures = get_measure_aggregates(engine)
    logger.info(f"Row counts post load: {after_counts}")

    audit_report = {
        "batch_id": batch_id or f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "loaded_at": datetime.utcnow().isoformat() + "Z",
        "load_strategy": "Idempotent Transactional Truncate-and-Reload (Atomic Guarantee)",
        "db_type": engine.name,
        "before_counts": before_counts,
        "after_counts": after_counts,
        "net_growth": {k: after_counts[k] - before_counts[k] for k in after_counts},
        "measure_audit": {
            "before": before_measures,
            "after": after_measures
        },
        "load_status": "SUCCESS"
    }

    report_path = output_audit or (EVIDENCE_DIR / "load_summary.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2, default=str)

    logger.info(f"Load audit recorded successfully to: {report_path}")
    return audit_report

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    res = load_data_warehouse()
    print("Load Audit Summary:\n", json.dumps(res, indent=2, default=str))
