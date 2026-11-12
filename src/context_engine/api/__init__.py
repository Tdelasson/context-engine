"""HTTP adapter over the core application facade. Requires the ``api`` extra."""

from context_engine.api.app import API_PREFIX, create_app

__all__ = ["API_PREFIX", "create_app"]
