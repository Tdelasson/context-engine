import io
import json
from http.client import HTTPMessage
from urllib.error import HTTPError, URLError

import pytest

from context_engine.models import (
    ModelFinishReason,
    ModelGatewayExecutionError,
    ModelGatewayRequestError,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelRole,
    ModelToolDefinition,
    ModelUsage,
    OllamaModelGateway,
    normalize_messages,
    normalize_model_tools,
)


class _FakeHTTPResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def test_ollama_gateway_translates_request_and_success_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_request_payload: dict[str, object] = {}
    captured_url: str = ""
    captured_timeout: float = 0.0

    def fake_urlopen(request: object, timeout: float) -> _FakeHTTPResponse:
        nonlocal captured_request_payload, captured_url, captured_timeout
        data = getattr(request, "data")
        full_url = getattr(request, "full_url")
        captured_request_payload = json.loads(data.decode("utf-8"))
        captured_url = full_url
        captured_timeout = timeout
        return _FakeHTTPResponse(
            json.dumps(
                {
                    "message": {"content": "Ollama says hello"},
                    "done_reason": "stop",
                    "prompt_eval_count": 11,
                    "eval_count": 5,
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr("context_engine.models.ollama.urlopen", fake_urlopen)

    gateway = OllamaModelGateway(
        base_url="http://localhost:11434/",
        model_name="llama3.2:latest",
        timeout_seconds=12.5,
    )
    request = ModelRequest(
        model_id="runtime-selected-model",
        messages=normalize_messages(
            [
                ModelMessage(role=ModelRole.SYSTEM, content="Be concise."),
                ModelMessage(role=ModelRole.USER, content="Say hello."),
            ]
        ),
        max_output_tokens=64,
        temperature=0.2,
    )

    response = gateway.generate(request)

    assert captured_url == "http://localhost:11434/api/chat"
    assert captured_timeout == 12.5
    assert captured_request_payload == {
        "model": "llama3.2:latest",
        "messages": [
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Say hello."},
        ],
        "stream": False,
        "options": {"num_predict": 64, "temperature": 0.2},
    }
    assert response == ModelResponse(
        model_id="runtime-selected-model",
        output_text="Ollama says hello",
        finish_reason=ModelFinishReason.STOP,
        usage=ModelUsage(input_tokens=11, output_tokens=5),
    )


def test_ollama_gateway_uses_request_model_when_default_model_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_request_payload: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: float) -> _FakeHTTPResponse:
        del timeout
        data = getattr(request, "data")
        captured_request_payload.update(json.loads(data.decode("utf-8")))
        return _FakeHTTPResponse(
            json.dumps({"message": {"content": "partial"}, "done_reason": "length"}).encode("utf-8")
        )

    monkeypatch.setattr("context_engine.models.ollama.urlopen", fake_urlopen)

    gateway = OllamaModelGateway(base_url="http://localhost:11434")
    response = gateway.generate(
        ModelRequest(
            model_id="phi4-mini",
            messages=(ModelMessage(role=ModelRole.USER, content="Summarize this."),),
        )
    )

    assert captured_request_payload["model"] == "phi4-mini"
    assert response.finish_reason is ModelFinishReason.LENGTH


def test_ollama_gateway_translates_provider_independent_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_request_payload: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: float) -> _FakeHTTPResponse:
        del timeout
        data = getattr(request, "data")
        captured_request_payload.update(json.loads(data.decode("utf-8")))
        return _FakeHTTPResponse(
            json.dumps({"message": {"content": "tool-ready"}, "done_reason": "stop"}).encode(
                "utf-8"
            )
        )

    monkeypatch.setattr("context_engine.models.ollama.urlopen", fake_urlopen)
    gateway = OllamaModelGateway()
    gateway.generate(
        ModelRequest(
            model_id="llama3.2",
            messages=(ModelMessage(role=ModelRole.USER, content="Use add."),),
            tools=normalize_model_tools(
                [
                    ModelToolDefinition(
                        name="add",
                        description="Add two integers.",
                        input_schema={
                            "type": "object",
                            "properties": {
                                "a": {"type": "integer"},
                                "b": {"type": "integer"},
                            },
                            "required": ["a", "b"],
                            "additionalProperties": False,
                        },
                    )
                ]
            ),
        )
    )

    assert captured_request_payload["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "add",
                "description": "Add two integers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer"},
                        "b": {"type": "integer"},
                    },
                    "required": ["a", "b"],
                    "additionalProperties": False,
                },
            },
        }
    ]


def test_ollama_gateway_translates_tool_call_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: object, timeout: float) -> _FakeHTTPResponse:
        del request, timeout
        return _FakeHTTPResponse(
            json.dumps(
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "add",
                                    "arguments": {"b": 3, "a": 2},
                                }
                            }
                        ],
                    },
                    "done_reason": "stop",
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr("context_engine.models.ollama.urlopen", fake_urlopen)
    gateway = OllamaModelGateway()

    response = gateway.generate(
        ModelRequest(
            model_id="llama3.2",
            messages=(ModelMessage(role=ModelRole.USER, content="What is 2+3?"),),
        )
    )

    assert response.model_id == "llama3.2"
    assert response.output_text == ""
    assert response.finish_reason is ModelFinishReason.STOP
    assert response.tool_call is not None
    assert response.tool_call.tool_name == "add"
    assert response.tool_call.arguments_as_mapping() == {"a": 2, "b": 3}


