"""Optional adapter for an already-loaded Hugging Face embedding tokenizer."""

from collections.abc import Sequence
from typing import Protocol

from context_engine.knowledge.chunking import ChunkingError, ChunkingErrorCode


class EncodingTokenizer(Protocol):
    def encode(
        self,
        text: str,
        *,
        add_special_tokens: bool,
        truncation: bool,
        padding: bool,
    ) -> Sequence[int]: ...


class TokenizerTokenCounter:
    """Use the embedding tokenizer, without loading a model or downloading files.

    Caller supplies the embedding runtime's actual maximum input length, tokenizer
    revision, and matching preprocessing. For SentenceTransformer Transformer modules,
    strip_text=True matches their whitespace stripping; lowercase matches do_lower_case.
    """

    def __init__(
        self,
        tokenizer: EncodingTokenizer,
        *,
        model_id: str,
        tokenizer_id: str,
        max_input_tokens: int,
        strip_text: bool = True,
        lowercase: bool = False,
    ) -> None:
        if (
            not isinstance(model_id, str)
            or not model_id.strip()
            or not isinstance(tokenizer_id, str)
            or not tokenizer_id.strip()
            or type(max_input_tokens) is not int
            or max_input_tokens <= 0
            or type(strip_text) is not bool
            or type(lowercase) is not bool
            or not callable(getattr(tokenizer, "encode", None))
        ):
            raise ChunkingError(
                ChunkingErrorCode.INCOMPATIBLE_TOKENIZER,
                "An embedding tokenizer, explicit identities, and runtime limit are required.",
            )
        self._tokenizer = tokenizer
        self.model_id = model_id
        self.tokenizer_id = (
            f"{tokenizer_id};strip={str(strip_text).lower()};lowercase={str(lowercase).lower()}"
        )
        self.max_input_tokens = max_input_tokens
        self._strip_text = strip_text
        self._lowercase = lowercase

    def count_tokens(self, text: str, *, add_special_tokens: bool = True) -> int:
        if self._strip_text:
            text = text.strip()
        if self._lowercase:
            text = text.lower()
        return len(
            self._tokenizer.encode(
                text,
                add_special_tokens=add_special_tokens,
                truncation=False,
                padding=False,
            )
        )
