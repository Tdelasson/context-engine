"""Explicit composition with the existing whole-document retrieval contract."""

from context_engine.knowledge.processing.contracts import ProcessedSource, SourceFormat
from context_engine.retrieval import Document


def to_document(source: ProcessedSource) -> Document:
    """Convert without chunking; pass the result to Ingestor.ingest_documents."""
    provenance = source.provenance
    metadata: dict[str, object] = {
        "source_id": provenance.source_id,
        "source_name": provenance.source_name,
        "source_kind": provenance.source_kind,
        "source_format": provenance.format.value,
        "content_sha256": provenance.content_sha256,
        "source_byte_length": provenance.byte_length,
        "source_encoding": provenance.encoding,
        "text_representation": "extracted_text",
    }
    if provenance.format is SourceFormat.PDF:
        locations = [
            {
                "page_number": block.location.page_number,
                "start_offset": block.location.start_offset,
                "end_offset": block.location.end_offset,
            }
            for block in source.blocks
            if block.location.page_number is not None
        ]
        metadata.update(
            source_page_count=len(locations),
            source_locations=locations,
            page_numbers=[location["page_number"] for location in locations],
            processing_diagnostics=[
                {
                    "code": diagnostic.code.value,
                    "message": diagnostic.message,
                    "page_number": (
                        diagnostic.location.page_number if diagnostic.location is not None else None
                    ),
                }
                for diagnostic in source.diagnostics
            ],
        )
    return Document.from_mapping(
        document_id=provenance.source_id,
        content=source.text,
        metadata=metadata,
    )
