"""
Stage 3: Persistent Storage Tests

Tests for SQLite reservation storage functionality:
- Database initialization
- Saving reservations
- Retrieving reservations
- Data validation and integrity
"""

import pytest
import sqlite3
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.stage3.storage import ReservationStorage
from src.stage3.integrate import process_approved_reservation, get_all_approved_reservations


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing."""
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test_reservations.db")
    yield db_path
    # Cleanup
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(tmpdir)
    except:
        pass


@pytest.fixture
def storage(temp_db_path):
    """Create a ReservationStorage instance with temporary database."""
    return ReservationStorage(db_path=temp_db_path)


@pytest.fixture
def sample_reservation():
    """Sample approved reservation."""
    return {
        "reservation_id": "REQ-20260225100000-001",
        "user_name": "John Doe",
        "car_number": "ABC123",
        "start_date": "2026-03-01",
        "end_date": "2026-03-07",
        "approval_time": "2026-02-25T10:00:00",
    }


# ============================================================================
# TESTS: Database Initialization
# ============================================================================

class TestDatabaseInit:
    """Test database initialization and table creation."""

    def test_database_creation(self, storage):
        """Test that database file is created."""
        assert storage.db_path.exists()

    def test_table_exists(self, storage):
        """Test that reservations table exists."""
        with sqlite3.connect(storage.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='reservations'"
            )
            assert cursor.fetchone() is not None


# ============================================================================
# TESTS: Saving Reservations
# ============================================================================

class TestSaveReservation:
    """Test saving reservations to database."""

    def test_save_success(self, storage, sample_reservation):
        """Test successful reservation save."""
        result = storage.save(sample_reservation)
        assert result is True

    def test_save_persists(self, storage, sample_reservation):
        """Test that saved reservation is persisted."""
        storage.save(sample_reservation)

        retrieved = storage.get_by_id(sample_reservation["reservation_id"])
        assert retrieved is not None
        assert retrieved["user_name"] == "John Doe"


# ============================================================================
# TESTS: Retrieving Reservations
# ============================================================================

class TestGetReservations:
    """Test retrieving reservations from database."""

    def test_get_by_id_success(self, storage, sample_reservation):
        """Test getting reservation by ID."""
        storage.save(sample_reservation)

        retrieved = storage.get_by_id(sample_reservation["reservation_id"])
        assert retrieved is not None
        assert retrieved["user_name"] == "John Doe"
        assert retrieved["car_number"] == "ABC123"

    def test_get_by_id_not_found(self, storage):
        """Test getting non-existent reservation."""
        retrieved = storage.get_by_id("REQ-NONEXISTENT")
        assert retrieved is None

    def test_get_all_empty(self, storage):
        """Test getting all from empty database."""
        all_reservations = storage.get_all()
        assert isinstance(all_reservations, list)
        assert len(all_reservations) == 0

    def test_get_all_with_data(self, storage):
        """Test getting all reservations."""
        res1 = {
            "reservation_id": "REQ-A",
            "user_name": "User A",
            "car_number": "CAR-A",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05",
            "approval_time": "2026-02-25T10:00:00",
        }
        res2 = {
            "reservation_id": "REQ-B",
            "user_name": "User B",
            "car_number": "CAR-B",
            "start_date": "2026-03-10",
            "end_date": "2026-03-15",
            "approval_time": "2026-02-25T11:00:00",
        }

        storage.save(res1)
        storage.save(res2)

        all_reservations = storage.get_all()
        assert len(all_reservations) == 2


# ============================================================================
# TESTS: Data Integrity
# ============================================================================

class TestDataIntegrity:
    """Test data integrity and constraints."""

    def test_primary_key_prevents_duplicates(self, storage, sample_reservation):
        """Test that primary key prevents duplicate IDs."""
        storage.save(sample_reservation)

        # Try to save with same ID but different data
        modified = sample_reservation.copy()
        modified["user_name"] = "Jane Doe"
        storage.save(modified)

        # Should still have 1 record
        all_reservations = storage.get_all()
        assert len(all_reservations) == 1

    def test_required_fields_stored(self, storage, sample_reservation):
        """Test that required fields are stored."""
        storage.save(sample_reservation)
        retrieved = storage.get_by_id(sample_reservation["reservation_id"])

        assert retrieved["user_name"] == "John Doe"
        assert retrieved["car_number"] == "ABC123"
        assert retrieved["start_date"] == "2026-03-01"
        assert retrieved["end_date"] == "2026-03-07"


# ============================================================================
# TESTS: Integration Functions
# ============================================================================

class TestIntegrationFunctions:
    """Test integration functions."""

    def test_process_approved_reservation(self, sample_reservation):
        """Test processing approved reservation."""
        result = process_approved_reservation(sample_reservation)
        assert result is True

    def test_get_all_approved_reservations(self, sample_reservation):
        """Test getting all approved reservations."""
        process_approved_reservation(sample_reservation)
        all_reservations = get_all_approved_reservations()
        assert len(all_reservations) > 0

