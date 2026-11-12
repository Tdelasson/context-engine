import { act, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { api } from './api/client'
import { subscribeToRunEvents } from './api/stream'
import type { StreamHandlers } from './api/stream'
import type { RunDetail } from './api/types'
import { EventBuilder, awaitingApprovalRun, makeRun, makeSystem, summaryOf } from './test/fixtures'

vi.mock('./api/stream', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./api/stream')>()),
  subscribeToRunEvents: vi.fn(),
}))

const subscribe = vi.mocked(subscribeToRunEvents)

function mockApi(detail: () => RunDetail) {
  vi.spyOn(api, 'listRuns').mockImplementation(async () => [summaryOf(detail())])
  vi.spyOn(api, 'getSystem').mockResolvedValue(makeSystem())
  vi.spyOn(api, 'getRun').mockImplementation(async () => detail())
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

beforeEach(() => subscribe.mockReset())
afterEach(() => vi.restoreAllMocks())

describe('App', () => {
  it('restores a finished run from the API on load, without opening an event stream', async () => {
    const run = makeRun()
    mockApi(() => run)

    renderAt('/runs/run-1')

    const inspector = await screen.findByRole('complementary', { name: 'Technical view' })
    expect(within(inspector).getByRole('region', { name: 'Execution lifecycle' })).toBeInTheDocument()
    expect(screen.getByText('The architecture guide explains it.')).toBeInTheDocument()
    expect(within(screen.getByRole('navigation', { name: 'Primary' })).getByRole('link', { name: /Which documents explain/ })).toBeInTheDocument()
    expect(within(screen.getByLabelText('Dependency status')).getByText('model')).toBeInTheDocument()
    expect(subscribe).not.toHaveBeenCalled()
  })

  it('follows a running run live, then reloads the final record when the stream ends', async () => {
    const live = new EventBuilder()
      .add('run_started', { model_id: 'llama3.2:1b', max_model_iterations: 4 })
      .add('model_call_started', { iteration: 1 })
    const running = makeRun({ status: 'running', outcome: null, final_response: null, finished_at: null, events: live.events, tool_results: [], traces: [] })
    const finished = makeRun()
    let current = running
    mockApi(() => current)

    renderAt('/runs/run-1')

    await screen.findByRole('complementary', { name: 'Technical view' })
    expect(screen.getAllByText('Running').length).toBeGreaterThan(0)
    expect(screen.getByLabelText('Prompt')).toBeDisabled()
    await waitFor(() => expect(subscribe).toHaveBeenCalledTimes(1))
    const [runId, after, handlers] = subscribe.mock.calls[0] as [string, number, StreamHandlers]
    expect(runId).toBe('run-1')
    expect(after).toBe(2)

    act(() => {
      live.add('model_call_completed', { iteration: 1, duration_seconds: 0.842, input_tokens: 412, output_tokens: 38 })
      handlers.onEvent(live.events.at(-1)!)
    })
    expect(screen.getByRole('region', { name: 'Runtime states' })).toHaveTextContent('842 ms')

    current = finished
    await act(async () => handlers.onEnd())

    expect(await screen.findByText('The architecture guide explains it.')).toBeInTheDocument()
    expect(screen.getAllByText('Success').length).toBeGreaterThan(0)
    await waitFor(() => expect(screen.getByLabelText('Prompt')).toBeEnabled())
  })

  it('shows approve and reject for a run awaiting approval and refreshes after a decision', async () => {
    const waiting = awaitingApprovalRun()
    let current = waiting
    mockApi(() => current)
    const decide = vi.spyOn(api, 'decideApproval').mockImplementation(async () => {
      current = makeRun({ run_id: 'run-1' })
      return summaryOf(current)
    })

    renderAt('/runs/run-1')

    const approve = await screen.findByRole('button', { name: 'Approve' })
    expect(screen.getByRole('button', { name: 'Reject' })).toBeInTheDocument()
    await act(async () => approve.click())

    expect(decide).toHaveBeenCalledWith('run-1', 'approved', '')
  })

  it('shows the thread and an unlocked composer at /runs, and redirects unknown paths there', async () => {
    const run = makeRun()
    mockApi(() => run)

    renderAt('/nowhere')

    expect(await screen.findByLabelText('Prompt')).toBeEnabled()
    expect(screen.queryByRole('complementary', { name: 'Technical view' })).not.toBeInTheDocument()
    expect(await screen.findByText('The architecture guide explains it.')).toBeInTheDocument()
  })

  it('reports an unreachable API instead of an empty success', async () => {
    vi.spyOn(api, 'listRuns').mockRejectedValue(new Error('Failed to fetch'))
    vi.spyOn(api, 'getSystem').mockRejectedValue(new Error('Failed to fetch'))

    renderAt('/runs')

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach the API: Failed to fetch')
  })
})
