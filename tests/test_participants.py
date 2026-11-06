
import pytest
from datetime import date
from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import Event, Participant
from app.routers.participants import router as participants_router
from app.routers.registrations import router as registrations_router
from app.schemas import Participant as ParticipantSchema
from app.services import (
    has_available_capacity,
    check_duplicate_registration,
)


# ==================================================
# Fixture : application et base de données de test
# ==================================================

@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    test_app = FastAPI()
    test_app.include_router(participants_router)
    test_app.include_router(registrations_router)
    test_app.state.TestingSessionLocal = TestingSessionLocal

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as test_client:
        yield test_client

    test_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# ==================================================
# Tests du schéma Participant
# ==================================================

def test_participant_valid_data():
    participant = ParticipantSchema(
        id=1,
        name="Alice Martin",
        email="alice@example.com",
    )

    assert participant.id == 1
    assert participant.name == "Alice Martin"
    assert participant.email == "alice@example.com"


def test_participant_minimum_name_length():
    participant = ParticipantSchema(
        id=2,
        name="Al",
        email="alice@example.com",
    )

    assert participant.name == "Al"


def test_participant_name_too_short():
    with pytest.raises(ValidationError):
        ParticipantSchema(
            id=3,
            name="A",
            email="alice@example.com",
        )


def test_participant_name_too_long():
    with pytest.raises(ValidationError):
        ParticipantSchema(
            id=4,
            name="A" * 101,
            email="alice@example.com",
        )


def test_participant_invalid_email():
    with pytest.raises(ValidationError):
        ParticipantSchema(
            id=5,
            name="Alice Martin",
            email="not-an-email",
        )


def test_participant_missing_name():
    with pytest.raises(ValidationError):
        ParticipantSchema(
            id=6,
            email="alice@example.com",
        )


# ==================================================
# Tests des services
# ==================================================

def test_duplicate_registration_raises_error():
    with pytest.raises(
        ValueError,
        match="Participant 1 is already registered.",
    ):
        check_duplicate_registration([1, 2, 3], 1)


def test_new_registration_does_not_raise_error():
    result = check_duplicate_registration([1, 2, 3], 4)
    assert result is None


def test_registration_with_empty_list():
    result = check_duplicate_registration([], 1)
    assert result is None


def test_has_available_capacity():
    assert has_available_capacity(5, 10) is True


def test_capacity_is_full():
    assert has_available_capacity(10, 10) is False


def test_capacity_is_exceeded():
    assert has_available_capacity(11, 10) is False


# ==================================================
# Tests API : création de participants
# ==================================================

