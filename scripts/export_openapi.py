"""Write the HTTP API's OpenAPI document for frontend type generation.

Usage: python scripts/export_openapi.py [output-path]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

from context_engine.api import create_app

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "frontend" / "openapi.json"


def main(argv: list[str]) -> None:
    output = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUTPUT
    # The OpenAPI document does not depend on a composed application.
    app = create_app(cast(Any, None))
    output.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
