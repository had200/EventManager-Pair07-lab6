import pytest
from pydantic import ValidationError

# À adapter selon l'emplacement réel de ces éléments dans votre projet
from app.schemas import Participant
from app.services import (
    has_available_capacity,
    check_duplicate_registration,
)


# ==========================================
# 1. HAPPY PATH TESTS
# ==========================================

def test_valid_participant_creation(sample_participant_dict):
    """Test the creation of a valid participant."""
    participant = Participant(**sample_participant_dict)

    assert participant.name == sample_participant_dict["name"]
    assert participant.email == sample_participant_dict["email"]


def test_available_capacity():
    """Test that capacity is available when seats remain."""
    assert has_available_capacity(3, 10) is True


# ==========================================
# 2. BOUNDARY VALUE TESTS
# ==========================================

def test_capacity_one_place_remaining():
    """Test when only one place remains."""
    assert has_available_capacity(9, 10) is True


def test_capacity_exactly_full():
    """Test when current count equals maximum capacity."""
    assert has_available_capacity(10, 10) is False


def test_capacity_exceeded():
    """Test when current count exceeds maximum capacity."""
    assert has_available_capacity(11, 10) is False


# ==========================================
# 3. NEGATIVE TESTS
# ==========================================

def test_invalid_email(sample_participant_dict):
    """Test that an invalid email raises ValidationError."""
    data = sample_participant_dict.copy()
    data["email"] = "invalid-email"

    with pytest.raises(ValidationError):
        Participant(**data)


def test_short_participant_name(sample_participant_dict):
    """Test that a name shorter than 2 characters is rejected."""
    data = sample_participant_dict.copy()
    data["name"] = "A"

    with pytest.raises(ValidationError):
        Participant(**data)


def test_duplicate_registration():
    """Test that registering an existing ID raises ValueError."""
    registered_ids = [1, 2, 3]

    with pytest.raises(ValueError):
        check_duplicate_registration(registered_ids, 2)


# ==========================================
# 4. ADDITIONAL HAPPY PATH TEST
# ==========================================

def test_registration_with_new_id():
    """Test registration with an ID that does not already exist."""
    registered_ids = [1, 2, 3]

    check_duplicate_registration(registered_ids, 4)
