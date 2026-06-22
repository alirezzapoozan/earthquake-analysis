import os
from pathlib import Path
from dotenv import load_dotenv

_BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BASE_DIR / ".env")

OUTPUT_DIR = "outputs"

TOKYO_LAT = 35.6762
TOKYO_LON = 139.6503

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "japan_earthquake")

if not DB_PASS:
    raise EnvironmentError(
        "\n\n[config] DB_PASS is not set!\n"
        "Create a .env file in the project root with:\n"
        "  DB_PASS=your_password\n"
        "See .env.example for a full template.\n"
    )

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
