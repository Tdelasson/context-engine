import { asBoolean, asList, asNumber, asString, isRecord } from '../api/json'
import type { JsonRecord } from '../api/json'
import type { RunDetail } from '../api/types'

export interface StageScore {
  strategy: string
  scoreKind: string
  score: number
  rank: number
  candidateCount: number | null
  durationSeconds: number | null
  modelId: string | null
}

export interface EvidenceItem {
  documentId: string
  score: number
  content: string
  truncated: boolean
  metadata: JsonRecord
  stages: StageScore[]
}

export interface SelectionCandidate {
  candidateId: string
  originalRank: number
  originalScore: number
  reason: string
  overlapFraction: number | null
  provenanceStatus: string
}

export interface SelectionView {
  status: string
  tokenCount: number | null
  candidates: SelectionCandidate[]
}

export interface PipelineStage {
  id: 'query' | 'dense' | 'lexical' | 'reranking' | 'selection' | 'returned'
  name: string
  enabled: boolean
  summary: string
  durationSeconds: number | null
}

export interface RetrievalView {
  query: string | null
  strategy: string
  stages: PipelineStage[]
  evidence: EvidenceItem[]
  selection: SelectionView | null
}

function parseStage(raw: unknown): StageScore | null {
  if (!isRecord(raw)) return null
  const strategy = asString(raw.strategy)
  const score = asNumber(raw.score)
  const rank = asNumber(raw.rank)
  if (strategy === null || score === null || rank === null) return null
  return {
    strategy,
    scoreKind: asString(raw.score_kind) ?? 'unspecified',
    score,
    rank,
    candidateCount: asNumber(raw.candidate_count),
    durationSeconds: asNumber(raw.duration_seconds),
    modelId: asString(raw.model_id),
  }
}

function parseEvidence(raw: unknown): EvidenceItem | null {
  if (!isRecord(raw)) return null
  const documentId = asString(raw.document_id)
  const score = asNumber(raw.score)
  if (documentId === null || score === null) return null
  return {
    documentId,
    score,
    content: asString(raw.content) ?? '',
    truncated: asBoolean(raw.content_truncated) ?? false,
    metadata: isRecord(raw.metadata) ? raw.metadata : {},
    stages: asList(raw.diagnostics)
      .map(parseStage)
      .filter((stage): stage is StageScore => stage !== null),
  }
}

function parseSelection(raw: unknown): SelectionView | null {
  if (!isRecord(raw)) return null
  const candidates = asList(raw.candidates).flatMap((item): SelectionCandidate[] => {
    if (!isRecord(item)) return []
    const candidateId = asString(item.candidate_id)
    const originalRank = asNumber(item.original_rank)
    const originalScore = asNumber(item.original_score)
    if (candidateId === null || originalRank === null || originalScore === null) return []
    return [
      {
        candidateId,
        originalRank,
        originalScore,
        reason: asString(item.reason) ?? 'unspecified',
        overlapFraction: asNumber(item.overlap_fraction),
        provenanceStatus: asString(item.provenance_status) ?? 'unspecified',
      },
    ]
  })
  return {
    status: asString(raw.status) ?? 'unspecified',
    tokenCount: asNumber(raw.token_count),
    candidates,
  }
}

function stageDuration(evidence: EvidenceItem[], match: (strategy: string) => boolean) {
  for (const item of evidence) {
    for (const stage of item.stages) {
      if (match(stage.strategy) && stage.durationSeconds !== null) return stage.durationSeconds
    }
  }
  return null
}

function stageCandidates(evidence: EvidenceItem[], match: (strategy: string) => boolean) {
  for (const item of evidence) {
    for (const stage of item.stages) {
      if (match(stage.strategy) && stage.candidateCount !== null) return stage.candidateCount
    }
  }
  return null
}

/**
 * Derive the retrieval pipeline and evidence from the run's latest successful
 * `search_documents` result. Returns null when the run has no such result (yet): retrieval
 * stages do not emit live events, so they appear once the run has finished.
 *
 * The evidence comes from the result's model output. The selection report is runtime-only,
 * so it comes from the diagnostics on the trace of the same call.
 */
export function deriveRetrieval(
  run: RunDetail,
  settings: Record<string, unknown> | null,
): RetrievalView | null {
  const result = run.tool_results.findLast(
    (item) => item.tool_name === 'search_documents' && item.status === 'success' && item.output,
  )
  const output = result?.output
  if (!isRecord(output)) return null

  const evidence = asList(output.results)
    .map(parseEvidence)
    .filter((item): item is EvidenceItem => item !== null)
  // Match the invocation id, which live calls often leave null. Each call has one result and
  // one trace in the same order, so requiring a successful trace still pairs the latest
  // successful search result with its own trace when every id is null.
  const trace = run.traces.findLast(
    (item) =>
      item.tool_name === 'search_documents' &&
      item.status === 'success' &&
      item.invocation_id === result?.invocation_id,
  )
  const selection = parseSelection(trace?.diagnostics?.selection)
  const strategies = new Set(evidence.flatMap((item) => item.stages.map((stage) => stage.strategy)))
  const hybridActive = [...strategies].some((s) => s === 'hybrid' || s.startsWith('hybrid_') || s === 'lexical')
  const rerankingActive = strategies.has('reranking')
  const configured = asString(settings?.retrieval_strategy)
  const strategy = hybridActive ? 'hybrid' : (configured ?? 'dense')
  const query = asString(output.query)

  const rerankModel = evidence.flatMap((item) => item.stages).find((s) => s.strategy === 'reranking')
  const rerankCandidates = stageCandidates(evidence, (s) => s === 'reranking')

  const stages: PipelineStage[] = [
    {
      id: 'query',
      name: 'Query',
      enabled: true,
      summary: query ?? 'Query not reported',
      durationSeconds: null,
    },
    {
      id: 'dense',
      name: 'Dense search',
      enabled: true,
      summary: `${evidence.length} passages from the vector index`,
      durationSeconds: stageDuration(evidence, (s) => s === 'hybrid_dense'),
    },
    {
      id: 'lexical',
      name: 'Lexical BM25 + rank fusion',
      enabled: hybridActive,
      summary: hybridActive
        ? `Fused ${stageCandidates(evidence, (s) => s === 'hybrid') ?? '?'} candidates`
        : 'Enabled by the hybrid strategy',
      durationSeconds: stageDuration(evidence, (s) => s === 'hybrid'),
    },
    {
      id: 'reranking',
      name: 'Cross-encoder reranking',
      enabled: rerankingActive,
      summary: rerankingActive
        ? `${rerankModel?.modelId ?? 'cross-encoder'} · ${rerankCandidates ?? '?'} candidates`
        : 'Disabled by default',
      durationSeconds: stageDuration(evidence, (s) => s === 'reranking'),
    },
    {
      id: 'selection',
      name: 'Evidence selection',
      enabled: selection !== null,
      summary: selection
        ? `${selection.status} · ${selection.tokenCount ?? '?'} tokens`
        : 'Disabled by default',
      durationSeconds: null,
    },
    {
      id: 'returned',
      name: 'Evidence returned to the model',
      enabled: true,
      summary: `${evidence.length} passages`,
      durationSeconds: null,
    },
  ]
  return { query, strategy, stages, evidence, selection }
}
