"""
Pytest configuration and fixtures for the FastAPI application tests.
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Fixture that provides a TestClient for making requests to the app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Fixture that resets the activities dict before and after each test.
    This prevents test pollution by ensuring each test starts with a clean state.
    Uses autouse=True to automatically apply to all tests.
    """
    # Save a deep copy of the original activities state before the test
    original_activities = copy.deepcopy(activities)
    
    yield  # Run the test
    
    # Restore the original activities state after the test
    activities.clear()
    activities.update(original_activities)
