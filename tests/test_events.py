import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.schemas import Event
from app.services import (
    filter_events_by_title,
    filter_events_by_location,
)
from app.database import Base, get_db
from app.routers.events import router as events_router


# ==================================================
# Fixtures
# ==================================================

@pytest.fixture
def sample_event_dict():
    return {
        "id": 1,
        "title": "Python Workshop",
        "description": "Python training",
        "date": date(2026, 11, 15),
        "location": "Constantine",
        "capacity": 50,
    }


@pytest.fixture
def sample_events():
    return [
        Event(
            id=1,
            title="Python Workshop",
            date=date(2026, 11, 15),
            location="Constantine",
            capacity=20,
        ),
        Event(
            id=2,
            title="Java Course",
            date=date(2026, 11, 16),
            location="Alger",
            capacity=30,
        ),
        Event(
            id=3,
            title="Python Conference",
            date=date(2026, 11, 17),
            location="Constantine",
            capacity=100,
        ),
    ]


@pytest.fixture
def event_client():
    """Client API utilisant une base SQLite temporaire."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    Base.metadata.create_all(bind=test_engine)

    app = FastAPI()
    app.include_router(events_router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture
def event_payload():
    """Données d'événement avec une date future."""
    return {
        "title": "Python Workshop",
        "description": "Workshop de Python",
        "date": (date.today() + timedelta(days=30)).isoformat(),
        "location": "Constantine",
        "capacity": 50,
    }


# ==================================================
# Tests du schéma Event
# ==================================================

def test_event_valid_data(sample_event_dict):
    event = Event(**sample_event_dict)

    assert event.title == "Python Workshop"
    assert event.location == "Constantine"
    assert event.capacity == 50


def test_event_minimum_capacity():
    event = Event(
        id=1,
        title="Workshop",
        date=date(2026, 11, 15),
        location="Alger",
        capacity=1,
    )

    assert event.capacity == 1


def test_event_maximum_capacity():
    event = Event(
        id=2,
        title="Workshop",
        date=date(2026, 11, 15),
        location="Alger",
        capacity=10000,
    )

    assert event.capacity == 10000


def test_event_minimum_title_length():
    event = Event(
        id=3,
        title="ABC",
        date=date(2026, 11, 15),
        location="Alger",
        capacity=10,
    )

    assert event.title == "ABC"


def test_event_title_too_short():
    with pytest.raises(ValidationError):
        Event(
            id=4,
            title="AB",
            date=date(2026, 11, 15),
            location="Alger",
            capacity=10,
        )


@pytest.mark.parametrize("capacity", [0, -1, 10001])
def test_event_invalid_capacity(capacity):
    with pytest.raises(ValidationError):
        Event(
            id=5,
            title="Workshop",
            date=date(2026, 11, 15),
            location="Alger",
            capacity=capacity,
        )


# ==================================================
# Tests des fonctions de filtrage
# ==================================================

def test_filter_events_by_title(sample_events):
    result = filter_events_by_title(sample_events, "Python")

    assert len(result) == 2


def test_filter_events_by_title_case_insensitive(sample_events):
    result = filter_events_by_title(sample_events, "pYtHoN")

    assert len(result) == 2


def test_filter_events_by_title_no_match(sample_events):
    assert filter_events_by_title(sample_events, "Ruby") == []


def test_filter_events_by_title_empty_list():
    assert filter_events_by_title([], "Python") == []


def test_filter_events_by_location(sample_events):
    result = filter_events_by_location(sample_events, "Constantine")

    assert len(result) == 2


def test_filter_events_by_location_case_insensitive(sample_events):
    result = filter_events_by_location(sample_events, "cOnStAnTiNe")

    assert len(result) == 2


def test_filter_events_by_location_no_match(sample_events):
    assert filter_events_by_location(sample_events, "Oran") == []


def test_filter_events_by_location_empty_list():
    assert filter_events_by_location([], "Alger") == []


# ==================================================
# Tests des routes de l'API Events
# ==================================================

def test_create_event_success(event_client, event_payload):
    response = event_client.post("/events/", json=event_payload)

    assert response.status_code == 201
    assert response.json()["title"] == "Python Workshop"
    assert response.json()["location"] == "Constantine"


def test_create_event_past_date(event_client, event_payload):
    event_payload["date"] = (
        date.today() - timedelta(days=1)
    ).isoformat()

    response = event_client.post("/events/", json=event_payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Event date cannot be in the past."


def test_list_events_empty(event_client):
    response = event_client.get("/events/")

    assert response.status_code == 200
    assert response.json() == []


def test_list_events_success(event_client, event_payload):
    event_client.post("/events/", json=event_payload)

    second_event = event_payload.copy()
    second_event["title"] = "Java Course"
    second_event["location"] = "Alger"

    event_client.post("/events/", json=second_event)

    response = event_client.get("/events/")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_events_search_by_title(event_client, event_payload):
    event_client.post("/events/", json=event_payload)

    response = event_client.get(
        "/events/",
        params={"search": "Python"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Python Workshop"


def test_list_events_search_by_location(event_client, event_payload):
    event_client.post("/events/", json=event_payload)

    response = event_client.get(
        "/events/",
        params={"location": "Constantine"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_events_search_by_title_and_location(
    event_client, event_payload
):
    event_client.post("/events/", json=event_payload)

    response = event_client.get(
        "/events/",
        params={
            "search": "Python",
            "location": "Constantine",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_events_search_no_match(event_client, event_payload):
    event_client.post("/events/", json=event_payload)

    response = event_client.get(
        "/events/",
        params={"search": "Ruby"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_event_success(event_client, event_payload):
    create_response = event_client.post(
        "/events/",
        json=event_payload,
    )
    event_id = create_response.json()["id"]

    response = event_client.get(f"/events/{event_id}")

    assert response.status_code == 200
    assert response.json()["id"] == event_id


def test_get_event_not_found(event_client):
    response = event_client.get("/events/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found."


def test_update_event_success(event_client, event_payload):
    create_response = event_client.post(
        "/events/",
        json=event_payload,
    )
    event_id = create_response.json()["id"]

    updated_payload = event_payload.copy()
    updated_payload["title"] = "Updated Python Workshop"
    updated_payload["capacity"] = 100

    response = event_client.put(
        f"/events/{event_id}",
        json=updated_payload,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Python Workshop"
    assert response.json()["capacity"] == 100


def test_update_event_not_found(event_client, event_payload):
    response = event_client.put(
        "/events/9999",
        json=event_payload,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found."


def test_update_event_past_date(event_client, event_payload):
    create_response = event_client.post(
        "/events/",
        json=event_payload,
    )
    event_id = create_response.json()["id"]

    updated_payload = event_payload.copy()
    updated_payload["date"] = (
        date.today() - timedelta(days=1)
    ).isoformat()

    response = event_client.put(
        f"/events/{event_id}",
        json=updated_payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Event date cannot be in the past."


def test_delete_event_success(event_client, event_payload):
    create_response = event_client.post(
        "/events/",
        json=event_payload,
    )
    event_id = create_response.json()["id"]

    response = event_client.delete(f"/events/{event_id}")

    assert response.status_code == 204

    get_response = event_client.get(f"/events/{event_id}")
    assert get_response.status_code == 404


def test_delete_event_not_found(event_client):
    response = event_client.delete("/events/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found."


