from datetime import date
import pytest
from app.schemas import Event, Participant


@pytest.fixture
def sample_event_dict():
    return {
        "id": 1,
        "title": "Python Conference",
        "description": "A great event",
        "date": date(2025, 6, 15),       # ← obligatoire !
        "location": "Paris",
        "capacity": 100,
    }


@pytest.fixture
def sample_participant_dict():
    return {"id": 1, "name": "Alice", "email": "alice@example.com"}


@pytest.fixture
def mock_event_store():
    store = []
    yield store
    store.clear()


@pytest.fixture
def prepopulated_event_store(mock_event_store):
    mock_event_store.extend([
        Event(id=1, title="Python Conf",      date=date(2025, 6, 15),
              location="Paris", capacity=100),
        Event(id=2, title="Django Meetup",    date=date(2025, 7, 1),
              location="Lyon",  capacity=50),
        Event(id=3, title="FastAPI Workshop", date=date(2025, 8, 10),
              location="Paris", capacity=20),
    ])
    return mock_event_store


@pytest.fixture(autouse=True)
def global_environment_logger():
    print("\n[SETUP] Début du test")
    yield
    print("[TEARDOWN] Fin du test")