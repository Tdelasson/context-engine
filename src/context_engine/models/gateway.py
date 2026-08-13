"""Provider-independent model gateway contracts."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelRequest:
    """Input required for a single model invocation."""

    prompt: str
    model: str


@dataclass(frozen=True)
class ModelResponse:
    """Provider-independent result returned by a model invocation."""

    text: str
    model: str


class ModelGatewayError(Exception):
    """Base error raised when a model gateway operation fails."""


class ModelGateway(ABC):
    """Provider-independent interface for model inference."""

    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a model response for a validated request."""
        raise NotImplementedError


class MockModelGateway(ModelGateway):
    """Deterministic model gateway implementation for tests."""

    def __init__(self, response: ModelResponse | None = None) -> None:
        self._response = response

    def generate(self, request: ModelRequest) -> ModelResponse:
        if not request.prompt:
            raise ModelGatewayError("Model request prompt must not be empty")
        if self._response is not None:
            return self._response
        return ModelResponse(text=request.prompt, model=request.model)
