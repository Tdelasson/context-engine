# Document Processing

`context_engine.knowledge.processing` accepts supplied bytes, independently of the
workbench. The caller acquires the content and assigns an identity stable across revisions.

```python
from context_engine.knowledge.processing import (
    ProcessingLimits,
    SourceFormat,
    SourceInput,
    process_source,
    to_document,
)

source = SourceInput(
    source_id="project:architecture",
    source_name="architecture.md",
    source_kind="project",
    content=b"# Architecture\n\nLocal-first processing.\n",
    format=SourceFormat.MARKDOWN,
)
processed = process_source(source, ProcessingLimits(max_bytes=1024, max_text_characters=1024))
document = to_document(processed)
# With an application-composed Ingestor: ingestor.ingest_documents((document,))
```

Use `SourceFormat.TEXT` for plain UTF-8 text. Formats are explicit enum values, not inferred
from names. `SourceInput` rejects missing identifiers, non-byte content, and unsupported formats.
No paths are opened, and no model inference is performed.

`ProcessedSource` contains extracted text, immutable structural blocks, source provenance,
and diagnostics. Text preserves original syntax, whitespace, and line endings except a leading
UTF-8 BOM. Markdown recognizes ATX/setext headings, fenced code, and indented code; other syntax
is retained as text. Blocks partition the complete extracted text, including whitespace.
Offsets are zero-based, end-exclusive Unicode character offsets in `ProcessedSource.text`,
identified by `representation="extracted_text"`. Line numbers are one-based, inclusive,
and follow Python `str.splitlines()` boundaries. They are not byte offsets in the source.

`SourceProvenance.source_id` is the logical identity. `content_sha256` is a full SHA-256
of the original supplied bytes, including any BOM; `byte_length` describes those same bytes.
Identical inputs and limits produce equivalent results without timestamps or generated IDs.
`to_document` uses the source ID as the document ID and includes provenance metadata.
It emits one whole document; it does not chunk, embed, or persist anything.

`ProcessingError` carries a `ProcessingErrorCode`: invalid input/configuration, unsupported
format, invalid UTF-8, empty/whitespace-only content, exceeded byte limit, or exceeded extracted
character limit. Limits are positive integers and inclusive, and default to 256 KiB of supplied
bytes and 262144 extracted characters. Failures return no partial result. Nonfatal diagnostics
report removal of a BOM and an unclosed code fence (preserved through end of source).

See [ADR-006](../architecture/decisions/ADR-006-knowledge-document-processing.md).
