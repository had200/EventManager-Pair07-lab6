
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models import Event, Participant, Registration
from app.routers.registrations import (
    register_participant,
    list_event_participants,
)


def setup_registration_queries(db, event, participant, existing=None):
    event_query = MagicMock()
    participant_query = MagicMock()
    registration_query = MagicMock()

    event_query.filter.return_value.first.return_value = event
    participant_query.filter.return_value.first.return_value = participant
    registration_query.filter.return_value.first.return_value = existing

    db.query.side_effect = [
        event_query,
        participant_query,
        registration_query,
    ]


def test_register_participant_success():
    db = MagicMock()
    event = SimpleNamespace(capacity=5, registrations=[])
    participant = SimpleNamespace(id=2)

    setup_registration_queries(db, event, participant)

    result = register_participant(
        event_id=1,
        participant_id=2,
        db=db,
    )

    assert isinstance(result, Registration)
    assert result.event_id == 1
    assert result.participant_id == 2
    db.add.assert_called_once_with(result)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)


def test_register_participant_event_not_found():
    db = MagicMock()
    event_query = MagicMock()
    event_query.filter.return_value.first.return_value = None
    db.query.return_value = event_query

    with pytest.raises(HTTPException) as exc:
        register_participant(event_id=999, participant_id=2, db=db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Event not found."
    db.add.assert_not_called()


def test_register_participant_participant_not_found():
    db = MagicMock()
    event = SimpleNamespace(capacity=5, registrations=[])
    setup_registration_queries(db, event, None)

    with pytest.raises(HTTPException) as exc:
        register_participant(event_id=1, participant_id=999, db=db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Participant not found."
    db.add.assert_not_called()


def test_register_participant_duplicate():
    db = MagicMock()
    event = SimpleNamespace(capacity=5, registrations=[])
    participant = SimpleNamespace(id=2)
    existing = SimpleNamespace(id=10)

    setup_registration_queries(db, event, participant, existing)

    with pytest.raises(HTTPException) as exc:
        register_participant(event_id=1, participant_id=2, db=db)

    assert exc.value.status_code == 409
    assert exc.value.detail == "Participant is already registered."
    db.add.assert_not_called()


def test_register_participant_capacity_reached():
    db = MagicMock()
    event = SimpleNamespace(
        capacity=1,
        registrations=[SimpleNamespace()],
    )
    participant = SimpleNamespace(id=2)

    setup_registration_queries(db, event, participant)

    with pytest.raises(HTTPException) as exc:
        register_participant(event_id=1, participant_id=2, db=db)

    assert exc.value.status_code == 409
    assert exc.value.detail == "Event capacity has been reached."
    db.add.assert_not_called()


def test_list_event_participants_success():
    db = MagicMock()

    participant1 = SimpleNamespace(
        id=1, name="Alice", email="alice@example.com"
    )
    participant2 = SimpleNamespace(
        id=2, name="Bob", email="bob@example.com"
    )

    event = SimpleNamespace(
        registrations=[
            SimpleNamespace(participant=participant1),
            SimpleNamespace(participant=participant2),
        ]
    )

    db.query.return_value.filter.return_value.first.return_value = event

    result = list_event_participants(event_id=1, db=db)

    assert result == [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
    ]


def test_list_event_participants_event_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        list_event_participants(event_id=999, db=db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Event not found."


