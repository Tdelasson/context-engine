"""Lossless compressed local artifacts; raw results remain independently replayable."""

import gzip
import json
from pathlib import Path
from typing import Any

from benchmarks.benchmark_evidence_selection import serialize_artifact


def read_artifact(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    raw = json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)
    if not isinstance(raw, dict) or any(not isinstance(key, str) for key in raw):
        raise ValueError("Evaluation artifacts must be JSON objects with string keys.")
    return {str(key): value for key, value in raw.items()}


def write_artifact(path: Path, output: dict[str, Any]) -> None:
    data = serialize_artifact(output).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(data, mtime=0) if path.suffix == ".gz" else data)
