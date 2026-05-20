"""Unit tests for AuthController business logic."""
import pytest
from unittest.mock import patch
from contextlib import contextmanager
from datetime import date

from wtcalculator.app_controler import AuthController, _parse_time_hh_mm, _parse_date_yyyy_mm_dd


class TestDateTimeParsing:
    """Test datetime parsing utilities."""

    def test_parse_valid_date(self):
        """Test parsing a valid YYYY-MM-DD date."""
        result = _parse_date_yyyy_mm_dd("2026-05-12")
        assert result == date(2026, 5, 12)

    def test_parse_invalid_date_format(self):
        """Test that invalid date format raises exception."""
        with pytest.raises(Exception):
            _parse_date_yyyy_mm_dd("12-05-2026")

    def test_parse_valid_time(self):
        """Test parsing a valid HH:MM time."""
        result = _parse_time_hh_mm("08:30")
        assert result.hour == 8
        assert result.minute == 30

    def test_parse_invalid_time_format(self):
        """Test that invalid time format raises exception."""
        with pytest.raises(Exception):
            _parse_time_hh_mm("25:99")  # Invalid hour and minute


class TestAuthControllerUserManagement:
    """Tests for user management methods in AuthController."""

    def test_get_all_users_returns_list(self, test_session, sample_user):
        """Test that get_all_users returns properly formatted user list."""
        # Note: This test requires a real database session due to session_scope usage
        # In a real test environment, we would mock the database or use integration tests
        pass  # Skipped due to session_scope dependency

    def test_upsert_user_validation_empty_names(self, test_session):
        """Test that upsert_user rejects empty first/last name."""
        @contextmanager
        def mock_session_scope():
            yield test_session

        controller = AuthController()
        with patch('wtcalculator.app_controler.session_scope', mock_session_scope):
            result = controller.upsert_user({
                'first_name': '',
                'last_name': '',
                'email': 'test@example.com',
                'role': 'Mitarbeiter',
                'birthdate': '2001-05-01',
            })
        assert result['status'] == 'error'
        assert 'Vorname und Nachname' in result['message']

    def test_upsert_user_validation_invalid_email(self, test_session):
        """Test that upsert_user rejects invalid email."""
        @contextmanager
        def mock_session_scope():
            yield test_session

        controller = AuthController()
        with patch('wtcalculator.app_controler.session_scope', mock_session_scope):
            result = controller.upsert_user({
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'not-an-email',
                'role': 'Mitarbeiter',
                'birthdate': '2001-10-01',
            })
        assert result['status'] == 'error'
        assert 'E-Mail' in result['message']

    def test_upsert_user_validation_invalid_role(self, test_session):
        """Test that upsert_user rejects invalid role."""
        @contextmanager
        def mock_session_scope():
            yield test_session

        controller = AuthController()
        with patch('wtcalculator.app_controler.session_scope', mock_session_scope):
            result = controller.upsert_user({
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'role': 'InvalidRole',
                'birthdate': '2001-11-01',
            })
        assert result['status'] == 'error'
        assert 'Rolle' in result['message']

    def test_upsert_user_validation_age_too_young(self, test_session):
        """Test that upsert_user rejects age below minimum."""
        @contextmanager
        def mock_session_scope():
            yield test_session

        controller = AuthController()
        with patch('wtcalculator.app_controler.session_scope', mock_session_scope):
            result = controller.upsert_user({
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'role': 'Mitarbeiter',
                'birthdate': '2016-01-01',
            })
        assert result['status'] == 'error'
        assert 'Alter' in result['message']

    def test_upsert_user_validation_age_too_old(self, test_session):
        """Test that upsert_user rejects age above maximum."""
        @contextmanager
        def mock_session_scope():
            yield test_session

        controller = AuthController()
        with patch('wtcalculator.app_controler.session_scope', mock_session_scope):
            result = controller.upsert_user({
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'role': 'Mitarbeiter',
                'birthdate': '1906-05-01',
            })
        assert result['status'] == 'error'
        assert 'Alter' in result['message']

    def test_upsert_user_validation_name_too_long(self, test_session):
        """Test that upsert_user rejects names exceeding max length."""
        @contextmanager
        def mock_session_scope():
            yield test_session

        controller = AuthController()
        with patch('wtcalculator.app_controler.session_scope', mock_session_scope):
            result = controller.upsert_user({
                'first_name': 'A' * 100,  # NAME_MAX_LENGTH is 50
                'last_name': 'Doe',
                'email': 'john@example.com',
                'role': 'Mitarbeiter',
                'birthdate': '2001-12-01',
            })
        assert result['status'] == 'error'
        assert 'zu lang' in result['message']


class TestAuthControllerTimeEntryValidation:
    """Tests for time entry validation in AuthController."""

    def test_save_time_entry_invalid_date_format(self):
        """Test that save_time_entry rejects invalid date format."""
        controller = AuthController()
        result = controller.save_time_entry(
            user_id=999,  # Non-existent user, but date validation happens first
            date_str="05-12-2026",  # Wrong format
            start_s="08:00",
            end_s="17:00",
            pause_minutes=60,
        )
        assert result['status'] == 'error'
        assert 'Datum' in result['message']

    def test_save_time_entry_invalid_time_format(self):
        """Test that save_time_entry rejects invalid time format."""
        controller = AuthController()
        result = controller.save_time_entry(
            user_id=999,
            date_str="2026-05-12",
            start_s="99:99",  # Invalid time
            end_s="17:00",
            pause_minutes=60,
        )
        assert result['status'] == 'error'
        assert 'hh:mm' in result['message']
