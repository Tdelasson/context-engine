"""The one JSON rendering of tool output shared by model gateways and evidence token counting."""

import json
from collections.abc import Mapping


def render_tool_output(output: Mapping[str, object]) -> str:
    """Render tool output as the JSON text a gateway sends and evidence selection counts.

    Raises ``ValueError`` for values JSON cannot represent, such as NaN or infinity.
    """
    return json.dumps(dict(output), sort_keys=True, ensure_ascii=True, allow_nan=False)
