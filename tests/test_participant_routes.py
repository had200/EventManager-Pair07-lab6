
import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from fastapi import HTTPException

from app.models import Participant
from app.routers.participants import (
    list_participants,
    get_participant,
    delete_participant,
    create_participant,
)
from app.schemas import ParticipantCreate


def test_list_participants():
    db = MagicMock()
    participants = [MagicMock(), MagicMock()]
    db.query.return_value.order_by.return_value.all.return_value = participants

    result = list_participants(db=db)

    assert result == participants
    db.query.assert_called_once_with(Participant)


def test_get_participant_success():
    db = MagicMock()
    participant = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = participant

    result = get_participant(participant_id=1, db=db)

    assert result == participant


def test_get_participant_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        get_participant(participant_id=999, db=db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Participant not found."


def test_delete_participant_success():
    db = MagicMock()
    participant = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = participant

    delete_participant(participant_id=1, db=db)

    db.delete.assert_called_once_with(participant)
    db.commit.assert_called_once()


def test_delete_participant_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        delete_participant(participant_id=999, db=db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Participant not found."
    db.delete.assert_not_called()
    db.commit.assert_not_called()


def test_create_participant_success():
    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value = query
    query.first.return_value = None

    participant_data = ParticipantCreate(
        name="Alice Smith",
        email="alice@example.com",
    )

    result = create_participant(participant_data, db)

    assert result.name == "Alice Smith"
    assert str(result.email) == "alice@example.com"
    db.add.assert_called_once_with(result)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)


def test_create_participant_duplicate_email_raises_409():
    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value = query
    query.first.return_value = SimpleNamespace(
        email="alice@example.com"
    )

    participant_data = ParticipantCreate(
        name="Alice Smith",
        email="alice@example.com",
    )

    with pytest.raises(HTTPException) as exc:
        create_participant(participant_data, db)

    assert exc.value.status_code == 409
    assert exc.value.detail == "Email is already registered."
    db.add.assert_not_called()
    db.commit.assert_not_called()
