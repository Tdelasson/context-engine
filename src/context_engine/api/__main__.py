"""Launch the local HTTP API: ``python -m context_engine.api``."""

from __future__ import annotations

import argparse
from pathlib import Path

from context_engine.api.app import create_app
from context_engine.core import build_live_application


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Context Engine local HTTP API.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: loopback).")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--static-dir", type=Path, default=None, help="Built frontend directory to serve at /."
    )
    args = parser.parse_args(argv)

    import uvicorn

    application = build_live_application()
    application.prepare()
    uvicorn.run(create_app(application, static_dir=args.static_dir), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
