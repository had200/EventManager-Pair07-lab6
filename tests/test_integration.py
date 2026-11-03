
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db


# Base de données temporaire réservée aux tests
SQLALCHEMY_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=test_engine)


def future_date():
    return (date.today() + timedelta(days=30)).isoformat()


def test_create_and_fetch_event_integration(client):
    # Créer un événement
    response = client.post(
        "/events/",
        json={
            "title": "DevOps Integration Conference",
            "description": "Integration testing",
            "date": future_date(),
            "location": "Constantine",
            "capacity": 200
        }
    )

    assert response.status_code == 201

    event_id = response.json()["id"]

    # Consulter l'événement créé
    get_response = client.get(f"/events/{event_id}")

    assert get_response.status_code == 200
    assert get_response.json()["title"] == "DevOps Integration Conference"


def test_register_participant_to_event_integration(client):
    # Créer un événement
    event_response = client.post(
        "/events/",
        json={
            "title": "Cybersecurity Workshop",
            "description": "DevOps integration test",
            "date": future_date(),
            "location": "NTIC",
            "capacity": 50
        }
    )

    assert event_response.status_code == 201
    event_id = event_response.json()["id"]

    # Créer un participant
    participant_response = client.post(
        "/participants/",
        json={
            "name": "Alice Dev",
            "email": "alice.integration@example.com"
        }
    )

    assert participant_response.status_code == 201
    participant_id = participant_response.json()["id"]

    # Inscrire le participant à l'événement
    registration_response = client.post(
        f"/events/{event_id}/register/{participant_id}"
    )

    assert registration_response.status_code == 201

    # Vérifier la liste des participants de l'événement
    list_response = client.get(
        f"/events/{event_id}/participants"
    )

    assert list_response.status_code == 200
    assert any(
        participant["id"] == participant_id
        for participant in list_response.json()
    )


def test_register_nonexistent_event_returns_404(client):
    response = client.post("/events/9999/register/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found."
