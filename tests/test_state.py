import sys
import os
import pytest

# Ensure the src directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.state import State  # noqa: E402


def test_state_persistence(tmp_path):
    # Use a file path for the SQLite database in the temp directory
    db_file = str(tmp_path / "test_state.db")

    # Initialize state with the database file
    state = State(db_path=db_file)

    # Act: Admit a patient
    state.admit("12345", "M")

    # Assert: Check via the API method
    assert state.has_patient("12345") is True

    # Simulation of restart: Create a new instance pointing to the same file
    new_state = State(db_path=db_file)

    # Assert: Data should still be there
    assert new_state.has_patient("12345") is True


def test_message_deduplication_persistence(tmp_path):
    db_file = str(tmp_path / "test_dedup.db")

    state = State(db_path=db_file)

    mid = "ID001"
    # Mark as processed
    state.mark_processed(mid)

    # Simulation of restart: Create a new instance
    restarted = State(db_path=db_file)

    # Assert: Deduplication should persist in the database
    assert restarted.is_processed(mid) is True


def test_lab_history_persistence(tmp_path):
    db_file = str(tmp_path / "test_labs.db")
    state = State(db_path=db_file)

    mrn = "999"
    state.admit(mrn, "F")
    state.add_creatinine(mrn, 1.5)
    state.add_creatinine(mrn, 2.5)

    # Re-initialize
    restarted = State(db_path=db_file)
    history = restarted.get_lab_history(mrn)

    assert history["min"] == 1.5
    assert history["max"] == 2.5
    assert len(history["results"]) == 2