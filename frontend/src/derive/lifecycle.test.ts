import { describe, expect, it } from 'vitest'
import { EventBuilder, awaitingApprovalRun, makeRun, successEvents } from '../test/fixtures'
import { countToolCalls, deriveLifecycle } from './lifecycle'

const byId = (steps: ReturnType<typeof deriveLifecycle>, id: string) => steps.find((step) => step.id === id)

describe('deriveLifecycle', () => {
  it('shows every step of a successful run as complete', () => {
    const steps = deriveLifecycle(makeRun())

    expect(steps.map((step) => step.title)).toEqual([
      'User prompt',
      'Model tool proposal',
      'Registry + schema validation',
      'Policy decision',
      'Tool execution',
      'Structured ToolResult',
      'Final model response',
    ])
    expect(steps.every((step) => step.state === 'complete')).toBe(true)
    expect(byId(steps, 'tool-0-proposal')?.detail).toBe('search_documents {"query":"tool policy"}')
    expect(byId(steps, 'tool-0-policy')?.badge).toBe('allow')
  })

  it('marks a tool error as failed while the model answer still completes', () => {
    const events = new EventBuilder()
      .add('run_started', { model_id: 'm', max_model_iterations: 4 })
      .toolProposal('calculator', { expression: '10 / 0' })
      .policy('calculator', 'allow')
      .toolFinished('calculator', 'error', 0.004, true, 'call-1', 'Division by zero')
      .finish().events

    const steps = deriveLifecycle(makeRun({ status: 'failed', events }))

    expect(byId(steps, 'tool-0-execution')).toMatchObject({ state: 'failed', badge: 'error', detail: 'Division by zero' })
    expect(byId(steps, 'tool-0-result')?.state).toBe('failed')
    expect(byId(steps, 'final-response')?.state).toBe('complete')
  })

  it('shows a run awaiting approval with the approval step active and later steps pending', () => {
    const steps = deriveLifecycle(awaitingApprovalRun())

    expect(byId(steps, 'tool-0-policy')).toMatchObject({ badge: 'require approval', state: 'complete' })
    expect(byId(steps, 'tool-0-approval')).toMatchObject({ state: 'active', badge: 'awaiting' })
    expect(byId(steps, 'tool-0-execution')?.state).toBe('pending')
    expect(byId(steps, 'final-response')?.state).toBe('pending')
    expect(steps.filter((step) => step.state === 'active')).toHaveLength(1)
  })

  it('shows a rejected approval as failed and the tool as not executed', () => {
    const builder = new EventBuilder()
      .add('run_started', { model_id: 'm', max_model_iterations: 4 })
      .toolProposal('search_documents', { query: 'x' })
      .policy('search_documents', 'require_approval')
      .add('tool_approval_requested', { tool_name: 'search_documents', arguments: {}, invocation_id: 'call-1', reason: null })
      .add('tool_approval_resolved', { tool_name: 'search_documents', decision: 'rejected', invocation_id: 'call-1', reason: 'Too risky' })
      .toolFinished('search_documents', 'error', null, false, 'call-1', 'rejected')
      .finish()

    const steps = deriveLifecycle(makeRun({ status: 'failed', events: builder.events }))

    expect(byId(steps, 'tool-0-approval')).toMatchObject({ state: 'failed', badge: 'rejected', detail: 'Too risky' })
    expect(byId(steps, 'tool-0-execution')).toMatchObject({ state: 'skipped', detail: 'Not executed' })
  })

  it('activates the first pending step of a running run', () => {
    const events = new EventBuilder()
      .add('run_started', { model_id: 'm', max_model_iterations: 4 })
      .toolProposal('search_documents', { query: 'x' })
      .policy('search_documents', 'allow')
      .events

    const steps = deriveLifecycle(makeRun({ status: 'running', outcome: null, final_response: null, events }))

    expect(byId(steps, 'tool-0-execution')).toMatchObject({ state: 'active', badge: 'in progress' })
    expect(byId(steps, 'tool-0-result')?.state).toBe('pending')
    expect(byId(steps, 'final-response')?.state).toBe('pending')
  })

  it('does not reach policy or execution when validation rejects the call', () => {
    const events = new EventBuilder()
      .add('run_started', { model_id: 'm', max_model_iterations: 4 })
      .add('tool_proposed', { tool_name: 'nope', arguments: {}, invocation_id: 'call-1' })
      .add('tool_validated', { tool_name: 'nope', accepted: false, invocation_id: 'call-1', error_message: 'Unknown tool' })
      .finish('failed', 'failed', 1).events

    const steps = deriveLifecycle(makeRun({ status: 'failed', outcome: 'failed', events }))

    expect(byId(steps, 'tool-0-validation')).toMatchObject({ state: 'failed', detail: 'Unknown tool' })
    expect(byId(steps, 'tool-0-policy')?.state).toBe('skipped')
    expect(byId(steps, 'tool-0-execution')?.state).toBe('skipped')
    expect(byId(steps, 'final-response')?.state).toBe('failed')
  })

  it('numbers steps when several tools were called and reports a limit as failed', () => {
    const builder = new EventBuilder().add('run_started', { model_id: 'm', max_model_iterations: 2 })
    for (const id of ['call-1', 'call-2']) {
      builder.toolProposal('search_documents', { query: id }, id).policy('search_documents', 'allow', id)
      builder.toolFinished('search_documents', 'success', 0.05, true, id)
    }
    builder.finish('limit_reached', 'failed', 2)

    const run = makeRun({ status: 'limit_reached', outcome: 'limit_reached', final_response: null, error_message: 'limit', events: builder.events })
    const steps = deriveLifecycle(run)

    expect(countToolCalls(run)).toBe(2)
    expect(steps.some((step) => step.title.startsWith('#2 '))).toBe(true)
    expect(byId(steps, 'final-response')).toMatchObject({ state: 'failed', badge: 'limit reached' })
  })

  it('shows only the prompt and the answer when no tool was proposed', () => {
    const events = new EventBuilder().add('run_started', { model_id: 'm', max_model_iterations: 4 }).finish('responded', 'completed', 1).events

    const steps = deriveLifecycle(makeRun({ events }))

    expect(steps.map((step) => step.id)).toEqual(['prompt', 'final-response'])
  })

  it('does not change the successful fixture when events arrive in the same order', () => {
    expect(deriveLifecycle(makeRun({ events: successEvents() }))).toEqual(deriveLifecycle(makeRun()))
  })
})
