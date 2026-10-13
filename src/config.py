"""
Configuration and Environment Settings
Course: ETL (UAO) - Workshop 2
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Source Database Settings (Grammy Operational Source)
SOURCE_DB_TYPE = os.getenv("SOURCE_DB_TYPE", "mysql").lower()
SOURCE_DB_HOST = os.getenv("SOURCE_DB_HOST", "127.0.0.1")
SOURCE_DB_PORT = int(os.getenv("SOURCE_DB_PORT", "3306"))
SOURCE_DB_USER = os.getenv("SOURCE_DB_USER", "root")
SOURCE_DB_PASSWORD = os.getenv("SOURCE_DB_PASSWORD", "")
SOURCE_DB_NAME = os.getenv("SOURCE_DB_NAME", "grammy_source_db")

# Target Data Warehouse Settings
DW_DB_TYPE = os.getenv("DW_DB_TYPE", "mysql").lower()
DW_DB_HOST = os.getenv("DW_DB_HOST", "127.0.0.1")
DW_DB_PORT = int(os.getenv("DW_DB_PORT", "3306"))
DW_DB_USER = os.getenv("DW_DB_USER", "root")
DW_DB_PASSWORD = os.getenv("DW_DB_PASSWORD", "")
DW_DB_NAME = os.getenv("DW_DB_NAME", "music_dw")

# File Paths
SPOTIFY_CSV_PATH = Path(os.getenv("SPOTIFY_CSV_PATH", BASE_DIR / "spotify_dataset.csv"))
GRAMMY_CSV_PATH = Path(os.getenv("GRAMMY_CSV_PATH", BASE_DIR / "the_grammy_awards.csv"))
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
RAW_DATA_DIR = DATA_DIR / "raw"
PREPARED_DATA_DIR = DATA_DIR / "prepared"
QUARANTINE_DATA_DIR = DATA_DIR / "quarantine"
EVIDENCE_DIR = Path(os.getenv("EVIDENCE_DIR", BASE_DIR / "docs" / "evidence"))

# Ensure directories exist
for p in [RAW_DATA_DIR, PREPARED_DATA_DIR, QUARANTINE_DATA_DIR, EVIDENCE_DIR]:
    p.mkdir(parents=True, exist_ok=True)
