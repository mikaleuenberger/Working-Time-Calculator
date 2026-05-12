"""Pytest fixtures and configuration."""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from wtcalculator.models import Base, User, TimeEntry


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create a new database session for a test."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_user(test_session):
    """Create a sample adult user (>= 18) for testing."""
    user = User(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        business_role="Mitarbeiter",
        age=25,
        password_hash="",
        must_change_password=False,
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture
def minor_user(test_session):
    """Create a sample minor user (< 18) for testing youth labor rules."""
    user = User(
        first_name="Young",
        last_name="Worker",
        email="minor@example.com",
        business_role="Mitarbeiter",
        age=16,
        password_hash="",
        must_change_password=False,
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture
def supervisor_user(test_session):
    """Create a supervisor user for testing."""
    user = User(
        first_name="Super",
        last_name="Visor",
        email="supervisor@example.com",
        business_role="Vorgesetzter",
        age=35,
        password_hash="",
        must_change_password=False,
    )
    test_session.add(user)
    test_session.commit()
    return user