def test_create_participant(client):
    response = client.post(
        "/participants/",
        json={
            "name": "Alice Martin",
            "email": "alice@example.com",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice Martin"
    assert data["email"] == "alice@example.com"
    assert "id" in data


def test_create_participant_duplicate_email(client):
    payload = {
        "name": "Alice Martin",
        "email": "alice@example.com",
    }

    first_response = client.post("/participants/", json=payload)
    assert first_response.status_code == 201

    second_response = client.post(
        "/participants/",
        json={
            "name": "Alice Dupont",
            "email": "alice@example.com",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Email is already registered."
    )


def test_create_participant_invalid_email(client):
    response = client.post(
        "/participants/",
        json={
            "name": "Alice Martin",
            "email": "invalid-email",
        },
    )

    assert response.status_code == 422


def test_create_participant_missing_name(client):
    response = client.post(
        "/participants/",
        json={"email": "alice@example.com"},
    )

    assert response.status_code == 422


# ==================================================
# Tests API : liste des participants
# ==================================================

def test_list_participants_empty(client):
    response = client.get("/participants/")

    assert response.status_code == 200
    assert response.json() == []


def test_list_participants(client):
    client.post(
        "/participants/",
        json={
            "name": "Zoe Martin",
            "email": "zoe@example.com",
        },
    )

    client.post(
        "/participants/",
        json={
            "name": "Alice Martin",
            "email": "alice@example.com",
        },
    )

    response = client.get("/participants/")

    assert response.status_code == 200
    assert [p["name"] for p in response.json()] == [
        "Alice Martin",
        "Zoe Martin",
    ]


# ==================================================
# Tests API : récupération d'un participant
# ==================================================

def test_get_participant_not_found(client):
    response = client.get("/participants/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found."


def test_get_participant_success(client):
    created = client.post(
        "/participants/",
        json={
            "name": "Alice Martin",
            "email": "alice@example.com",
        },
    )

    assert created.status_code == 201
    participant_id = created.json()["id"]

    response = client.get(f"/participants/{participant_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Alice Martin"
    assert response.json()["email"] == "alice@example.com"


# ==================================================
# Tests API : suppression d'un participant
# ==================================================

def test_delete_participant_not_found(client):
    response = client.delete("/participants/999")

    assert response.status_code == 404


def test_delete_participant_success(client):
    created = client.post(
        "/participants/",
        json={
            "name": "Alice Martin",
            "email": "alice@example.com",
        },
    )

    assert created.status_code == 201
    participant_id = created.json()["id"]

    response = client.delete(f"/participants/{participant_id}")

    assert response.status_code == 204

    get_response = client.get(f"/participants/{participant_id}")
    assert get_response.status_code == 404


# ==================================================
# Fixtures pour les tests d'inscriptions
# ==================================================

@pytest.fixture
def sample_event(client):
    SessionLocal = client.app.state.TestingSessionLocal
    db = SessionLocal()

    try:
        event = Event(
            title="Python Workshop",
            description="Workshop de Python",
            date=date(2026, 11, 15),
            location="Constantine",
            capacity=2,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        event_id = event.id
    finally:
        db.close()

    return event_id


@pytest.fixture
def sample_participant(client):
    response = client.post(
        "/participants/",
        json={
            "name": "Alice Martin",
            "email": "alice@example.com",
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


# ==================================================
# Tests API : inscription à un événement
# ==================================================

def test_register_participant_success(
    client, sample_event, sample_participant
):
    response = client.post(
        f"/events/{sample_event}/register/{sample_participant}"
    )

    assert response.status_code == 201


def test_register_event_not_found(client, sample_participant):
    response = client.post(
        f"/events/999/register/{sample_participant}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found."


def test_register_participant_not_found(client, sample_event):
    response = client.post(
        f"/events/{sample_event}/register/999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found."


def test_register_duplicate_participant(
    client, sample_event, sample_participant
):
    url = (
        f"/events/{sample_event}/register/"
        f"{sample_participant}"
    )

    first_response = client.post(url)
    assert first_response.status_code == 201

    second_response = client.post(url)

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Participant is already registered."
    )


def test_register_when_event_is_full(client):
    SessionLocal = client.app.state.TestingSessionLocal
    db = SessionLocal()

    try:
        event = Event(
            title="Small Workshop",
            description="Event with one place",
            date=date(2026, 11, 15),
            location="Constantine",
            capacity=1,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        event_id = event.id
    finally:
        db.close()

    first = client.post(
        "/participants/",
        json={
            "name": "Alice Martin",
            "email": "alice@example.com",
        },
    )

    second = client.post(
        "/participants/",
        json={
            "name": "Bob Martin",
            "email": "bob@example.com",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201

    first_id = first.json()["id"]
    second_id = second.json()["id"]

    response1 = client.post(
        f"/events/{event_id}/register/{first_id}"
    )
    assert response1.status_code == 201

    response2 = client.post(
        f"/events/{event_id}/register/{second_id}"
    )

    assert response2.status_code == 409
    assert response2.json()["detail"] == (
        "Event capacity has been reached."
    )


# ==================================================
# Tests API : liste des participants d'un événement
# ==================================================

def test_list_event_participants(
    client, sample_event, sample_participant
):
    registration_response = client.post(
        f"/events/{sample_event}/register/{sample_participant}"
    )
    assert registration_response.status_code == 201

    response = client.get(
        f"/events/{sample_event}/participants"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Alice Martin"
    assert response.json()[0]["email"] == "alice@example.com"


def test_list_participants_event_not_found(client):
    response = client.get("/events/999/participants")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found."


def test_list_event_participants_empty(client, sample_event):
    response = client.get(
        f"/events/{sample_event}/participants"
    )

    assert response.status_code == 200
    assert response.json() == []

def test_main_app_import_and_root():
    from fastapi import FastAPI
    from app.routers.participants import router as participants_router
    from app.routers.registrations import router as registrations_router

    test_app = FastAPI()
    test_app.include_router(participants_router)
    test_app.include_router(registrations_router)

    with TestClient(test_app) as test_client:
        response = test_client.get("/")

        assert response.status_code == 404

def test_get_db_closes_session(monkeypatch):
    from app import database

    class FakeSession:
        closed = False

        def close(self):
            self.closed = True

    session = FakeSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)

    db_generator = database.get_db()

    assert next(db_generator) is session
    assert session.closed is False

    db_generator.close()

    assert session.closed is True
