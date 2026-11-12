import type { PendingApproval, RunDetail, RunEvent, RunSummary, SystemInfo } from '../api/types'

type Payload = RunEvent['payload']

/** Builds an ordered event list with increasing sequence numbers and timestamps. */
export class EventBuilder {
  private sequence = 0
  private clock: number
  readonly events: RunEvent[] = []

  constructor(
    private readonly runId = 'run-1',
    start = 1000,
  ) {
    this.clock = start
  }

  add(kind: string, payload: Payload = {}, advanceSeconds = 0.01): this {
    this.sequence += 1
    this.clock += advanceSeconds
    this.events.push({
      run_id: this.runId,
      sequence: this.sequence,
      timestamp: this.clock,
      kind,
      payload,
    })
    return this
  }

  transition(from: string, to: string, advance = 0.001): this {
    return this.add('state_transitioned', { from_status: from, to_status: to }, advance)
  }

  modelCall(iteration: number, seconds: number, input: number, output: number): this {
    this.add('model_call_started', { iteration })
    return this.add(
      'model_call_completed',
      { iteration, duration_seconds: seconds, finish_reason: 'stop', input_tokens: input, output_tokens: output, error: null },
      seconds,
    )
  }

  toolProposal(tool: string, args: Record<string, unknown>, id = 'call-1'): this {
    this.add('tool_proposed', { tool_name: tool, arguments: args, invocation_id: id })
    this.add('tool_validated', { tool_name: tool, accepted: true, invocation_id: id, error_type: null, error_message: null })
    return this
  }

  policy(tool: string, decision: string, id = 'call-1', reason: string | null = null): this {
    return this.add('tool_policy_decided', { tool_name: tool, decision, invocation_id: id, reason })
  }

  toolFinished(tool: string, status: string, seconds: number | null, executed = true, id = 'call-1', error: string | null = null): this {
    return this.add(
      'tool_call_finished',
      {
        tool_name: tool,
        status,
        executed,
        invocation_id: id,
        duration_seconds: seconds,
        error_type: error ? 'Error' : null,
        error_message: error,
      },
      seconds ?? 0.01,
    )
  }

  finish(outcome = 'responded', terminal = 'completed', iterations = 2): this {
    return this.add('run_finished', { outcome, terminal_status: terminal, model_iterations: iterations, error_message: null })
  }
}

/** A complete run that searched documents once and answered. */
export function successEvents(): RunEvent[] {
  return new EventBuilder()
    .add('run_started', { model_id: 'llama3.2:1b', max_model_iterations: 4 })
    .transition('start', 'context')
    .transition('context', 'think')
    .modelCall(1, 0.842, 412, 38)
    .transition('think', 'action_proposed')
    .toolProposal('search_documents', { query: 'tool policy' })
    .transition('action_proposed', 'runtime_validate')
    .policy('search_documents', 'allow')
    .transition('runtime_validate', 'tool_call')
    .toolFinished('search_documents', 'success', 0.061)
    .transition('tool_call', 'think')
    .modelCall(2, 1.31, 1186, 74)
    .transition('think', 'action_proposed')
    .transition('action_proposed', 'runtime_validate')
    .transition('runtime_validate', 'respond')
    .transition('respond', 'completed')
    .finish().events
}

export const SEARCH_OUTPUT_DENSE = {
  query: 'tool policy',
  result_count: 2,
  results: [
    {
      document_id: 'architecture.md#chunk-0007',
      score: 0.7412,
      content: 'Tools are the controlled interface between the agent and external systems.',
      content_truncated: false,
      metadata: { source_kind: 'preloaded', source_name: 'architecture.md' },
    },
    {
      document_id: 'demo-guide.txt#chunk-0000',
      score: 0.6127,
      content: 'The model can propose either the search_documents tool or the calculator.',
      content_truncated: true,
      metadata: { source_kind: 'preloaded', source_name: 'demo-guide.txt' },
    },
  ],
}

function stage(strategy: string, scoreKind: string, score: number, rank: number, extra: Record<string, unknown> = {}) {
  return { strategy, score_kind: scoreKind, score, rank, configuration_id: 'cfg', model_id: null, candidate_count: null, duration_seconds: null, ...extra }
}

export const SEARCH_OUTPUT_FULL = {
  query: 'tool policy',
  result_count: 1,
  results: [
    {
      document_id: 'architecture.md#chunk-0007',
      score: 0.91,
      content: 'Policy is applied before execution.',
      content_truncated: false,
      metadata: { source_kind: 'preloaded', source_name: 'architecture.md' },
      diagnostics: [
        stage('hybrid_dense', 'cosine', 0.74, 1),
        stage('hybrid_lexical', 'bm25', 11.2, 3),
        stage('hybrid', 'rrf', 0.032, 1, { candidate_count: 20, duration_seconds: 0.012 }),
        stage('reranking', 'cross_encoder', 8.4, 1, {
          model_id: 'cross-encoder/ms-marco-MiniLM-L6-v2',
          candidate_count: 20,
          duration_seconds: 0.4,
        }),
      ],
    },
  ],
}

