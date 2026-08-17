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
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelRole,
    ModelToolCall,
    ModelToolDefinition,
    ModelToolResultStatus,
    ModelUsage,
    normalize_tool_call_arguments,
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
        messages = [self._translate_message(message) for message in request.messages]
        payload: dict[str, Any] = {
            "model": provider_model_name,
            "messages": messages,
            "stream": False,
        }
        if request.tools:
            payload["tools"] = self._translate_tools(request.tools)

        options: dict[str, Any] = {}
        if request.max_output_tokens is not None:
            options["num_predict"] = request.max_output_tokens
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if options:
            payload["options"] = options

        return payload

    def _translate_message(self, message: ModelMessage) -> dict[str, object]:
        translated: dict[str, object] = {"role": message.role.value, "content": message.content}
        if message.role is ModelRole.ASSISTANT and message.tool_call is not None:
            function_payload: dict[str, object] = {
                "name": message.tool_call.tool_name,
                "arguments": message.tool_call.arguments_as_mapping(),
            }
            if message.tool_call.tool_call_id is not None:
                function_payload["id"] = message.tool_call.tool_call_id
            translated["tool_calls"] = [{"function": function_payload}]
            return translated

        if message.role is ModelRole.TOOL and message.tool_result is not None:
            tool_content: dict[str, object] = {
                "tool_name": message.tool_result.tool_name,
                "status": message.tool_result.status.value,
            }
            if message.tool_result.tool_call_id is not None:
                tool_content["tool_call_id"] = message.tool_result.tool_call_id
            if message.tool_result.status is ModelToolResultStatus.SUCCESS:
                tool_content["output"] = message.tool_result.output_as_mapping()
            else:
                tool_content["error"] = {
                    "error_type": message.tool_result.error_type,
                    "message": message.tool_result.error_message,
                }
            translated["content"] = json.dumps(tool_content, sort_keys=True)
            translated["name"] = message.tool_result.tool_name
        return translated

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

        tool_call = self._translate_tool_call(message_payload)
        output_text = message_payload.get("content")
        if output_text is None and tool_call is not None:
            output_text = ""
        if not isinstance(output_text, str):
            raise ModelGatewayExecutionError("Ollama response message content must be a string.")

        usage = self._translate_usage(payload)
        return ModelResponse(
            model_id=requested_model_id,
            output_text=output_text,
            finish_reason=self._translate_finish_reason(payload.get("done_reason")),
            tool_call=tool_call,
            usage=usage,
        )

    def _translate_tools(self, tools: tuple[ModelToolDefinition, ...]) -> list[dict[str, object]]:
        translated: list[dict[str, object]] = []
        for tool in tools:
            translated.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": dict(tool.input_schema),
                    },
                }
            )
        return translated

    def _translate_tool_call(self, message_payload: dict[str, Any]) -> ModelToolCall | None:
        tool_calls_payload = message_payload.get("tool_calls")
        if tool_calls_payload is None:
            return None
        if not isinstance(tool_calls_payload, list):
            raise ModelGatewayExecutionError("Ollama response tool_calls must be a list.")
        if len(tool_calls_payload) != 1:
            raise ModelGatewayExecutionError(
                "Ollama response must contain exactly one tool call when tool_calls is present."
            )

        tool_call_payload = tool_calls_payload[0]
        if not isinstance(tool_call_payload, dict):
            raise ModelGatewayExecutionError("Ollama tool call entry must be an object.")

        function_payload = tool_call_payload.get("function")
        if not isinstance(function_payload, dict):
            raise ModelGatewayExecutionError("Ollama tool call function payload must be an object.")

        tool_name = function_payload.get("name")
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ModelGatewayExecutionError(
                "Ollama tool call function name must be a non-empty string."
            )

        raw_arguments = function_payload.get("arguments")
        arguments = self._parse_tool_call_arguments(raw_arguments)
        raw_tool_call_id = function_payload.get("id")
        if raw_tool_call_id is not None and not isinstance(raw_tool_call_id, str):
            raise ModelGatewayExecutionError("Ollama tool call id must be a string when provided.")
        return ModelToolCall(
            tool_name=tool_name,
            arguments=normalize_tool_call_arguments(arguments),
            tool_call_id=raw_tool_call_id,
        )

    def _parse_tool_call_arguments(self, raw_arguments: object) -> dict[str, object]:
        if isinstance(raw_arguments, str):
            try:
                parsed_arguments = json.loads(raw_arguments)
            except json.JSONDecodeError as exc:
                raise ModelGatewayExecutionError(
                    "Ollama tool call arguments string must be valid JSON object."
                ) from exc
            raw_arguments = parsed_arguments
        if raw_arguments is None:
            return {}
        if not isinstance(raw_arguments, dict):
            raise ModelGatewayExecutionError("Ollama tool call arguments must be an object.")
        if not all(isinstance(key, str) for key in raw_arguments):
            raise ModelGatewayExecutionError("Ollama tool call arguments must use string keys.")
        return dict(raw_arguments)

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
