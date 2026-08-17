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
    ModelToolCall,
    ModelToolDefinition,
    ModelUsage,
    normalize_messages,
    normalize_model_tools,
    normalize_tool_call_arguments,
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
    "ModelToolCall",
    "ModelToolDefinition",
    "ModelUsage",
    "OllamaModelGateway",
    "normalize_messages",
    "normalize_model_tools",
    "normalize_tool_call_arguments",
]
