"""Ollama-backed implementation of the provider-independent model gateway."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from context_engine.models.errors import ModelGatewayExecutionError, ModelGatewayRequestError
from context_engine.models.gateway import (
    ModelFinishReason,
    ModelGateway,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)


@dataclass(frozen=True, slots=True)
class _OllamaGatewayConfig:
    base_url: str
    model_name: str | None
    timeout_seconds: float


class OllamaModelGateway(ModelGateway):
    """Translate provider-independent model requests into Ollama chat API calls."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        model_name: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        normalized_base_url = base_url.rstrip("/")
        if not normalized_base_url:
            raise ValueError("base_url must not be empty.")
        if model_name is not None and not model_name.strip():
            raise ValueError("model_name must not be empty when provided.")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

        self._config = _OllamaGatewayConfig(
            base_url=normalized_base_url,
            model_name=model_name,
            timeout_seconds=timeout_seconds,
        )

    def generate(self, request: ModelRequest) -> ModelResponse:
        if not request.messages:
            raise ModelGatewayRequestError("Model request must include at least one message.")

        provider_model_name = self._config.model_name or request.model_id
        payload = self._build_payload(request=request, provider_model_name=provider_model_name)
        response_payload = self._execute_chat_request(payload)
        return self._translate_response(
            payload=response_payload,
            requested_model_id=request.model_id,
        )

    def _build_payload(self, *, request: ModelRequest, provider_model_name: str) -> dict[str, Any]:
        messages = [
            {"role": message.role.value, "content": message.content} for message in request.messages
        ]
        payload: dict[str, Any] = {
            "model": provider_model_name,
            "messages": messages,
            "stream": False,
        }

        options: dict[str, Any] = {}
        if request.max_output_tokens is not None:
            options["num_predict"] = request.max_output_tokens
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if options:
            payload["options"] = options

        return payload

    def _execute_chat_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        endpoint = f"{self._config.base_url}/api/chat"
        serialized_payload = json.dumps(payload).encode("utf-8")
        request = Request(
            endpoint,
            data=serialized_payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        try:
            with urlopen(request, timeout=self._config.timeout_seconds) as response:
                response_bytes = response.read()
        except HTTPError as exc:
            error_body = self._read_error_body(exc)
            raise ModelGatewayExecutionError(
                f"Ollama request failed with HTTP status {exc.code}: {error_body}"
            ) from exc
        except (URLError, TimeoutError) as exc:
            raise ModelGatewayExecutionError(
                "Ollama request failed due to connection or timeout error."
            ) from exc

        try:
            response_payload = json.loads(response_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ModelGatewayExecutionError("Ollama response was not valid JSON.") from exc

        if not isinstance(response_payload, dict):
            raise ModelGatewayExecutionError("Ollama response payload must be a JSON object.")

        return response_payload

    def _translate_response(
        self,
        *,
        payload: dict[str, Any],
        requested_model_id: str,
    ) -> ModelResponse:
        message_payload = payload.get("message")
        if not isinstance(message_payload, dict):
            raise ModelGatewayExecutionError("Ollama response did not include a message object.")

        output_text = message_payload.get("content")
        if not isinstance(output_text, str):
            raise ModelGatewayExecutionError("Ollama response message content must be a string.")

        usage = self._translate_usage(payload)
        return ModelResponse(
            model_id=requested_model_id,
            output_text=output_text,
            finish_reason=self._translate_finish_reason(payload.get("done_reason")),
            usage=usage,
        )

    def _translate_usage(self, payload: dict[str, Any]) -> ModelUsage | None:
        input_tokens = self._validate_optional_int(
            payload.get("prompt_eval_count"),
            "prompt_eval_count",
        )
        output_tokens = self._validate_optional_int(payload.get("eval_count"), "eval_count")
        if input_tokens is None and output_tokens is None:
            return None
        return ModelUsage(input_tokens=input_tokens, output_tokens=output_tokens)

    def _translate_finish_reason(self, done_reason: object) -> ModelFinishReason:
        if done_reason == "stop":
            return ModelFinishReason.STOP
        if done_reason in {"length", "max_tokens"}:
            return ModelFinishReason.LENGTH
        return ModelFinishReason.OTHER

    def _validate_optional_int(self, value: object, field_name: str) -> int | None:
        if value is None:
            return None
        if not isinstance(value, int):
            raise ModelGatewayExecutionError(
                f"Ollama response field '{field_name}' must be an integer when provided."
            )
        return value

    def _read_error_body(self, error: HTTPError) -> str:
        try:
            raw_error_body = error.read().decode("utf-8", errors="replace").strip()
        except OSError:
            return "<unable to read error body>"
        return raw_error_body or "<empty>"
