"""
Database Connection and Utilities Module
Supports both MySQL and PostgreSQL dynamically based on configuration.
Course: ETL (UAO) - Workshop 2
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from src.config import (
    SOURCE_DB_TYPE, SOURCE_DB_HOST, SOURCE_DB_PORT, SOURCE_DB_USER, SOURCE_DB_PASSWORD, SOURCE_DB_NAME,
    DW_DB_TYPE, DW_DB_HOST, DW_DB_PORT, DW_DB_USER, DW_DB_PASSWORD, DW_DB_NAME, BASE_DIR
)

logger = logging.getLogger(__name__)

def build_connection_url(db_type: str, user: str, password: str, host: str, port: int, db_name: str) -> str:
    """Constructs SQLAlchemy connection URI."""
    encoded_pass = f":{password}" if password else ""
    if db_type == "mysql":
        return f"mysql+pymysql://{user}{encoded_pass}@{host}:{port}/{db_name}?charset=utf8mb4"
    elif db_type in ("postgres", "postgresql"):
        return f"postgresql+psycopg2://{user}{encoded_pass}@{host}:{port}/{db_name}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}. Only MySQL and PostgreSQL are allowed.")

def get_source_engine() -> Engine:
    """Returns SQLAlchemy engine for Grammy Source Database."""
    url = build_connection_url(
        SOURCE_DB_TYPE, SOURCE_DB_USER, SOURCE_DB_PASSWORD,
        SOURCE_DB_HOST, SOURCE_DB_PORT, SOURCE_DB_NAME
    )
    return create_engine(url, pool_pre_ping=True)

def get_dw_engine() -> Engine:
    """Returns SQLAlchemy engine for Target Analytical Data Warehouse."""
    url = build_connection_url(
        DW_DB_TYPE, DW_DB_USER, DW_DB_PASSWORD,
        DW_DB_HOST, DW_DB_PORT, DW_DB_NAME
    )
    return create_engine(url, pool_pre_ping=True)

def init_dw_tables():
    """Initializes tables in the Data Warehouse using DDL script."""
    engine = get_dw_engine()
    ddl_file = BASE_DIR / "sql" / "dw_schema.sql"
    if DW_DB_TYPE in ("postgres", "postgresql"):
        ddl_file = BASE_DIR / "sql" / "dw_schema_postgres.sql"

    logger.info(f"Initializing DW schema using {ddl_file}...")
    with open(ddl_file, "r", encoding="utf-8") as f:
        ddl_script = f.read()

    # Split statements
    statements = [stmt.strip() for stmt in ddl_script.split(";") if stmt.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            # Skip comment-only chunks
            lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
            clean_stmt = "\n".join(lines).strip()
            if clean_stmt:
                conn.execute(text(clean_stmt))
    logger.info("DW schema initialized successfully.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_dw_tables()
