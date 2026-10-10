"""Explicit offline real-model verification, excluded unless a snapshot is supplied."""

import os

import pytest

from context_engine.retrieval.embeddings import Document
from context_engine.retrieval.local_cross_encoder import (
    LocalCrossEncoderConfig,
    LocalCrossEncoderReranker,
)
from context_engine.retrieval.reranking import (
    RerankerInputCompatibilityError,
    RerankingCandidate,
    RerankingRequest,
)


def test_real_local_cross_encoder() -> None:
    reference = os.getenv("CONTEXT_ENGINE_RERANKING_INTEGRATION_MODEL")
    if not reference:
        pytest.skip("Supply a prepared offline model snapshot to opt in.")
    assert reference is not None
    reranker = LocalCrossEncoderReranker(LocalCrossEncoderConfig(model_reference=reference))
    request = RerankingRequest(
        "Which planet is known as the Red Planet?",
        tuple(
            RerankingCandidate(Document.from_mapping(document_id=str(i), content=text))
            for i, text in enumerate(("Mars is known as the Red Planet.", "Venus is Earth's twin."))
        ),
    )
    scores = reranker.score(request)
    assert scores[0].score > scores[1].score
    overflow = RerankingRequest(
        "query",
        (
            RerankingCandidate(
                Document.from_mapping(document_id="oversize", content="planet " * 600)
            ),
        ),
    )
    with pytest.raises(RerankerInputCompatibilityError):
        reranker.score(overflow)
