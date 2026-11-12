import { describe, expect, it } from 'vitest'
import { EventBuilder, awaitingApprovalRun, successEvents } from '../test/fixtures'
import { deriveTimings, deriveTokenUsage, deriveTransitions } from './timeline'

describe('deriveTransitions', () => {
  it('lists state transitions with offsets from the first event', () => {
    const transitions = deriveTransitions(successEvents())

    expect(transitions[0]).toMatchObject({ from: 'start', to: 'context' })
    expect(transitions.at(-1)).toMatchObject({ from: 'respond', to: 'completed' })
    expect(transitions.map((item) => item.offsetSeconds)).toEqual(
      [...transitions.map((item) => item.offsetSeconds)].sort((a, b) => a - b),
    )
    expect(transitions[0]?.offsetSeconds).toBeGreaterThan(0)
  })
})

describe('deriveTimings', () => {
  it('reports model calls and tool execution durations in order', () => {
    const timings = deriveTimings(successEvents())

    expect(timings.map((timing) => [timing.label, timing.durationSeconds, timing.running])).toEqual([
      ['Model call 1', 0.842, false],
      ['Tool execution', 0.061, false],
      ['Model call 2', 1.31, false],
    ])
  })

  it('keeps a model call running until it completes', () => {
    const events = new EventBuilder().add('run_started', {}).add('model_call_started', { iteration: 1 }).events

    expect(deriveTimings(events)).toEqual([
      { id: 'model-1', kind: 'model', label: 'Model call 1', durationSeconds: null, running: true },
    ])
  })

  it('times the wait for approval and leaves it running while unanswered', () => {
    const waiting = deriveTimings(awaitingApprovalRun().events)
    expect(waiting.find((timing) => timing.kind === 'approval')).toMatchObject({ running: true, durationSeconds: null })

    const events = new EventBuilder()
      .add('tool_approval_requested', { tool_name: 't' })
      .add('tool_approval_resolved', { tool_name: 't', decision: 'approved' }, 18)
      .events
    const resolved = deriveTimings(events).find((timing) => timing.kind === 'approval')
    expect(resolved?.running).toBe(false)
    expect(resolved?.durationSeconds).toBeCloseTo(18)
  })

  it('does not time a tool that was never executed', () => {
    const events = new EventBuilder().toolFinished('search_documents', 'error', null, false).events

    expect(deriveTimings(events)).toEqual([])
  })
})

describe('deriveTokenUsage', () => {
  it('totals the tokens the model reported', () => {
    expect(deriveTokenUsage(successEvents())).toEqual({
      calls: [
        { iteration: 1, input: 412, output: 38 },
        { iteration: 2, input: 1186, output: 74 },
      ],
      totalInput: 1598,
      totalOutput: 112,
    })
  })

  it('keeps unreported tokens as null and out of the totals', () => {
    const events = new EventBuilder().add('model_call_completed', { iteration: 1, duration_seconds: 1, input_tokens: null, output_tokens: null }).events

    expect(deriveTokenUsage(events)).toEqual({
      calls: [{ iteration: 1, input: null, output: null }],
      totalInput: 0,
      totalOutput: 0,
    })
  })
})
