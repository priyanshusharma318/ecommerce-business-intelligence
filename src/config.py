"""
Configuration module for the E-Commerce BI & Sales Analytics Platform.
Handles environment variables, filesystem paths, database connection parameters,
and core operational constants.
"""

import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Define project root directory dynamically
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()  # Fallback to standard environment

# Configure Matplotlib writable cache directory
mpl_cache_dir = os.environ.get("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "ecommerce_mpl_cache"))
os.makedirs(mpl_cache_dir, exist_ok=True)
os.environ["MPLCONFIGDIR"] = mpl_cache_dir

# Directory Paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = Path(os.environ.get("RAW_DATA_DIR", DATA_DIR / "raw"))
PROCESSED_DATA_DIR = Path(os.environ.get("PROCESSED_DATA_DIR", DATA_DIR / "processed"))
EXPORTS_DIR = Path(os.environ.get("EXPORTS_DIR", DATA_DIR / "exports"))
SQL_DIR = PROJECT_ROOT / "sql"
REPORTS_DIR = PROJECT_ROOT / "reports"
POWERBI_DIR = PROJECT_ROOT / "powerbi"

# Ensure runtime directories exist
for path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, EXPORTS_DIR, REPORTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Database Configuration
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "ecommerce_olist")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

# PostgreSQL default URL
POSTGRES_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Standalone SQLite fallback for zero-dependency local testing and CI/CD validation
SQLITE_DB_PATH = PROCESSED_DATA_DIR / "ecommerce_analytics.db"
SQLITE_URL = f"sqlite:///{SQLITE_DB_PATH.as_posix()}"

# Active Database URL: uses DATABASE_URL if set, else POSTGRES_URL
ACTIVE_DB_URL = os.environ.get("DATABASE_URL", POSTGRES_URL)

# Required Olist Dataset File Mapping
DATASET_FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

# Date format constants for Olist dataset
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_ONLY_FORMAT = "%Y-%m-%d"
