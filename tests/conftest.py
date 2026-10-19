from datetime import date, timedelta

import pytest
from app.schemas import Event


@pytest.fixture
def sample_event_dict():
    """Return a valid event dictionary for testing."""
    return {
        "id": 1,
        "title": "Python Conference",
        "description": "A great event",
        "date": date.today() + timedelta(days=10),
        "location": "Paris",
        "capacity": 100,
    }


@pytest.fixture
def sample_participant_dict():
    """Return a valid participant dictionary for testing."""
    return {
        "id": 1,
        "name": "Alice Smith",
        "email": "alice@example.com",
    }


@pytest.fixture
def mock_event_store():
    """Create an in-memory event store and clear it after each test."""
    store = []
    yield store
    store.clear()


@pytest.fixture
def prepopulated_event_store(mock_event_store, sample_event_dict):
    """Create three sample Event objects for testing."""
    events_data = [
        sample_event_dict.copy(),
        {
            **sample_event_dict,
            "id": 2,
            "title": "Cybersecurity Workshop",
            "location": "London",
        },
        {
            **sample_event_dict,
            "id": 3,
            "title": "Cybersecurity Summit",
            "location": "Paris",
        },
    ]

    mock_event_store.extend(
        Event(**event_data) for event_data in events_data
    )

    return mock_event_store


@pytest.fixture(autouse=True)
def global_environment_logger():
    """Print setup and teardown markers for every test."""
    print("\n[SETUP] Starting test")
    yield
    print("\n[TEARDOWN] Test completed")
