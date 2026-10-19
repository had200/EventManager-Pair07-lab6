
from unittest.mock import MagicMock

from app import database


def test_get_db_yields_session_and_closes_it(monkeypatch):
    fake_db = MagicMock()

    monkeypatch.setattr(
        database,
        "SessionLocal",
        lambda: fake_db,
    )

    db_generator = database.get_db()

    # The generator should yield the session.
    yielded_db = next(db_generator)
    assert yielded_db is fake_db

    # Closing the generator should execute the finally block.
    db_generator.close()
    fake_db.close.assert_called_once()
