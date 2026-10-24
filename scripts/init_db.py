"""Create the LitroPH warehouse schemas and raw tables.

Usage (from the project root, with DB_* values in .env):
    python scripts/init_db.py
"""
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
SQL_FILE = ROOT / "sql" / "create_raw_tables.sql"


def main():
    load_dotenv(ROOT / ".env")
    missing = [k for k in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD") if not os.getenv(k)]
    if missing:
        sys.exit(f"Missing {', '.join(missing)} in .env")

    print(f"Connecting to {os.getenv('DB_NAME')} on {os.getenv('DB_HOST')}...")
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
        sslmode=os.getenv("DB_SSLMODE", "prefer"),
        connect_timeout=30,
    )
    try:
        with conn, conn.cursor() as cur:
            cur.execute(SQL_FILE.read_text(encoding="utf-8"))
            cur.execute("""
                SELECT table_schema || '.' || table_name FROM information_schema.tables
                WHERE table_schema = 'raw_ingestion' ORDER BY 1
            """)
            tables = [row[0] for row in cur.fetchall()]
        print("Ready:", ", ".join(tables))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
