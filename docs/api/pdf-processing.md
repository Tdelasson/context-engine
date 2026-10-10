# PDF processing

`process_source(SourceInput(..., format=SourceFormat.PDF), limits)` dispatches to
`process_pdf`. The adapter reads supplied bytes locally with pypdf; no files, models,
network services, or OCR are invoked. Install the optional extra with
`pip install "context-engine[pdf]"`. Development installs also include pypdf so CI
runs real PDF fixtures. pypdf is pure Python, actively maintained, and BSD-3-Clause
licensed; it provides PDF parsing and font decoding that would be disproportionate
to implement here. It remains behind the processing contracts.

Each original page produces a text block carrying `location.page_number` (one-based),
including extraction-empty pages. The extracted text of adjacent pages is joined by
exactly `\n\n`, represented by separate whitespace blocks without a page number.
Original page text is unchanged. Offsets are zero-based, end-exclusive Unicode character
positions in the combined `ProcessedSource.text`, never PDF byte or visual coordinates.
Lines use `str.splitlines()` boundaries. Empty pages have zero-width locations.
Provenance retains the source ID, input-byte SHA-256 revision, and byte count;
`encoding=None` because a PDF is not a UTF-8 input text stream.

`EMPTY_PAGE` diagnostics identify pages without usable extracted text. This may mean
blank pages or images without a text layer; it does not assert that a page is scanned.
Mixed documents also return `PARTIAL_EXTRACTION`. Diagnostics remain outside source
text. PDFs without any usable text fail with `EMPTY_CONTENT`. Text on image-bearing
pages can be extracted, but completeness of non-text visual content is not assessed.

Typed failures include `MISSING_DEPENDENCY` (with installation guidance),
`MALFORMED_PDF`, `ENCRYPTED_PDF`, `BYTE_LIMIT`, `PAGE_LIMIT`, and `TEXT_LIMIT`.
All encryption is rejected, including documents readable with an empty password.
`ProcessingLimits` defaults to 256 KiB input, 256 Ki characters, and 100 pages.
Byte limits are checked before parsing, page limits before extraction, and cumulative
character limits after each page extraction, including inserted separators. These
limits do **not** bound parser CPU, decompression, or peak memory: pypdf may expand
compressed streams and allocate an entire page's text before checking its length.
Process isolation and hard resource quotas remain future work.

Extraction reads the existing PDF text layer. Reading order, complex layouts, tables,
image descriptions, and correctness of an existing OCR layer are not guaranteed.
See [pypdf extraction guidance](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
and its [license](https://github.com/py-pdf/pypdf/blob/main/LICENSE).

The whole-document adapter adds JSON-safe `page_numbers`, `source_locations`
(page number and extracted character span), `source_page_count`, and
`processing_diagnostics` metadata. Chunk composition retains finer location metadata.
The workbench accepts `.pdf`, reports diagnostics after ingestion, and displays page
references with evidence. Its current catalog still indexes whole documents.

PDF workbench limits are configured separately from text upload limits:

| Environment variable | Default |
| --- | --- |
| `CONTEXT_ENGINE_WORKBENCH_MAX_PDF_BYTES` | 10485760 |
| `CONTEXT_ENGINE_WORKBENCH_MAX_PDF_PAGES` | 100 |
| `CONTEXT_ENGINE_WORKBENCH_MAX_PDF_TEXT_CHARACTERS` | 1048576 |

The existing maximum upload count applies to all formats. Updating the same filename
replaces its content and diagnostics. Clearing uploads clears their diagnostic state.
