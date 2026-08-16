"""Model gateway abstractions and typed contracts."""

from context_engine.models.errors import (
    ModelGatewayError,
    ModelGatewayExecutionError,
    ModelGatewayRequestError,
)
from context_engine.models.gateway import (
    ModelFinishReason,
    ModelGateway,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelRole,
    ModelUsage,
    normalize_messages,
)
from context_engine.models.ollama import OllamaModelGateway

__all__ = [
    "ModelFinishReason",
    "ModelGateway",
    "ModelGatewayError",
    "ModelGatewayExecutionError",
    "ModelGatewayRequestError",
    "ModelMessage",
    "ModelRequest",
    "ModelResponse",
    "ModelRole",
    "ModelUsage",
    "OllamaModelGateway",
    "normalize_messages",
]
