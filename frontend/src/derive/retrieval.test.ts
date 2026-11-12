import { describe, expect, it } from 'vitest'
import { SEARCH_OUTPUT_FULL, SELECTION_DIAGNOSTICS, awaitingApprovalRun, makeRun, searchTrace } from '../test/fixtures'
import { deriveRetrieval } from './retrieval'

const stage = (view: NonNullable<ReturnType<typeof deriveRetrieval>>, id: string) =>
  view.stages.find((item) => item.id === id)

function runWithOutput(output: unknown, diagnostics: Record<string, unknown> | null = null) {
  return makeRun({
    tool_results: [
      { tool_name: 'search_documents', invocation_id: 'call-1', arguments: {}, status: 'success', output: output as never, error: null },
    ],
    traces: [searchTrace({ arguments: {}, output: output as never, diagnostics: diagnostics as never })],
  })
}

describe('deriveRetrieval', () => {
  it('shows a single dense stage for the default configuration', () => {
    const view = deriveRetrieval(makeRun(), { retrieval_strategy: 'dense' })

    expect(view?.strategy).toBe('dense')
    expect(view?.query).toBe('tool policy')
    expect(view?.stages.map((item) => [item.id, item.enabled])).toEqual([
      ['query', true],
      ['dense', true],
      ['lexical', false],
      ['reranking', false],
      ['selection', false],
      ['returned', true],
    ])
    expect(view?.evidence).toHaveLength(2)
    expect(view?.evidence[1]?.truncated).toBe(true)
    expect(view?.selection).toBeNull()
  })

  it('derives the hybrid, reranking and selection stages from the diagnostics', () => {
    const view = deriveRetrieval(runWithOutput(SEARCH_OUTPUT_FULL, { selection: SELECTION_DIAGNOSTICS }), {
      retrieval_strategy: 'hybrid',
    })

    expect(view?.strategy).toBe('hybrid')
    expect(stage(view!, 'lexical')).toMatchObject({ enabled: true, durationSeconds: 0.012 })
    expect(stage(view!, 'reranking')).toMatchObject({ enabled: true, durationSeconds: 0.4 })
    expect(stage(view!, 'reranking')?.summary).toContain('cross-encoder/ms-marco-MiniLM-L6-v2')
    expect(stage(view!, 'selection')).toMatchObject({ enabled: true, summary: 'selected · 812 tokens' })
    expect(view?.evidence[0]?.stages.map((item) => item.strategy)).toEqual([
      'hybrid_dense',
      'hybrid_lexical',
      'hybrid',
      'reranking',
    ])
    expect(view?.selection?.candidates.map((item) => item.reason)).toEqual(['selected', 'excluded_overlap'])
  })

  it('reads the selection report from the trace of the matching search call', () => {
    const run = runWithOutput(SEARCH_OUTPUT_FULL, { selection: SELECTION_DIAGNOSTICS })
    const otherCall = { ...run.traces[0]!, invocation_id: 'call-0', diagnostics: { selection: { status: 'over_budget', token_count: 9 } } }
    const view = deriveRetrieval({ ...run, traces: [...run.traces, otherCall] }, null)

    expect(stage(view!, 'selection')).toMatchObject({ enabled: true, summary: 'selected · 812 tokens' })
  })

  it('keeps the selection report when a later search call fails and calls carry no ids', () => {
    const run = runWithOutput(SEARCH_OUTPUT_FULL, { selection: SELECTION_DIAGNOSTICS })
    const succeeded = { ...run.traces[0]!, invocation_id: null }
    const failed = { ...succeeded, status: 'error', output: null, diagnostics: null, error: { error_type: 'ToolInputValidationError', message: 'm' } }
    const view = deriveRetrieval(
      {
        ...run,
        tool_results: [
          { ...run.tool_results[0]!, invocation_id: null },
          { ...run.tool_results[0]!, invocation_id: null, status: 'error', output: null, error: failed.error },
        ],
        traces: [succeeded, failed],
      },
      null,
    )

    expect(stage(view!, 'selection')).toMatchObject({ enabled: true, summary: 'selected · 812 tokens' })
  })

  it('returns null while the run has no successful search result', () => {
    expect(deriveRetrieval(awaitingApprovalRun(), null)).toBeNull()
    expect(
      deriveRetrieval(
        makeRun({
          tool_results: [
            { tool_name: 'search_documents', invocation_id: 'call-1', arguments: {}, status: 'error', output: null, error: { error_type: 'E', message: 'm' } },
          ],
        }),
        null,
      ),
    ).toBeNull()
  })

  it('skips malformed evidence instead of guessing', () => {
    const view = deriveRetrieval(runWithOutput({ query: 'q', results: [{ document_id: 5 }, 'x', { document_id: 'a#1', score: 0.5 }] }), null)

    expect(view?.evidence.map((item) => item.documentId)).toEqual(['a#1'])
  })
})
