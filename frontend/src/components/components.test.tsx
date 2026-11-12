import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import { PENDING, SEARCH_OUTPUT_FULL, awaitingApprovalRun, makeRun, makeSystem, summaryOf } from '../test/fixtures'
import { ApprovalCard } from './ApprovalCard'
import { Composer } from './Composer'
import { Inspector } from './Inspector'
import { RunCard } from './RunCard'

afterEach(() => vi.restoreAllMocks())

function renderCard(run = summaryOf(makeRun())) {
  return render(
    <MemoryRouter>
      <RunCard run={run} index={0} selected={false} detail={null} approvalTimeoutSeconds={120} onChanged={vi.fn()} />
    </MemoryRouter>,
  )
}

describe('ApprovalCard', () => {
  it('sends an explicit decision with the optional reason', async () => {
    const onDecide = vi.fn().mockResolvedValue(undefined)
    render(<ApprovalCard pending={PENDING} requestedAt={null} timeoutSeconds={120} onDecide={onDecide} />)

    expect(screen.getByText('search_documents')).toBeInTheDocument()
    expect(screen.getByText('{"query":"retention"}')).toBeInTheDocument()
    expect(screen.getByText(/unanswered after 120 s/)).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Reason (optional)'), 'Too risky')
    await userEvent.click(screen.getByRole('button', { name: 'Reject' }))

    expect(onDecide).toHaveBeenCalledWith('rejected', 'Too risky')
  })

  it('shows the server error when the decision is refused', async () => {
    const onDecide = vi.fn().mockRejectedValue(new Error('Run has no pending approval request.'))
    render(<ApprovalCard pending={PENDING} requestedAt={null} timeoutSeconds={null} onDecide={onDecide} />)

    await userEvent.click(screen.getByRole('button', { name: 'Approve' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('no pending approval')
  })

  it('counts down from the approval request time', () => {
    vi.useFakeTimers({ now: 1_050_000 })
    try {
      render(<ApprovalCard pending={PENDING} requestedAt={1000} timeoutSeconds={120} onDecide={vi.fn()} />)

      expect(screen.getByText(/1:10 left of the 2:00 timeout/)).toBeInTheDocument()
    } finally {
      vi.useRealTimers()
    }
  })
})

describe('Composer', () => {
  it('starts a run and reports it', async () => {
    const started = summaryOf(makeRun())
    const spy = vi.spyOn(api, 'startRun').mockResolvedValue(started)
    const onStarted = vi.fn()
    render(<Composer presets={[]} locked={false} modelId="llama3.2:1b" onStarted={onStarted} />)

    await userEvent.type(screen.getByLabelText('Prompt'), 'Compute 2 + 2')
    await userEvent.click(screen.getByRole('button', { name: /Run agent/ }))

    expect(spy).toHaveBeenCalledWith('Compute 2 + 2')
    await waitFor(() => expect(onStarted).toHaveBeenCalledWith(started))
  })

  it('is disabled while another run is active', () => {
    render(<Composer presets={[]} locked modelId={null} onStarted={vi.fn()} />)

    expect(screen.getByLabelText('Prompt')).toBeDisabled()
    expect(screen.getByRole('button', { name: /Run agent/ })).toBeDisabled()
    expect(screen.getByLabelText('Prompt')).toHaveAttribute('placeholder', expect.stringContaining('A run is in progress'))
  })

  it('fills the prompt from a preset', async () => {
    render(
      <Composer presets={[{ name: 'Calculator', prompt: 'Use the calculator.' }]} locked={false} modelId={null} onStarted={vi.fn()} />,
    )

    await userEvent.selectOptions(screen.getByLabelText('Preset'), 'Calculator')

    expect(screen.getByLabelText('Prompt')).toHaveValue('Use the calculator.')
  })

  it('shows a refused start without clearing the prompt', async () => {
    vi.spyOn(api, 'startRun').mockRejectedValue(new Error('Run abc is still active'))
    render(<Composer presets={[]} locked={false} modelId={null} onStarted={vi.fn()} />)

    await userEvent.type(screen.getByLabelText('Prompt'), 'again')
    await userEvent.click(screen.getByRole('button', { name: /Run agent/ }))

    expect(await screen.findByRole('alert')).toHaveTextContent('still active')
    expect(screen.getByLabelText('Prompt')).toHaveValue('again')
  })
})

describe('RunCard', () => {
  it('renders the status the API reports, with the answer, for a success', () => {
    renderCard()

    expect(screen.getByText('Success')).toBeInTheDocument()
    expect(screen.getByText('The architecture guide explains it.')).toBeInTheDocument()
  })

  it('never presents a failed run as a success', () => {
    renderCard(
      summaryOf(
        makeRun({
          status: 'failed',
          error_phase: 'tool_execution',
          error_message: 'CalculatorEvaluationError: Division by zero',
          final_response: 'I cannot divide by zero.',
        }),
      ),
    )

    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(screen.queryByText('Success')).not.toBeInTheDocument()
    expect(screen.getByText('Run failed in tool_execution.')).toBeInTheDocument()
    expect(screen.getByText(/not shown as a successful answer/)).toBeInTheDocument()
  })

  it('reports an iteration limit without an answer', () => {
    renderCard(summaryOf(makeRun({ status: 'limit_reached', final_response: null, error_message: 'limit', model_iterations: 4 })))

    expect(screen.getByText('Limit reached')).toBeInTheDocument()
    expect(screen.getByText('Iteration limit reached.')).toBeInTheDocument()
    expect(screen.getByText('4 of 4 model iterations')).toBeInTheDocument()
  })

  it('offers approve and reject for a run awaiting approval and sends the decision', async () => {
    const spy = vi.spyOn(api, 'decideApproval').mockResolvedValue(summaryOf(makeRun()))
    const onChanged = vi.fn()
    render(
      <MemoryRouter>
        <RunCard run={summaryOf(awaitingApprovalRun())} index={0} selected detail={null} approvalTimeoutSeconds={120} onChanged={onChanged} />
      </MemoryRouter>,
    )

    expect(screen.getByText('Awaiting approval')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Approve' }))

    expect(spy).toHaveBeenCalledWith('run-1', 'approved', '')
    await waitFor(() => expect(onChanged).toHaveBeenCalled())
  })
})

describe('Inspector', () => {
  const renderInspector = (run = makeRun(), system = makeSystem()) =>
    render(
      <MemoryRouter>
        <Inspector run={run} system={system} section={null} />
      </MemoryRouter>,
    )

  it('shows the default dense run: lifecycle, one pipeline stage, evidence, trace, configuration and runtime states', () => {
    renderInspector()

    const lifecycle = screen.getByRole('region', { name: 'Execution lifecycle' })
    expect(lifecycle).toHaveTextContent('Policy decision')
    const pipeline = screen.getByRole('region', { name: 'Retrieval pipeline' })
    expect(pipeline).toHaveTextContent('strategy: dense')
    expect(pipeline).toHaveTextContent('Enabled by the hybrid strategy')
    expect(screen.getByRole('region', { name: 'Retrieved evidence' })).toHaveTextContent('architecture.md')
    expect(screen.getByRole('region', { name: 'Tool execution trace' })).toHaveTextContent('1 invocation')
    expect(screen.getByRole('region', { name: 'Run configuration' })).toHaveTextContent('search_documents')
    const states = screen.getByRole('region', { name: 'Runtime states' })
    expect(states).toHaveTextContent('Recorded from run events')
    expect(states).toHaveTextContent('Model call 1')
    expect(states).toHaveTextContent('1,598')
  })

  it('shows per-stage scores and selection diagnostics for the full pipeline', () => {
    const run = makeRun({
      tool_results: [
        { tool_name: 'search_documents', invocation_id: 'call-1', arguments: {}, status: 'success', output: SEARCH_OUTPUT_FULL as never, error: null },
      ],
    })
    renderInspector(run, makeSystem({ retrieval_strategy: 'hybrid' }))

    const pipeline = screen.getByRole('region', { name: 'Retrieval pipeline' })
    expect(pipeline).toHaveTextContent('strategy: hybrid')
    expect(pipeline).toHaveTextContent('cross-encoder/ms-marco-MiniLM-L6-v2')
    const evidence = screen.getByRole('region', { name: 'Retrieved evidence' })
    expect(evidence).toHaveTextContent('hybrid_lexical')
    expect(evidence).toHaveTextContent('excluded_overlap')
  })

  it('names the failing phase and the error for a failed run', () => {
    renderInspector(
      makeRun({
        status: 'failed',
        error_phase: 'tool_execution',
        error_message: 'CalculatorEvaluationError: Division by zero',
        traces: [
          {
            tool_name: 'calculator',
            invocation_id: 'call-1',
            arguments: { expression: '10 / 0' },
            policy_decision: 'allow',
            approval_decision: null,
            status: 'error',
            output: null,
            error: { error_type: 'CalculatorEvaluationError', message: 'Division by zero' },
          },
        ],
      }),
    )

    expect(screen.getByText('Failing phase: tool_execution')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Tool execution trace' })).toHaveTextContent('Division by zero')
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('shows a run awaiting approval as live, with the pending call and no retrieval yet', () => {
    renderInspector(awaitingApprovalRun())

    expect(screen.getByText('Live — paused for a decision')).toBeInTheDocument()
    expect(screen.getByText('1 of 4')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Execution lifecycle' })).toHaveTextContent('awaiting')
    expect(screen.getByRole('region', { name: 'Tool execution trace' })).toHaveTextContent('not executed')
    expect(screen.getByRole('region', { name: 'Retrieval pipeline' })).toHaveTextContent('not streamed live')
    expect(screen.getByRole('region', { name: 'Runtime states' })).toHaveTextContent('Filling in live')
  })
})
