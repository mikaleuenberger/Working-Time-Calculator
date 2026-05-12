"""Script to add more test time entries for testing purposes."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from wtcalculator.data_access.db import session_scope
from wtcalculator.models import User
from wtcalculator.services.time_entry_service import TimeEntryService


def add_test_entries():
    # Get all users first
    with session_scope() as session:
        users = session.query(User).all()
        if not users:
            print("No users found! Please seed users first.")
            return
        print(f"Found {len(users)} users")

    # Add entries for each user in separate sessions
    today = date.today()

    for user in users:
        print(f"Adding entries for {user.first_name} {user.last_name} (ID: {user.id})...")

        with session_scope() as session:
            # Re-fetch user in this session
            db_user = session.get(User, user.id)
            if not db_user:
                print(f"  User {user.id} not found in session")
                continue

            tes = TimeEntryService(session)

            # Add entries for current month and past 2 months
            for month_offset in range(3):
                # Calculate target month
                target_month = today.month - month_offset
                target_year = today.year
                while target_month <= 0:
                    target_month += 12
                    target_year -= 1

                # Add 15-20 working days per month
                from datetime import date as date_class
                day = date_class(target_year, target_month, 1)

                # Find last day of month
                if target_month == 12:
                    last_day = date_class(target_year + 1, 1, 1) - timedelta(days=1)
                else:
                    last_day = date_class(target_year, target_month + 1, 1) - timedelta(days=1)

                entries_added = 0
                while day <= last_day:
                    # Only weekdays (Mon=0 to Fri=4)
                    if day.weekday() < 5:
                        # Random work hours between 6 and 10
                        hours = 6 + (day.day % 4)  # 6, 7, 8, or 9 hours

                        start_hour = 8
                        end_hour = start_hour + hours

                        start_str = f"{start_hour:02d}:00"
                        end_str = f"{end_hour:02d}:00"

                        # Random pause between 30 and 90 minutes
                        pause = 30 + (day.day % 4) * 15  # 30, 45, 60, or 75 minutes

                        try:
                            tes.upsert_entry(
                                user=db_user,
                                work_date=day,
                                start_hhmm=start_str,
                                end_hhmm=end_str,
                                lunch_start_hhmm=None,
                                lunch_end_hhmm=None,
                                short_break_min=pause,
                            )
                            entries_added += 1
                        except Exception as e:
                            print(f"  Error for {day}: {e}")

                    day += timedelta(days=1)

                print(f"  Added {entries_added} entries for {target_month}/{target_year}")

    print("Done!")


if __name__ == "__main__":
    add_test_entries()
