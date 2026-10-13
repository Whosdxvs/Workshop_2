"""
Source Preparation Script: Grammy Awards Relational Source Database
Loads the provided Grammy CSV into the operational source table and produces
row-count reconciliation evidence.
Course: ETL (UAO) - Workshop 2
"""
import json
import logging
from datetime import datetime
import pandas as pd
from sqlalchemy import text
from src.config import GRAMMY_CSV_PATH, EVIDENCE_DIR, BASE_DIR
from src.db import get_source_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("source_prep")

def setup_grammy_source_database():
    logger.info("Starting Grammy Source Database preparation...")

    if not GRAMMY_CSV_PATH.exists():
        raise FileNotFoundError(f"Grammy CSV source file not found at: {GRAMMY_CSV_PATH}")

    # Read CSV
    df = pd.read_csv(GRAMMY_CSV_PATH)
    csv_row_count = len(df)
    logger.info(f"Loaded source CSV '{GRAMMY_CSV_PATH.name}' with {csv_row_count} rows.")

    engine = get_source_engine()

    # Execute DDL
    ddl_path = BASE_DIR / "sql" / "source_setup.sql"
    with open(ddl_path, "r", encoding="utf-8") as f:
        ddl_script = f.read()

    with engine.begin() as conn:
        for stmt in ddl_script.split(";"):
            clean_stmt = stmt.strip()
            # filter comments
            lines = [l for l in clean_stmt.splitlines() if not l.strip().startswith("--")]
            clean_stmt = "\n".join(lines).strip()
            if clean_stmt:
                conn.execute(text(clean_stmt))

    logger.info("Created table 'source_grammy_awards' in operational database.")

    # Prepare DataFrame for insertion
    df_to_insert = df.copy()
    # Normalize types
    df_to_insert["winner"] = df_to_insert["winner"].astype(bool)
    
    # Ingest into operational source table
    df_to_insert.to_sql(
        name="source_grammy_awards",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=1000
    )

    # Reconcile row count
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM source_grammy_awards"))
        db_row_count = result.scalar()

    logger.info(f"Row count reconciliation: CSV={csv_row_count}, DB={db_row_count}")

    is_reconciled = (csv_row_count == db_row_count)
    evidence = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_csv_path": str(GRAMMY_CSV_PATH),
        "source_table": "source_grammy_awards",
        "csv_row_count": csv_row_count,
        "database_row_count": db_row_count,
        "reconciliation_status": "SUCCESS" if is_reconciled else "FAILED",
        "columns_mapped": list(df.columns)
    }

    reconciliation_file = EVIDENCE_DIR / "source_reconciliation.json"
    with open(reconciliation_file, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    logger.info(f"Reconciliation evidence recorded at: {reconciliation_file}")

    if not is_reconciled:
        raise ValueError(f"Reconciliation mismatch! CSV rows: {csv_row_count}, DB rows: {db_row_count}")

    print("\n" + "="*60)
    print("SOURCE PREPARATION AND RECONCILIATION SUCCESSFUL")
    print(f"Grammy CSV Rows:      {csv_row_count}")
    print(f"Database Table Rows: {db_row_count}")
    print("="*60 + "\n")
    return evidence

if __name__ == "__main__":
    setup_grammy_source_database()
