# ADR-011: Lexical BM25 retrieval and shared chunk ownership

- Status: Accepted
- Date: 2026-10-10
- Issue: #66

## Context

Lexical retrieval supplies an independently measurable signal for query terms and
technical identifiers. Dense similarity remains the baseline. ADR-009 requires a
single persisted source journal and explicit recovery for incomplete operations.
Upsert replaces a complete point; omitted vector representations must not be
assumed to survive. Two independent collection writers would make visibility and
recovery harder to reason about.

## Decision

Applications continue using Retriever. LexicalRetriever delegates text queries to
the provider-independent LexicalIndex capability, validates records/scores/filters,
and adds immutable BM25 diagnostics outside canonical provenance. BM25 scores are
nonnegative lexical ranking values, not probabilities or cosine similarities.
Results are ordered by descending score, then chunk ID for ties among returned
candidates. Backend top-K boundary ties can select different equally ranked
candidates; no bitwise ranking guarantee is promised.

QdrantBM25ChunkStore owns complete canonical chunk points, both named dense and
lexical vectors, source manifests, and deletion. SourceIngestionCoordinator uses
this store unchanged: processing and embedding precede the staging manifest;
complete point writes include both representations; ready/active transitions,
rollback and shorter replacement deletion follow ADR-009. Both searches check
manifests before and after queries and fail closed while recovery is needed.
Lexical search additionally checks each returned ID and source hash against the
active manifest. Recovery requires neither original source bytes nor inference.

QdrantLexicalIndex exposes only lexical capability to LexicalRetriever. Its direct
mutations require coordinator-owned pending states. Lexical updates must match
existing canonical text and metadata and use update_vectors, which preserves
other vectors and payload. It cannot independently create sparse-only chunks.
Deletion removes complete chunks and requires a pending source operation. The
combined store is the normal ingestion path; do not call adapters to bypass it.

Native BM25 encoding runs inside the explicitly configured local Qdrant server,
using qdrant/bm25 Document inputs and sparse IDF modifier. The SDK's
cloud_inference=True means forwarding Document inputs to that configured URL;
it does not select a cloud endpoint. Only the native BM25 model is submitted.
No hosted provider or model downloads are used. Loopback URLs are the default
policy; non-loopback servers require explicit adapter allow_remote_server=True.
Workbench lexical configuration permits loopback only. Client/server transport
failures become actionable typed errors at the lexical capability boundary.

Supported minimum: Qdrant 1.16.3 and qdrant-client 1.16; verified together with
client 1.16.2. Native BM25 was introduced earlier, but this implementation's
complete configuration/storage behavior is verified against 1.16.3. Server
version participates in the lexical configuration identity; opening the same
collection after a server upgrade requires explicit rebuild. An incompatible
named-vector layout, sparse modifier, embedding space, chunking identity, or
lexical configuration is rejected. Dense-only QdrantVectorStore rejects a
lexical-enabled collection, preventing accidental sparse erasure.

BM25 defaults: k=1.2, b=0.75, fixed average_document_length=128, language=English,
word tokenizer, lowercase=true, default English Snowball stemming, empty
stopwords. The average length is an explicit fixed parameter, not an automatically
computed corpus statistic. Native term IDs use Murmur3 hashing; collisions are
possible, so this is lexical relevance rather than exact identifier verification.
IDF statistics are collection-wide, including points retained during replacement;
search is unavailable during pending operations. Nonsearchable manifests have no
lexical vector; collection point count still affects BM25 IDF denominator.

Real 1.16.3 tests establish: ToolApprovalRequiredError remains a single token
(case-insensitive; Approval alone does not match); search_documents splits into
search/documents; COBALT-742 splits into cobalt/742; a path such as
context_engine/knowledge/ingestion.py splits into words across underscores,
slashes and dots. café matches CAFÉ, but cafe does not match café; 東京 matches
itself. Punctuation-only queries return no results. There is no added custom
splitting, Unicode normalization, ASCII folding, or multilingual stemming.
Language configuration other than English is rejected for this first version.

## Alternatives and consequences

Local FastEmbed would allow earlier server versions but introduces an optional
encoder library, cached language assets, and a second tokenizer implementation.
Native server encoding keeps inference local and uses the database's supported
BM25 path without new Python dependencies. It requires an actual Qdrant server;
embedded Python Qdrant is not accepted as equivalent native encoding.

Separate sparse collections avoid named dense-vector changes but require a second
mutation durability boundary and reconciliation after failure. Shared points keep
one lifecycle owner and preserve existing source identities. Lexical query
execution needs no embedding model; normal shared ingestion still computes dense
embeddings to retain a directly comparable baseline. Future standalone storage
adapters can implement LexicalIndex without changing tools or agents.

Migration: select a new lexical collection, reingest original sources using the
combined store, verify source reports/search, then retire the old collection
explicitly. Existing dense-only M5 collections continue using the dense adapter.
Do not silently alter collections or migrate by rewriting manifests.
