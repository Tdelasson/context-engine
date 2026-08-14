"""Explicit model gateway error boundaries."""


class ModelGatewayError(Exception):
    """Base exception for model gateway failures."""


class ModelGatewayRequestError(ModelGatewayError, ValueError):
    """Raised when a model request is invalid for gateway processing."""


class ModelGatewayExecutionError(ModelGatewayError):
    """Raised when model generation fails during provider execution."""
