"""
init_database.py
-----------------
Creates all database tables (idempotent). Run this once before
generate_data.py.

Usage:
    python scripts/init_database.py
"""
import _bootstrap  # noqa: F401
from src import database
from src.config import settings


def main():
    database.init_schema()
    print(f"Schema initialized against: {settings.database_url}")
    print("Tables ready: sessions, events, journeys, causal_results, simulations, recommendations")


if __name__ == "__main__":
    main()