def test_ollama_gateway_rejects_empty_message_requests() -> None:
    gateway = OllamaModelGateway()
    request = ModelRequest(model_id="llama3.2", messages=())

    with pytest.raises(ModelGatewayRequestError, match="at least one message"):
        gateway.generate(request)


def test_ollama_gateway_wraps_http_errors_with_gateway_execution_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: object, timeout: float) -> _FakeHTTPResponse:
        del request, timeout
        raise HTTPError(
            url="http://localhost:11434/api/chat",
            code=503,
            msg="Service Unavailable",
            hdrs=HTTPMessage(),
            fp=io.BytesIO(b'{"error":"service unavailable"}'),
        )

    monkeypatch.setattr("context_engine.models.ollama.urlopen", fake_urlopen)
    gateway = OllamaModelGateway()

    with pytest.raises(ModelGatewayExecutionError, match="HTTP status 503"):
        gateway.generate(
            ModelRequest(
                model_id="llama3.2",
                messages=(ModelMessage(role=ModelRole.USER, content="hello"),),
            )
        )


@pytest.mark.parametrize(
    "provider_exception",
    [URLError("connection refused"), TimeoutError("timed out")],
)  # type: ignore[misc]
def test_ollama_gateway_wraps_connection_and_timeout_failures(
    monkeypatch: pytest.MonkeyPatch,
    provider_exception: Exception,
) -> None:
    def fake_urlopen(request: object, timeout: float) -> _FakeHTTPResponse:
        del request, timeout
        raise provider_exception

    monkeypatch.setattr("context_engine.models.ollama.urlopen", fake_urlopen)
    gateway = OllamaModelGateway()

    with pytest.raises(ModelGatewayExecutionError, match="connection or timeout"):
        gateway.generate(
            ModelRequest(
                model_id="llama3.2",
                messages=(ModelMessage(role=ModelRole.USER, content="hello"),),
            )
        )


@pytest.mark.parametrize(
    ("response_payload", "expected_error_message"),
    [
        (b"not-json", "not valid JSON"),
        (json.dumps({"message": "bad-shape"}).encode("utf-8"), "message object"),
        (json.dumps({"message": {"content": 123}}).encode("utf-8"), "must be a string"),
        (
            json.dumps({"message": {"content": "ok"}, "prompt_eval_count": "invalid"}).encode(
                "utf-8"
            ),
            "prompt_eval_count",
        ),
        (
            json.dumps({"message": {"content": "", "tool_calls": {}}}).encode("utf-8"),
            "tool_calls must be a list",
        ),
        (
            json.dumps({"message": {"content": "", "tool_calls": []}}).encode("utf-8"),
            "exactly one tool call",
        ),
        (
            json.dumps(
                {
                    "message": {
                        "content": "",
                        "tool_calls": [{"function": {"name": "", "arguments": {}}}],
                    }
                }
            ).encode("utf-8"),
            "function name must be a non-empty string",
        ),
        (
            json.dumps(
                {
                    "message": {
                        "content": "",
                        "tool_calls": [{"function": {"name": "add", "arguments": "["}}],
                    }
                }
            ).encode("utf-8"),
            "arguments string must be valid JSON object",
        ),
    ],
)  # type: ignore[misc]
def test_ollama_gateway_rejects_malformed_provider_responses(
    monkeypatch: pytest.MonkeyPatch,
    response_payload: bytes,
    expected_error_message: str,
) -> None:
    def fake_urlopen(request: object, timeout: float) -> _FakeHTTPResponse:
        del request, timeout
        return _FakeHTTPResponse(response_payload)

    monkeypatch.setattr("context_engine.models.ollama.urlopen", fake_urlopen)
    gateway = OllamaModelGateway()

    with pytest.raises(ModelGatewayExecutionError, match=expected_error_message):
        gateway.generate(
            ModelRequest(
                model_id="llama3.2",
                messages=(ModelMessage(role=ModelRole.USER, content="hello"),),
            )
        )


def test_ollama_gateway_maps_unknown_done_reason_to_other(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: object, timeout: float) -> _FakeHTTPResponse:
        del request, timeout
        return _FakeHTTPResponse(
            json.dumps({"message": {"content": "cannot continue"}, "done_reason": "load"}).encode(
                "utf-8"
            )
        )

    monkeypatch.setattr("context_engine.models.ollama.urlopen", fake_urlopen)
    gateway = OllamaModelGateway()

    response = gateway.generate(
        ModelRequest(
            model_id="llama3.2",
            messages=(ModelMessage(role=ModelRole.USER, content="hello"),),
        )
    )

    assert response.finish_reason is ModelFinishReason.OTHER
