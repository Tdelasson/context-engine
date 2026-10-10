"""Explicit composition with the existing whole-document retrieval contract."""

from context_engine.knowledge.processing.contracts import ProcessedSource
from context_engine.retrieval import Document


def to_document(source: ProcessedSource) -> Document:
    """Convert without chunking; pass the result to Ingestor.ingest_documents."""
    provenance = source.provenance
    return Document.from_mapping(
        document_id=provenance.source_id,
        content=source.text,
        metadata={
            "source_id": provenance.source_id,
            "source_name": provenance.source_name,
            "source_kind": provenance.source_kind,
            "source_format": provenance.format.value,
            "content_sha256": provenance.content_sha256,
            "source_byte_length": provenance.byte_length,
            "source_encoding": provenance.encoding,
            "text_representation": "extracted_text",
        },
    )
