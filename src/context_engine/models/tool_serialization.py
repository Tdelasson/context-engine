"""Explicit JSON output accounting; runtime-only search selection reports stay out of history."""

import json
from collections.abc import Mapping


def model_visible_tool_output(tool_name: str, output: Mapping[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in output.items()
        if tool_name != "search_documents" or key != "selection_diagnostics"
    }


def render_tool_output(output: Mapping[str, object]) -> str:
    """Match the output object's representation inside Ollama's sorted JSON envelope."""
    return json.dumps(dict(output), sort_keys=True, ensure_ascii=True, allow_nan=False)
