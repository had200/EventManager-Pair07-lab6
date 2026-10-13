from datetime import date
import pytest
from pydantic import ValidationError

from app.schemas import Event
from app.services import filter_events_by_location, filter_events_by_title


# ============================ HAPPY PATH ============================

def test_valid_event_instantiation(sample_event_dict):
    event = Event(**sample_event_dict)
    assert event.title == "Python Conference"
    assert event.capacity == 100


def test_filter_by_location_case_insensitive(prepopulated_event_store):
    results = filter_events_by_location(prepopulated_event_store, "paris")
    assert len(results) == 2
    assert all(e.location.lower() == "paris" for e in results)


def test_filter_by_title_case_insensitive(prepopulated_event_store):
    results = filter_events_by_title(prepopulated_event_store, "python")
    assert len(results) == 1
    assert results[0].title.lower() == "python conf"


# ========================= BOUNDARY VALUES =========================

def test_capacity_minimum_boundary():
    event = Event(id=1, title="Test", date=date(2025, 1, 1),
                  location="Paris", capacity=1)
    assert event.capacity == 1


def test_capacity_maximum_boundary():
    event = Event(id=1, title="Test", date=date(2025, 1, 1),
                  location="Paris", capacity=10000)
    assert event.capacity == 10000


def test_title_minimum_length_boundary():
    event = Event(id=1, title="abc", date=date(2025, 1, 1),
                  location="Paris", capacity=10)
    assert len(event.title) == 3


# ============================ NEGATIVE =============================

def test_short_title_raises_validation_error():
    with pytest.raises(ValidationError):
        Event(id=1, title="ab", date=date(2025, 1, 1),
              location="Paris", capacity=10)


def test_zero_capacity_raises_validation_error():
    with pytest.raises(ValidationError):
        Event(id=1, title="Test", date=date(2025, 1, 1),
              location="Paris", capacity=0)


def test_negative_capacity_raises_validation_error():
    with pytest.raises(ValidationError):
        Event(id=1, title="Test", date=date(2025, 1, 1),
              location="Paris", capacity=-5)