/** Runtime-only selection report that the search tool records on its trace. */
export const SELECTION_DIAGNOSTICS = {
  status: 'selected',
  token_count: 812,
  candidates: [
    {
      candidate_id: 'architecture.md#chunk-0007',
      original_rank: 1,
      original_score: 0.91,
      reason: 'selected',
      overlap_fraction: null,
      provenance_status: 'verified',
    },
    {
      candidate_id: 'architecture.md#chunk-0008',
      original_rank: 2,
      original_score: 0.88,
      reason: 'excluded_overlap',
      overlap_fraction: 0.9,
      provenance_status: 'verified',
    },
  ],
}

export function makeRun(overrides: Partial<RunDetail> = {}): RunDetail {
  return {
    run_id: 'run-1',
    prompt: 'Which documents explain how tool policy works?',
    model_id: 'llama3.2:1b',
    max_model_iterations: 4,
    status: 'success',
    started_at: 1000,
    finished_at: 1003,
    model_iterations: 2,
    final_response: 'The architecture guide explains it.',
    outcome: 'responded',
    error_phase: null,
    error_message: null,
    pending_approval: null,
    events: successEvents(),
    tool_results: [
      {
        tool_name: 'search_documents',
        invocation_id: 'call-1',
        arguments: { query: 'tool policy' },
        status: 'success',
        output: SEARCH_OUTPUT_DENSE,
        error: null,
      },
    ],
    traces: [
      {
        tool_name: 'search_documents',
        invocation_id: 'call-1',
        arguments: { query: 'tool policy' },
        policy_decision: 'allow',
        approval_decision: null,
        status: 'success',
        output: SEARCH_OUTPUT_DENSE,
        error: null,
        diagnostics: null,
      },
    ],
    ...overrides,
  }
}

export function summaryOf(run: RunDetail): RunSummary {
  return {
    run_id: run.run_id,
    prompt: run.prompt,
    model_id: run.model_id,
    max_model_iterations: run.max_model_iterations,
    status: run.status,
    started_at: run.started_at,
    finished_at: run.finished_at,
    pending_approval: run.pending_approval,
    model_iterations: run.model_iterations,
    final_response: run.final_response,
    outcome: run.outcome,
    error_phase: run.error_phase,
    error_message: run.error_message,
  }
}

export const PENDING: PendingApproval = {
  tool_name: 'search_documents',
  arguments: { query: 'retention' },
  invocation_id: 'call-1',
  reason: 'Tool invocation requires explicit human approval: search_documents',
}

/** A run paused on a tool that requires approval. */
export function awaitingApprovalRun(): RunDetail {
  const events = new EventBuilder()
    .add('run_started', { model_id: 'llama3.2:1b', max_model_iterations: 4 })
    .transition('start', 'context')
    .transition('context', 'think')
    .modelCall(1, 0.79, 405, 36)
    .transition('think', 'action_proposed')
    .toolProposal('search_documents', { query: 'retention' })
    .transition('action_proposed', 'runtime_validate')
    .policy('search_documents', 'require_approval', 'call-1', PENDING.reason)
    .transition('runtime_validate', 'tool_call')
    .add('tool_approval_requested', {
      tool_name: 'search_documents',
      arguments: { query: 'retention' },
      invocation_id: 'call-1',
      reason: PENDING.reason,
    }).events
  return makeRun({
    status: 'awaiting_approval',
    finished_at: null,
    model_iterations: 1,
    final_response: null,
    outcome: null,
    pending_approval: PENDING,
    events,
    tool_results: [],
    traces: [],
  })
}

export function makeSystem(overrides: Record<string, unknown> = {}): SystemInfo {
  return {
    settings: {
      model_id: 'llama3.2:1b',
      retrieval_strategy: 'dense',
      embedding_model_id: 'sentence-transformers/all-MiniLM-L6-v2',
      max_model_iterations: 4,
      max_output_tokens: 256,
      reranking_enabled: false,
      evidence_selection_enabled: false,
      approval_required_tools: [],
      approval_timeout_seconds: 120,
      ...overrides,
    },
    tools: [
      { name: 'calculator', description: 'Evaluate arithmetic.' },
      { name: 'search_documents', description: 'Search documents.' },
    ],
    prompt_presets: [{ name: 'Calculator', prompt: 'Use the calculator to compute 2 + 2.' }],
    dependencies: [
      { name: 'model', state: 'configured', detail: 'llama3.2:1b' },
      { name: 'vector_store', state: 'ready', detail: 'http://localhost:6333' },
    ],
    active_run_id: null,
  }
}
