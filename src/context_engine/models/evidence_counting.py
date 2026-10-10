"""Offline answering-model tokenizer adapter; no model inference or downloads."""

import importlib
import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from context_engine.retrieval.evidence_selection import EvidenceSelectionError


class QwenEvidenceTokenCounter:
    """Count raw JSON with a pinned Qwen2.5 tokenizer, excluding the chat template.

    Exact for the loaded HF encoding; Ollama/GGUF parity is not asserted. This is
    an identified tokenizer budget, not a guarantee about the full model request.
    """

    method = "qwen2.5-hf-raw-json;no-special-tokens;ollama-parity-unverified"

    def __init__(self, directory: str, *, model_id: str = "qwen2.5:0.5b") -> None:
        if model_id != "qwen2.5:0.5b" or not isinstance(directory, str) or not directory.strip():
            raise EvidenceSelectionError(
                "Only qwen2.5:0.5b with an explicit local tokenizer is supported."
            )
        try:
            root = Path(directory)
            config_bytes = (root / "tokenizer_config.json").read_bytes()
            config = json.loads(config_bytes)
            # Explicit semantic compatibility plus a byte fingerprint of the actual encoding.
            if config.get("tokenizer_class") != "Qwen2Tokenizer":
                raise ValueError("Expected the Qwen2.5 Qwen2 tokenizer configuration.")
            tokenizer_bytes = (root / "tokenizer.json").read_bytes()
            if (
                sha256(tokenizer_bytes).hexdigest()
                != "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539"
                or sha256(config_bytes).hexdigest()
                != "5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583"
            ):
                raise ValueError(
                    "Unsupported tokenizer revision; use the documented pinned snapshot."
                )
            module = importlib.import_module("tokenizers")
            self._tokenizer: Any = module.Tokenizer.from_str(tokenizer_bytes.decode())
            self._tokenizer.no_truncation()
            self._tokenizer.no_padding()
        except Exception as exc:
            raise EvidenceSelectionError(
                "Local Qwen tokenizer is unavailable or incompatible."
            ) from exc
        self.model_id = model_id
        self.configuration_id = sha256(
            tokenizer_bytes + config_bytes + self.method.encode()
        ).hexdigest()

    def count_tokens(self, text: str) -> int:
        return len(self._tokenizer.encode(text, add_special_tokens=False).ids)
