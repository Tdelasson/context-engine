"""Optional local Sentence Transformers cross-encoder with strict pair accounting."""

import importlib
import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
from time import perf_counter
from typing import Any, Protocol

from context_engine.retrieval.reranking import (
    RerankerConfigurationError,
    RerankerError,
    RerankerInferenceError,
    RerankerInitializationError,
    RerankerInputCompatibilityError,
    RerankingRequest,
    RerankingScore,
    positive_integer,
)


@dataclass(frozen=True, slots=True)
class LocalCrossEncoderConfig:
    """Offline by default; prefixes are explicitly included in exact pair token counts."""

    model_reference: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    revision: str | None = None
    device: str = "cpu"
    batch_size: int = 8
    max_input_tokens: int = 512
    query_prefix: str = ""
    passage_prefix: str = ""
    local_files_only: bool = True

    def __post_init__(self) -> None:
        for name in ("model_reference", "device"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise RerankerConfigurationError(f"{name} must be nonblank.")
        if self.revision is not None and (
            not isinstance(self.revision, str) or not self.revision.strip()
        ):
            raise RerankerConfigurationError("revision must be nonblank when supplied.")
        for name in ("query_prefix", "passage_prefix"):
            if not isinstance(getattr(self, name), str):
                raise RerankerConfigurationError(f"{name} must be text.")
        if type(self.local_files_only) is not bool:
            raise RerankerConfigurationError("local_files_only must be boolean.")
        positive_integer("batch_size", self.batch_size)
        positive_integer("max_input_tokens", self.max_input_tokens)


class CrossEncoderBackend(Protocol):
    """Adapter-private runtime contract used for deterministic fixtures."""

    @property
    def max_input_tokens(self) -> int: ...

    @property
    def identity(self) -> str: ...

    @property
    def model_parameter_bytes(self) -> int | None: ...

    def count_pair(self, query: str, passage: str) -> int: ...

    def score_pairs(self, pairs: Sequence[tuple[str, str]]) -> Sequence[float]: ...


class LocalCrossEncoderReranker:
    """Load once, validate every pair before any inference, then score bounded batches."""

    score_kind = "logit"

    def __init__(
        self,
        config: LocalCrossEncoderConfig | None = None,
        *,
        backend_factory: Callable[[LocalCrossEncoderConfig], CrossEncoderBackend] | None = None,
    ) -> None:
        self.config = config or LocalCrossEncoderConfig()
        started = perf_counter()
        try:
            self._backend = (backend_factory or _SentenceTransformersBackend)(self.config)
            positive_integer("backend input limit", self._backend.max_input_tokens)
            if not self._backend.identity:
                raise RerankerInitializationError("Backend identity is empty.")
            if self.config.max_input_tokens > self._backend.max_input_tokens:
                raise RerankerConfigurationError(
                    f"Configured limit {self.config.max_input_tokens} exceeds model limit "
                    f"{self._backend.max_input_tokens}."
                )
        except RerankerError:
            raise
        except Exception as exc:
            raise RerankerInitializationError("Failed to initialize local cross-encoder.") from exc
        self.initialization_seconds = perf_counter() - started
        self.configuration_id = sha256(
            json.dumps(
                {
                    "settings": asdict(self.config),
                    "runtime": self._backend.identity,
                    "score_kind": self.score_kind,
                    "preprocessing": "exact-pair-no-strip-no-headings-v1",
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        self.model_id = self._backend.identity

    @property
    def model_parameter_bytes(self) -> int | None:
        return self._backend.model_parameter_bytes

    def score(self, request: RerankingRequest) -> tuple[RerankingScore, ...]:
        pairs = tuple(
            (
                self.config.query_prefix + request.query,
                self.config.passage_prefix + candidate.document.content,
            )
            for candidate in request.candidates
        )
        try:
            # No successful-looking partial inference if a later pair is incompatible.
            for candidate, pair in zip(request.candidates, pairs, strict=True):
                count = self._backend.count_pair(*pair)
                if type(count) is not int or count < 0:
                    raise RerankerInferenceError("Tokenizer returned an invalid pair count.")
                if count > self.config.max_input_tokens:
                    raise RerankerInputCompatibilityError(
                        f"Candidate '{candidate.candidate_id}' requires {count} pair tokens; "
                        f"effective limit is {self.config.max_input_tokens} for {self.model_id}. "
                        "Includes unchanged query, passage, prefixes, and special tokens."
                    )
            outputs: list[RerankingScore] = []
            for start in range(0, len(pairs), self.config.batch_size):
                batch = pairs[start : start + self.config.batch_size]
                scores = tuple(self._backend.score_pairs(batch))
                if len(scores) != len(batch):
                    raise RerankerInferenceError("Local model returned an incorrect score count.")
                for candidate, score in zip(
                    request.candidates[start : start + len(batch)], scores, strict=True
                ):
                    outputs.append(RerankingScore(candidate.candidate_id, score))
            return tuple(outputs)
        except RerankerError:
            raise
        except Exception as exc:
            raise RerankerInferenceError("Local cross-encoder scoring failed.") from exc


class _SentenceTransformersBackend:
    """Uses the ST-loaded classifier directly; predict() may enable hidden truncation."""

    def __init__(self, config: LocalCrossEncoderConfig) -> None:
        try:
            module = importlib.import_module("sentence_transformers")
            self._torch: Any = importlib.import_module("torch")
            self._cross_encoder: Any = module.CrossEncoder(
                config.model_reference,
                revision=config.revision,
                device=config.device,
                local_files_only=config.local_files_only,
                trust_remote_code=False,
                backend="torch",
            )
            self._model: Any = self._cross_encoder.model
            self._tokenizer: Any = self._cross_encoder.tokenizer
            self._model.eval()
            if self._model.config.num_labels != 1:
                raise RerankerInitializationError(
                    "Only single-logit text classifiers are supported."
                )
            limits = (self._tokenizer.model_max_length, self._model.config.max_position_embeddings)
            usable = [
                int(value) for value in limits if isinstance(value, int) and 0 < value < 10**9
            ]
            if not usable:
                raise RerankerInitializationError("Cannot establish the actual model input limit.")
            self.max_input_tokens = min(usable)
            digest = sha256(self._tokenizer.backend_tokenizer.to_str().encode())
            digest.update(json.dumps(self._model.config.to_dict(), sort_keys=True).encode())
            for name, parameter in self._model.named_parameters():
                digest.update(name.encode())
                digest.update(str(parameter.dtype).encode())
                digest.update(str(tuple(parameter.shape)).encode())
                digest.update(
                    parameter.detach()
                    .cpu()
                    .contiguous()
                    .view(-1)
                    .view(self._torch.uint8)
                    .numpy()
                    .tobytes()
                )
            self.identity = f"{config.model_reference}@loaded-sha256:{digest.hexdigest()}"
            self.model_parameter_bytes = sum(
                int(value.numel()) * int(value.element_size()) for value in self._model.parameters()
            )
        except RerankerError:
            raise
        except ImportError as exc:
            raise RerankerInitializationError(
                "Install the reranking extra and explicitly prepare the model locally."
            ) from exc
        except Exception as exc:
            raise RerankerInitializationError(
                f"Cannot load local cross-encoder '{config.model_reference}'. "
                "Offline loading is the default; download the model explicitly during setup."
            ) from exc

    def count_pair(self, query: str, passage: str) -> int:
        encoded = self._tokenizer(
            query, passage, add_special_tokens=True, truncation=False, padding=False
        )
        return len(encoded["input_ids"])

    def score_pairs(self, pairs: Sequence[tuple[str, str]]) -> tuple[float, ...]:
        encoded = self._tokenizer(
            [pair[0] for pair in pairs],
            [pair[1] for pair in pairs],
            add_special_tokens=True,
            truncation=False,
            padding=True,
            return_tensors="pt",
        )
        if int(encoded["input_ids"].shape[1]) > self.max_input_tokens:
            raise RerankerInputCompatibilityError("Encoded batch exceeds actual model input limit.")
        encoded = {name: value.to(self._cross_encoder.device) for name, value in encoded.items()}
        with self._torch.inference_mode():
            logits = self._model(**encoded, return_dict=True).logits
        if tuple(logits.shape) != (len(pairs), 1):
            raise RerankerInferenceError("Expected one native logit per input pair.")
        return tuple(float(value) for value in logits[:, 0].detach().cpu().tolist())
