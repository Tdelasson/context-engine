"""Workbench names for the core application settings.

Settings moved to ``context_engine.core.settings``; these aliases keep the Streamlit
workbench and its tests working until it is removed.
"""

from context_engine.core.settings import (
    ApplicationConfigurationError as WorkbenchConfigurationError,
)
from context_engine.core.settings import ApplicationSettings as WorkbenchSettings

__all__ = ["WorkbenchConfigurationError", "WorkbenchSettings"]
