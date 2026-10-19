
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models import Event as EventModel
from app.routers import events as event_routes
from app.schemas import EventCreate, EventUpdate


def make_db(event=None, events=None):
    """Create a mocked database session without a real database."""
    db = MagicMock()
    query = MagicMock()

    db.query.return_value = query
    query.filter.return_value = query
    query.order_by.return_value = query
    query.first.return_value = event
    query.all.return_value = events if events is not None else []

    return db


def make_event_data(event_date=None):
    """Return valid data for creating or updating an event."""
    return {
        "title": "Cybersecurity Workshop",
        "description": "A security event",
        "date": event_date or date.today() + timedelta(days=10),
        "location": "Constantine",
        "capacity": 50,
    }


# ======================== CREATE EVENT ========================

def test_create_event_success():
    db = make_db()
    event_data = EventCreate(**make_event_data())

    result = event_routes.create_event(event_data, db)

    assert result.title == "Cybersecurity Workshop"
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_create_event_in_the_past_raises_400():
    db = make_db()
    event_data = EventCreate(
        **make_event_data(date.today() - timedelta(days=1))
    )

    with pytest.raises(HTTPException) as exc:
        event_routes.create_event(event_data, db)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Event date cannot be in the past."
    db.add.assert_not_called()


# ======================== LIST EVENTS ========================


def test_list_events_without_filters():
    expected_events = [MagicMock(), MagicMock()]
    db = make_db(events=expected_events)

    result = event_routes.list_events(
        search=None,
        location=None,
        db=db,
    )

    assert result == expected_events
    db.query.assert_called_once_with(EventModel)
    db.query.return_value.order_by.assert_called_once()



def test_list_events_with_search_and_location():
    expected_events = [MagicMock()]
    db = make_db(events=expected_events)

    result = event_routes.list_events(
        search="  cyber  ",
        location="Constantine",
        db=db,
    )

    assert result == expected_events
    assert db.query.return_value.filter.call_count == 2
    db.query.return_value.order_by.assert_called_once()


def test_list_events_with_search_only():
    db = make_db(events=[])

    result = event_routes.list_events(
        search="python",
        location=None,
        db=db,
    )

    assert result == []
    db.query.return_value.filter.assert_called_once()


def test_list_events_with_location_only():
    db = make_db(events=[])

    result = event_routes.list_events(
        search=None,
        location="Paris",
        db=db,
    )

    assert result == []
    db.query.return_value.filter.assert_called_once()


# ======================== GET EVENT ========================

def test_get_event_success():
    expected_event = SimpleNamespace(id=1, title="Workshop")
    db = make_db(event=expected_event)

    result = event_routes.get_event(1, db)

    assert result is expected_event


def test_get_event_not_found_raises_404():
    db = make_db(event=None)

    with pytest.raises(HTTPException) as exc:
        event_routes.get_event(999, db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Event not found."


# ======================== UPDATE EVENT ========================

def test_update_event_success():
    existing_event = SimpleNamespace(
        id=1,
        title="Old title",
        description="Old description",
        date=date.today() + timedelta(days=5),
        location="Paris",
        capacity=10,
    )
    db = make_db(event=existing_event)
    update_data = EventUpdate(**make_event_data())

    result = event_routes.update_event(1, update_data, db)

    assert result.title == "Cybersecurity Workshop"
    assert result.location == "Constantine"
    assert result.capacity == 50
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(existing_event)


def test_update_event_not_found_raises_404():
    db = make_db(event=None)
    update_data = EventUpdate(**make_event_data())

    with pytest.raises(HTTPException) as exc:
        event_routes.update_event(999, update_data, db)

    assert exc.value.status_code == 404


def test_update_event_with_past_date_raises_400():
    existing_event = SimpleNamespace(id=1, title="Workshop")
    db = make_db(event=existing_event)
    update_data = EventUpdate(
        **make_event_data(date.today() - timedelta(days=1))
    )

    with pytest.raises(HTTPException) as exc:
        event_routes.update_event(1, update_data, db)

    assert exc.value.status_code == 400
    db.commit.assert_not_called()


# ======================== DELETE EVENT ========================

def test_delete_event_success():
    existing_event = SimpleNamespace(id=1, title="Workshop")
    db = make_db(event=existing_event)

    result = event_routes.delete_event(1, db)

    assert result is None
    db.delete.assert_called_once_with(existing_event)
    db.commit.assert_called_once()


def test_delete_event_not_found_raises_404():
    db = make_db(event=None)

    with pytest.raises(HTTPException) as exc:
        event_routes.delete_event(999, db)

    assert exc.value.status_code == 404
    db.delete.assert_not_called()
