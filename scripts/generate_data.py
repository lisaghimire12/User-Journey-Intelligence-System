"""
generate_data.py
-----------------
Generates synthetic event-level data and loads it into the database.

Usage:
    python scripts/generate_data.py --sessions 6000 --reset
"""
import argparse
import _bootstrap  # noqa: F401

from src import database
from src.data_generator import generate_events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=int, default=None, help="Number of sessions to generate")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--reset", action="store_true", help="Truncate existing data first")
    args = parser.parse_args()

    database.init_schema()
    if args.reset:
        database.truncate_all()
        print("Existing data cleared.")

    print("Generating synthetic sessions/events/journeys ...")
    sessions_df, events_df, journeys_df = generate_events(n_sessions=args.sessions, seed=args.seed)

    n_sessions = database.write_dataframe(sessions_df.to_pandas(), "sessions")
    n_events = database.write_dataframe(events_df.to_pandas(), "events")
    n_journeys = database.write_dataframe(journeys_df.to_pandas(), "journeys")

    print(f"Inserted: {n_sessions} sessions, {n_events} events, {n_journeys} journeys")
    print(f"Conversion rate: {journeys_df['converted'].mean() * 100:.2f}%")


if __name__ == "__main__":
    main()
