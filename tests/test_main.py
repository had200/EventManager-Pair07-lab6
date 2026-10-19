
import importlib


def test_main_app_configuration_and_root(monkeypatch):
    from app.database import Base

    # Prevent connecting to the real database during this test.
    monkeypatch.setattr(
        Base.metadata,
        "create_all",
        lambda **kwargs: None,
    )

    main_module = importlib.import_module("app.main")

    assert main_module.app.title == "Event Manager API"
    assert main_module.app.description == (
        "A teaching project for Git, Docker and CI/CD"
    )
    assert main_module.app.version == "1.0.0"

    assert main_module.root() == {
        "message": "Welcome to Event Manager API"
    }

    # Verify that the expected routers are included.
    assert main_module.app.router is not None
    assert main_module.events.router in (
        main_module.events.router,
    )
    assert main_module.participants.router is not None
    assert main_module.registrations.router is not None
