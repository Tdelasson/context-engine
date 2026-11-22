import { asBoolean, asNumber, asString } from '../api/json'
import type { RunEvent } from '../api/types'

export interface Transition {
  sequence: number
  offsetSeconds: number
  from: string
  to: string
}

export interface Timing {
  id: string
  kind: 'model' | 'tool' | 'approval'
  label: string
  /** Null while the step is still running. */
  durationSeconds: number | null
  running: boolean
}

export interface TokenCall {
  iteration: number
  input: number | null
  output: number | null
}

export interface TokenUsage {
  calls: TokenCall[]
  totalInput: number
  totalOutput: number
}

function origin(events: readonly RunEvent[]): number {
  return events[0]?.timestamp ?? 0
}

export function deriveTransitions(events: readonly RunEvent[]): Transition[] {
  const start = origin(events)
  const transitions: Transition[] = []
  for (const event of events) {
    if (event.kind !== 'state_transitioned') continue
    transitions.push({
      sequence: event.sequence,
      offsetSeconds: Math.max(0, event.timestamp - start),
      from: asString(event.payload.from_status) ?? '?',
      to: asString(event.payload.to_status) ?? '?',
    })
  }
  return transitions
}

export function deriveTimings(events: readonly RunEvent[]): Timing[] {
  const timings: Timing[] = []
  const modelCalls = new Map<number, Timing>()
  let approvalRequestedAt: number | null = null
  let approvalIndex = 0

  for (const event of events) {
    switch (event.kind) {
      case 'model_call_started': {
        const iteration = asNumber(event.payload.iteration) ?? modelCalls.size + 1
        const timing: Timing = {
          id: `model-${iteration}`,
          kind: 'model',
          label: `Model call ${iteration}`,
          durationSeconds: null,
          running: true,
        }
        modelCalls.set(iteration, timing)
        timings.push(timing)
        break
      }
      case 'model_call_completed': {
        const iteration = asNumber(event.payload.iteration) ?? 0
        const timing = modelCalls.get(iteration)
        if (timing) {
          timing.durationSeconds = asNumber(event.payload.duration_seconds)
          timing.running = false
        }
        break
      }
      case 'tool_approval_requested':
        approvalRequestedAt = event.timestamp
        approvalIndex += 1
        timings.push({
          id: `approval-${approvalIndex}`,
          kind: 'approval',
          label: 'Waiting for approval',
          durationSeconds: null,
          running: true,
        })
        break
      case 'tool_approval_resolved': {
        const waiting = timings.findLast((item) => item.kind === 'approval' && item.running)
        if (waiting && approvalRequestedAt !== null) {
          waiting.durationSeconds = Math.max(0, event.timestamp - approvalRequestedAt)
          waiting.running = false
        }
        break
      }
      case 'tool_call_finished':
        if (asBoolean(event.payload.executed)) {
          timings.push({
            id: `tool-${event.sequence}`,
            kind: 'tool',
            label: 'Tool execution',
            durationSeconds: asNumber(event.payload.duration_seconds),
            running: false,
          })
        }
        break
    }
  }
  return timings
}

export function deriveTokenUsage(events: readonly RunEvent[]): TokenUsage {
  const calls: TokenCall[] = []
  let totalInput = 0
  let totalOutput = 0
  for (const event of events) {
    if (event.kind !== 'model_call_completed') continue
    const input = asNumber(event.payload.input_tokens)
    const output = asNumber(event.payload.output_tokens)
    calls.push({ iteration: asNumber(event.payload.iteration) ?? calls.length + 1, input, output })
    totalInput += input ?? 0
    totalOutput += output ?? 0
  }
  return { calls, totalInput, totalOutput }
}
