"""
Apache Airflow DAG: Reliable Music Data Batch Pipeline
Orchestrates: Extract -> Raw Validation -> Transform & Integrate -> Prepared Validation -> Load DW
Course: ETL (G01) - Workshop 2
Authoring Interface: Airflow 3.1.8 TaskFlow API (airflow.sdk)
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Standard Airflow 3.1.8 TaskFlow API imports with graceful fallback
try:
    from airflow.sdk import dag, task
except ImportError:
    try:
        from airflow.decorators import dag, task
    except ImportError:
        # Standalone mock runner for local development without active Airflow runtime
        def dag(*args, **kwargs):
            def decorator(f):
                return f
            return decorator
        def task(*args, **kwargs):
            def decorator(f):
                return f
            return decorator

from src.extract import extract_spotify as run_extract_spotify
from src.extract import extract_grammys as run_extract_grammys
from src.validation import validate_spotify_raw as run_validate_spotify_raw
from src.validation import validate_grammy_raw as run_validate_grammy_raw
from src.validation import validate_prepared as run_validate_prepared
from src.transform import transform_and_integrate as run_transform_and_integrate
from src.load import load_data_warehouse as run_load_dw

# Selective Retry Policies (Section 6.11)
DEFAULT_DAG_ARGS = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
}

@dag(
    dag_id="reliable_music_pipeline",
    default_args=DEFAULT_DAG_ARGS,
    description="Batch pipeline integrating Spotify catalog and Grammy awards with dual GX validation gates",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["etl", "workshop-2", "spotify", "grammy", "great-expectations"]
)
def reliable_music_pipeline():
    """
    Complete end-to-end DAG orchestrating Spotify and Grammy data integration.
    """

    # --------------------------------------------------------------------------
    # BRANCH 1: SPOTIFY EXTRACTION & RAW VALIDATION
    # --------------------------------------------------------------------------
    @task(
        task_id="extract_spotify",
        retries=2,
        retry_delay=timedelta(seconds=10),
        retry_exponential_backoff=False
    )
    def extract_spotify() -> dict:
        """Extracts raw Spotify catalog CSV and outputs metadata reference."""
        return run_extract_spotify()

    @task(
        task_id="validate_spotify_raw",
        retries=0  # Deterministic DQ checks must NOT retry blindly
    )
    def validate_spotify_raw(metadata: dict) -> dict:
        """Raw validation gate for Spotify catalog enforcing GX expectations."""
        raw_file = Path(metadata["raw_output_path"])
        return run_validate_spotify_raw(raw_file)

    # --------------------------------------------------------------------------
    # BRANCH 2: GRAMMY RELATIONAL DB EXTRACTION & RAW VALIDATION
    # --------------------------------------------------------------------------
    @task(
        task_id="extract_grammys",
        retries=3,  # Transient DB connection retries are justified
        retry_delay=timedelta(seconds=15),
        retry_exponential_backoff=True
    )
    def extract_grammys() -> dict:
        """Extracts Grammy records from operational relational source table."""
        return run_extract_grammys()

    @task(
        task_id="validate_grammys_raw",
        retries=0  # Deterministic DQ checks
    )
    def validate_grammys_raw(metadata: dict) -> dict:
        """Raw validation gate for Grammy relational data enforcing GX expectations."""
        raw_file = Path(metadata["raw_output_path"])
        return run_validate_grammy_raw(raw_file)

    # --------------------------------------------------------------------------
    # CONVERGENCE: TRANSFORMATION & CROSS-SOURCE INTEGRATION
    # --------------------------------------------------------------------------
    @task(
        task_id="transform_and_integrate",
        retries=0
    )
    def transform_and_integrate(spotify_val: dict, grammy_val: dict) -> dict:
        """
        Executes cleaning, harmonization, entity resolution, and star schema preparation.
        Only runs when both raw validation gates have succeeded.
        """
        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        return run_transform_and_integrate(batch_id=batch_id)

    # --------------------------------------------------------------------------
    # GATE 2: PREPARED DATA VALIDATION
    # --------------------------------------------------------------------------
    @task(
        task_id="validate_prepared",
        retries=0
    )
    def validate_prepared(transform_meta: dict) -> dict:
        """
        Prepared validation gate ensuring domain ranges, uniqueness, and referential integrity.
        Blocks DW loading if any Critical expectation is violated.
        """
        from src.config import PREPARED_DATA_DIR
        return run_validate_prepared(PREPARED_DATA_DIR)

    # --------------------------------------------------------------------------
    # TARGET: DIMENSIONAL DATA WAREHOUSE LOAD
    # --------------------------------------------------------------------------
    @task(
        task_id="load_dw",
        retries=2,  # Transient deadlock / lock wait retries
        retry_delay=timedelta(seconds=15)
    )
    def load_dw(val_meta: dict) -> dict:
        """
        Loads prepared dimensional star schema into Data Warehouse with idempotence guarantee.
        """
        from src.config import PREPARED_DATA_DIR
        return run_load_dw(PREPARED_DATA_DIR)

    # Dependency Flow Definition
    spot_meta = extract_spotify()
    spot_val = validate_spotify_raw(spot_meta)

    gram_meta = extract_grammys()
    gram_val = validate_grammys_raw(gram_meta)

    prepared_meta = transform_and_integrate(spot_val, gram_val)
    prepared_val = validate_prepared(prepared_meta)
    
    load_summary = load_dw(prepared_val)

# Instantiate the DAG
pipeline_dag = reliable_music_pipeline()
