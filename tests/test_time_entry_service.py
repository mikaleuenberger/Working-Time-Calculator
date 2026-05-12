"""Unit tests for TimeEntryService."""
from datetime import date, time

import pytest

from wtcalculator.models import TimeEntry
from wtcalculator.services.time_entry_service import TimeEntryService


class TestTimeEntryService:
    """Tests for TimeEntryService CRUD operations."""

    def test_upsert_entry_creates_new(self, test_session, sample_user):
        """Test creating a new time entry."""
        service = TimeEntryService(test_session)

        entry = service.upsert_entry(
            user=sample_user,
            work_date=date(2026, 5, 12),
            start_hhmm="08:00",
            end_hhmm="17:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=60,
        )

        assert entry.id is not None
        assert entry.start_time == time(8, 0)
        assert entry.end_time == time(17, 0)
        assert entry.short_break_min == 60
        assert entry.net_hours == 8.0
        assert entry.approved is False

    def test_upsert_entry_updates_existing(self, test_session, sample_user):
        """Test updating an existing time entry on the same date."""
        service = TimeEntryService(test_session)

        # Create first entry
        entry1 = service.upsert_entry(
            user=sample_user,
            work_date=date(2026, 5, 12),
            start_hhmm="08:00",
            end_hhmm="17:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=60,
        )

        # Update same date
        entry2 = service.upsert_entry(
            user=sample_user,
            work_date=date(2026, 5, 12),
            start_hhmm="09:00",
            end_hhmm="18:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=60,
        )

        assert entry1.id == entry2.id
        assert entry2.start_time == time(9, 0)
        assert entry2.end_time == time(18, 0)
        assert entry2.net_hours == 8.0  # 9h gross - 1h break

    def test_entry_exists(self, test_session, sample_user):
        """Test checking if entry exists for a date."""
        service = TimeEntryService(test_session)

        assert service.entry_exists(user_id=sample_user.id, work_date=date(2026, 5, 12)) is False

        service.upsert_entry(
            user=sample_user,
            work_date=date(2026, 5, 12),
            start_hhmm="08:00",
            end_hhmm="17:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=60,
        )

        assert service.entry_exists(user_id=sample_user.id, work_date=date(2026, 5, 12)) is True

    def test_list_month_entries(self, test_session, sample_user):
        """Test listing entries for a specific month."""
        service = TimeEntryService(test_session)

        # Add entries for May 2026
        service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 11),
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )
        service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 12),
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )
        # Entry for June (should not be in May results)
        service.upsert_entry(
            user=sample_user, work_date=date(2026, 6, 1),
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )

        may_entries = service.list_month_entries(user_id=sample_user.id, year=2026, month=5)
        assert len(may_entries) == 2

        june_entries = service.list_month_entries(user_id=sample_user.id, year=2026, month=6)
        assert len(june_entries) == 1

    def test_list_week_entries(self, test_session, sample_user):
        """Test listing entries for a specific week."""
        service = TimeEntryService(test_session)

        # Week of May 11, 2026 (Mon) - May 17, 2026 (Sun)
        service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 11),  # Monday
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )
        service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 13),  # Wednesday
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )
        # Next week
        service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 18),  # Monday next week
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )

        # Query week containing May 13
        week_entries = service.list_week_entries(
            user_id=sample_user.id, any_day_in_week=date(2026, 5, 13)
        )
        assert len(week_entries) == 2

    def test_get_weekly_hours(self, test_session, sample_user):
        """Test calculating total weekly hours."""
        service = TimeEntryService(test_session)

        # Add two 8h entries for the same week
        service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 11),
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )
        service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 13),
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )

        total = service.get_weekly_hours(
            user_id=sample_user.id,
            any_day_in_week=date(2026, 5, 13),
            exclude_date=None,
        )
        assert total == 16.0  # 2 x 8h days

    def test_exclude_date_in_weekly_hours(self, test_session, sample_user):
        """Test that exclude_date properly excludes a specific date."""
        service = TimeEntryService(test_session)

        service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 11),
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )
        service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 13),
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )

        # Exclude May 13 from calculation
        total = service.get_weekly_hours(
            user_id=sample_user.id,
            any_day_in_week=date(2026, 5, 13),
            exclude_date=date(2026, 5, 13),
        )
        assert total == 8.0  # Only May 11

    def test_approve_entry(self, test_session, sample_user):
        """Test approving a time entry."""
        service = TimeEntryService(test_session)

        entry = service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 12),
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )
        assert entry.approved is False

        success = service.approve_entry(entry_id=entry.id)
        assert success is True

        # Reload to verify
        approved_entry = test_session.get(TimeEntry, entry.id)
        assert approved_entry.approved is True

    def test_list_unapproved_entries(self, test_session, sample_user):
        """Test listing unapproved entries."""
        service = TimeEntryService(test_session)

        entry1 = service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 11),
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )
        service.upsert_entry(
            user=sample_user, work_date=date(2026, 5, 12),
            start_hhmm="08:00", end_hhmm="17:00",
            lunch_start_hhmm=None, lunch_end_hhmm=None, short_break_min=60,
        )

        service.approve_entry(entry_id=entry1.id)

        unapproved = service.list_unapproved_entries()
        # Should only have the one not yet approved
        assert len(unapproved) >= 1  # At least the one from May 12
