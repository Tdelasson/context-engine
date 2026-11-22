import type { RunEvent } from './types'

/** Event kinds the server names its SSE frames after (ADR-015). */
export const EVENT_KINDS = [
  'run_started',
  'state_transitioned',
  'model_call_started',
  'model_call_completed',
  'tool_proposed',
  'tool_validated',
  'tool_policy_decided',
  'tool_approval_requested',
  'tool_approval_resolved',
  'tool_call_finished',
  'run_finished',
] as const

export interface EventSourceLike {
  addEventListener(type: string, listener: (event: MessageEvent<string>) => void): void
  close(): void
  onerror: ((event: Event) => void) | null
}

export type EventSourceFactory = (url: string) => EventSourceLike

export interface StreamHandlers {
  onEvent: (event: RunEvent) => void
  /** The server closed the stream after `run_finished`. */
  onEnd: () => void
  onError?: () => void
}

const defaultFactory: EventSourceFactory = (url) => new EventSource(url)

/**
 * Follow a run's events. The server replays everything after `afterSequence`, then
 * streams live and ends with `run_finished`; the browser reconnects on its own and resumes
 * through `Last-Event-ID`. Returns a function that stops following.
 */
export function subscribeToRunEvents(
  runId: string,
  afterSequence: number,
  handlers: StreamHandlers,
  factory: EventSourceFactory = defaultFactory,
): () => void {
  const url = `/api/v1/runs/${encodeURIComponent(runId)}/events?after=${afterSequence}`
  const source = factory(url)
  let closed = false
  const close = () => {
    if (closed) return
    closed = true
    source.close()
  }

  for (const kind of EVENT_KINDS) {
    source.addEventListener(kind, (message) => {
      if (closed) return
      handlers.onEvent(JSON.parse(message.data) as RunEvent)
      if (kind === 'run_finished') {
        close()
        handlers.onEnd()
      }
    })
  }
  source.onerror = () => {
    if (!closed) handlers.onError?.()
  }
  return close
}
