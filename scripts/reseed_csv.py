"""Script to reseed time entries from CSV (clears existing entries first)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from wtcalculator.data_access.db import session_scope
from wtcalculator.data_access.seed import seed_time_entries


def reseed_csv():
    """Clear all time entries and reseed from CSV."""
    csv_path = Path("data/time_entries.csv")

    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return

    with session_scope() as session:
        # Delete all existing time entries
        from wtcalculator.models import TimeEntry
        session.query(TimeEntry).delete()
        print("Cleared all existing time entries.")

    # Now seed from CSV with overwrite=True
    with session_scope() as session:
        imported, skipped, errors = seed_time_entries(session, csv_path, overwrite=True)
        print(f"Imported {imported} entries from CSV")
        if skipped > 0:
            print(f"Skipped: {skipped}")
        if errors:
            print(f"Errors:")
            for err in errors[:10]:
                print(f"  - {err}")

    print("Done!")


if __name__ == "__main__":
    reseed_csv()
