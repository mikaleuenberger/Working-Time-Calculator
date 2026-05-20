"""Unit tests for the time_calculator domain logic."""
from datetime import date

import pytest

from wtcalculator.domain.time_calculator import (
    calculate_net_hours_and_comment,
    MIN_LUNCH_BREAK_MIN,
)


class TestNetHoursCalculation:
    """Test basic net hours calculation."""

    def test_simple_work_day_8h_with_1h_break(self):
        """8:00-17:00 with 60min break = 8h gross, 7h net."""
        result = calculate_net_hours_and_comment(
            start_hhmm="08:00",
            end_hhmm="17:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=60,
            user_birthdate=date(2001, 1, 1),
            work_date=date(2026, 5, 12),
        )
        assert result.net_hours_decimal == 8.0  # 9h gross - 1h break = 8h net

    def test_no_break_entered(self):
        """No break entered, only short_break_min deducted."""
        result = calculate_net_hours_and_comment(
            start_hhmm="08:00",
            end_hhmm="16:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=0,
            user_birthdate=date(2001, 1, 1),
            work_date=date(2026, 5, 12),
        )
        # 8h gross - 0 min break = 8h net
        assert result.net_hours_decimal == 8.0
        assert result.comment == ""

    def test_overnight_shift(self):
        """22:00 to 06:00 = 8h work (overnight)."""
        result = calculate_net_hours_and_comment(
            start_hhmm="22:00",
            end_hhmm="06:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=30,
            user_birthdate=date(2001, 1, 1),
            work_date=date(2026, 5, 12),
        )
        # 8h gross - 0.5h break = 7.5h net
        assert result.net_hours_decimal == 7.5

    def test_lunch_start_before_end(self):
        """12:00-13:00 lunch = 60min break."""
        result = calculate_net_hours_and_comment(
            start_hhmm="08:00",
            end_hhmm="17:00",
            lunch_start_hhmm="12:00",
            lunch_end_hhmm="13:00",
            short_break_min=0,
            user_birthdate=date(2001, 1, 1),
            work_date=date(2026, 5, 12),
        )
        # 9h gross - 1h lunch = 8h net
        assert result.net_hours_decimal == 8.0

    def test_lunch_end_before_start_invalid(self):
        """13:00 to 12:00 is invalid (end before start without overnight)."""
        result = calculate_net_hours_and_comment(
            start_hhmm="08:00",
            end_hhmm="17:00",
            lunch_start_hhmm="13:00",
            lunch_end_hhmm="12:00",
            short_break_min=0,
            user_birthdate=date(2001, 1, 1),
            work_date=date(2026, 5, 12),
        )
        # Should have error comment about invalid lunch
        assert "Ende vor Start" in result.comment

    def test_lunch_too_short_under_30min(self):
        """Lunch break of 15min should trigger warning."""
        result = calculate_net_hours_and_comment(
            start_hhmm="08:00",
            end_hhmm="17:00",
            lunch_start_hhmm="12:00",
            lunch_end_hhmm="12:15",
            short_break_min=0,
            user_birthdate=date(2001, 1, 1),
            work_date=date(2026, 5, 12),
        )
        assert "Mittag zu kurz" in result.comment

    def test_lunch_exceeds_3h_warning(self):
        """Lunch break of 4h should trigger unusual warning."""
        result = calculate_net_hours_and_comment(
            start_hhmm="08:00",
            end_hhmm="17:00",
            lunch_start_hhmm="12:00",
            lunch_end_hhmm="16:00",
            short_break_min=0,
            user_birthdate=date(2001, 1, 1),
            work_date=date(2026, 5, 12),
        )
        assert "unüblich" in result.comment


class TestMinorWorkerRules:
    """Test youth labor protection rules (user_age < 18)."""

    def test_minor_max_9h_daily(self):
        """Minors should get warning if working > 9h."""
        result = calculate_net_hours_and_comment(
            start_hhmm="06:00",
            end_hhmm="18:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=60,
            user_birthdate=date(2010, 1, 1),
            work_date=date(2026, 5, 12),
        )
        # 12h gross - 1h break = 11h net, but minor max is 9h
        assert "Maximalarbeitszeit Minderjährige" in result.comment

    def test_minor_night_work_warning(self):
        """Minors should not work between 22:00 and 06:00."""
        result = calculate_net_hours_and_comment(
            start_hhmm="22:00",
            end_hhmm="06:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=30,
            user_birthdate=date(2010, 1, 1),
            work_date=date(2026, 5, 12),
        )
        assert "Nachtarbeit" in result.comment
        assert "verboten" in result.comment

    def test_minor_weekend_work_warning(self):
        """Minors should not work on weekends (Sat=5, Sun=6)."""
        # Saturday
        result = calculate_net_hours_and_comment(
            start_hhmm="08:00",
            end_hhmm="17:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=60,
            user_birthdate=date(2010, 1, 1),
            work_date=date(2026, 5, 16),  # Saturday
        )
        assert "Wochenendarbeit" in result.comment
        assert "Minderjährige" in result.comment

    def test_minor_legal_hours_no_warning(self):
        """Minors working <= 9h should not get minor-max warning."""
        result = calculate_net_hours_and_comment(
            start_hhmm="08:00",
            end_hhmm="16:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=30,
            user_birthdate=date(2010, 1, 1),
            work_date=date(2026, 5, 12),  # Tuesday
        )
        # 8h gross - 0.5h break = 7.5h net, <= 9h, no warning
        assert "Maximalarbeitszeit Minderjährige" not in result.comment
        assert "Nachtarbeit" not in result.comment


class TestOverTimeWarnings:
    """Test overtime and over-12h warnings."""

    def test_over_12h_warning(self):
        """Working more than 12h net should trigger warning."""
        result = calculate_net_hours_and_comment(
            start_hhmm="06:00",
            end_hhmm="20:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=30,
            user_birthdate=date(1996, 1, 1),
            work_date=date(2026, 5, 12),
        )
        # 14h gross - 0.5h break = 13.5h net
        assert "Überzeit" in result.comment
        assert "12h" in result.comment

    def test_legal_hours_no_warning(self):
        """Normal 8h day with 1h break = 8h net, no warnings."""
        result = calculate_net_hours_and_comment(
            start_hhmm="08:00",
            end_hhmm="17:00",
            lunch_start_hhmm=None,
            lunch_end_hhmm=None,
            short_break_min=60,
            user_birthdate=date(1996, 1, 1),
            work_date=date(2026, 5, 12),
        )
        assert result.comment == ""
        assert result.net_hours_decimal == 8.0
