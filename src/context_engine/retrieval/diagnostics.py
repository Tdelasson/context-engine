"""Immutable ranking diagnostics, kept separate from canonical evidence metadata."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class RetrievalStageDiagnostic:
    """One ranking stage; native score semantics are defined by score_kind."""

    strategy: str
    score_kind: str
    score: float
    rank: int
    configuration_id: str
    model_id: str | None = None
    candidate_count: int | None = None
    duration_seconds: float | None = None

    def __post_init__(self) -> None:
        for name in ("strategy", "score_kind", "configuration_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonblank string.")
        if self.model_id is not None and (
            not isinstance(self.model_id, str) or not self.model_id.strip()
        ):
            raise ValueError("model_id must be a nonblank string when supplied.")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise ValueError("score must be a finite number.")
        if not isfinite(self.score):
            raise ValueError("score must be a finite number.")
        for name in ("rank", "candidate_count"):
            value = getattr(self, name)
            if value is None and name == "candidate_count":
                continue
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")
        if self.duration_seconds is not None and (
            isinstance(self.duration_seconds, bool)
            or not isinstance(self.duration_seconds, (int, float))
            or not isfinite(self.duration_seconds)
            or self.duration_seconds < 0
        ):
            raise ValueError("duration_seconds must be finite and nonnegative.")
