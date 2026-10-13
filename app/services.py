# app/services.py
from app.schemas import Event


# ============ Filter logic (Student A — Lab 2) ============

def filter_events_by_location(events: list[Event], location: str) -> list[Event]:
    """Filtre par location (case-insensitive), sur une liste en mémoire."""
    return [e for e in events if location.lower() in e.location.lower()]


def filter_events_by_title(events: list[Event], title: str) -> list[Event]:
    """Filtre par titre (case-insensitive), sur une liste en mémoire."""
    return [e for e in events if title.lower() in e.title.lower()]


# ============ Registration logic (Student B — Lab 2) ============

def has_available_capacity(current_count: int, max_capacity: int) -> bool:
    return current_count < max_capacity


def check_duplicate_registration(registered_ids: list[int], new_id: int) -> None:
    if new_id in registered_ids:
        raise ValueError(f"Participant {new_id} is already registered.")