import { asBoolean, asNumber, asString, isRecord } from '../api/json'
import { isActive } from '../api/types'
import type { RunDetail, RunEvent } from '../api/types'

export type StepState = 'complete' | 'active' | 'pending' | 'failed' | 'skipped'

export interface LifecycleStep {
  id: string
  title: string
  state: StepState
  badge: string
  detail?: string
}

interface Invocation {
  id: string | null
  tool: string
  args: Record<string, unknown>
  validated?: { accepted: boolean; error: string | null }
  policy?: { decision: string; reason: string | null }
  approvalRequested: boolean
  approval?: { decision: string; reason: string | null }
  finished?: { status: string; executed: boolean; error: string | null }
}

function payloadString(event: RunEvent, key: string): string | null {
  return asString(event.payload[key])
}

function groupInvocations(events: readonly RunEvent[]): Invocation[] {
  const invocations: Invocation[] = []
  const latest = (tool: string, id: string | null): Invocation | undefined => {
    for (let index = invocations.length - 1; index >= 0; index -= 1) {
      const candidate = invocations[index]
      if (candidate && candidate.tool === tool && (id === null || candidate.id === id)) {
        return candidate
      }
    }
    return undefined
  }

  for (const event of events) {
    const tool = payloadString(event, 'tool_name')
    if (tool === null) continue
    const id = payloadString(event, 'invocation_id')
    if (event.kind === 'tool_proposed') {
      const args = event.payload.arguments
      invocations.push({
        id,
        tool,
        args: isRecord(args) ? args : {},
        approvalRequested: false,
      })
      continue
    }
    const invocation = latest(tool, id)
    if (!invocation) continue
    switch (event.kind) {
      case 'tool_validated':
        invocation.validated = {
          accepted: asBoolean(event.payload.accepted) ?? false,
          error: payloadString(event, 'error_message'),
        }
        break
      case 'tool_policy_decided':
        invocation.policy = {
          decision: payloadString(event, 'decision') ?? 'unknown',
          reason: payloadString(event, 'reason'),
        }
        break
      case 'tool_approval_requested':
        invocation.approvalRequested = true
        break
      case 'tool_approval_resolved':
        invocation.approval = {
          decision: payloadString(event, 'decision') ?? 'unknown',
          reason: payloadString(event, 'reason'),
        }
        break
      case 'tool_call_finished':
        invocation.finished = {
          status: payloadString(event, 'status') ?? 'unknown',
          executed: asBoolean(event.payload.executed) ?? false,
          error: payloadString(event, 'error_message'),
        }
        break
    }
  }
  return invocations
}

function invocationSteps(invocation: Invocation, prefix: string, index: number): LifecycleStep[] {
  const key = `tool-${index}`
  const steps: LifecycleStep[] = []
  const argsText = JSON.stringify(invocation.args)
  steps.push({
    id: `${key}-proposal`,
    title: `${prefix}Model tool proposal`,
    state: 'complete',
    badge: 'complete',
    detail: `${invocation.tool} ${argsText}`,
  })

  const validation = invocation.validated
  steps.push(
    validation
      ? {
          id: `${key}-validation`,
          title: `${prefix}Registry + schema validation`,
          state: validation.accepted ? 'complete' : 'failed',
          badge: validation.accepted ? 'complete' : 'rejected',
          detail: validation.accepted
            ? 'Registered tool and typed arguments accepted'
            : (validation.error ?? 'Validation failed'),
        }
      : pendingStep(`${key}-validation`, `${prefix}Registry + schema validation`),
  )

  const validationFailed = validation !== undefined && !validation.accepted
  if (invocation.policy) {
    const decision = invocation.policy.decision
    steps.push({
      id: `${key}-policy`,
      title: `${prefix}Policy decision`,
      state: decision === 'deny' ? 'failed' : 'complete',
      badge: decision === 'require_approval' ? 'require approval' : decision,
      detail: invocation.policy.reason ?? 'No approval required',
    })
  } else if (validationFailed) {
    steps.push(skippedStep(`${key}-policy`, `${prefix}Policy decision`, 'Not reached'))
  } else {
    steps.push(pendingStep(`${key}-policy`, `${prefix}Policy decision`))
  }

  if (invocation.approvalRequested || invocation.approval) {
    const approval = invocation.approval
    steps.push(
      approval
        ? {
            id: `${key}-approval`,
            title: `${prefix}Human approval`,
            state: approval.decision === 'approved' ? 'complete' : 'failed',
            badge: approval.decision,
            detail: approval.reason ?? undefined,
          }
        : {
            id: `${key}-approval`,
            title: `${prefix}Human approval`,
            state: 'active',
            badge: 'awaiting',
            detail: 'Blocks the run until a person answers',
          },
    )
  }

  const finished = invocation.finished
  if (finished) {
    if (finished.executed) {
      const ok = finished.status === 'success'
      steps.push({
        id: `${key}-execution`,
        title: `${prefix}Tool execution`,
        state: ok ? 'complete' : 'failed',
        badge: finished.status,
        detail: finished.error ?? 'Deterministic execution completed',
      })
      steps.push({
        id: `${key}-result`,
        title: `${prefix}Structured ToolResult`,
        state: ok ? 'complete' : 'failed',
        badge: finished.status,
        detail: ok
          ? 'Structured result returned to the model'
          : 'Structured error returned to the model; no output payload',
      })
    } else {
      steps.push(
        skippedStep(`${key}-execution`, `${prefix}Tool execution`, 'Not executed'),
        skippedStep(`${key}-result`, `${prefix}Structured ToolResult`, finished.error ?? 'None'),
      )
    }
  } else if (validationFailed) {
    steps.push(
      skippedStep(`${key}-execution`, `${prefix}Tool execution`, 'Not reached'),
      skippedStep(`${key}-result`, `${prefix}Structured ToolResult`, 'Not reached'),
    )
  } else {
    steps.push(
      pendingStep(`${key}-execution`, `${prefix}Tool execution`),
      pendingStep(`${key}-result`, `${prefix}Structured ToolResult`),
    )
  }
  return steps
}

function pendingStep(id: string, title: string): LifecycleStep {
  return { id, title, state: 'pending', badge: 'pending' }
}

function skippedStep(id: string, title: string, detail: string): LifecycleStep {
  return { id, title, state: 'skipped', badge: 'not reached', detail }
}

function finalStep(run: RunDetail): LifecycleStep {
  const id = 'final-response'
  const title = 'Final model response'
  if (isActive(run.status)) return pendingStep(id, title)
  if (run.outcome === 'responded') {
    return {
      id,
      title,
      state: 'complete',
      badge: 'complete',
      detail: 'Model text produced from the structured result',
    }
  }
  const limit = run.status === 'limit_reached'
  return {
    id,
    title,
    state: 'failed',
    badge: limit ? 'limit reached' : 'not produced',
    detail: run.error_message ?? undefined,
  }
}

/**
 * Derive the execution lifecycle from the run's events. The server's run status is shown
 * as reported; this function only arranges events into steps and never infers success.
 */
export function deriveLifecycle(run: RunDetail): LifecycleStep[] {
  const invocations = groupInvocations(run.events)
  const multiple = invocations.length > 1
  const steps: LifecycleStep[] = [
    {
      id: 'prompt',
      title: 'User prompt',
      state: 'complete',
      badge: 'complete',
      detail: 'Submitted to runtime',
    },
  ]
  invocations.forEach((invocation, index) => {
    steps.push(...invocationSteps(invocation, multiple ? `#${index + 1} ` : '', index))
  })
  steps.push(finalStep(run))

  if (isActive(run.status) && !steps.some((step) => step.state === 'active')) {
    const next = steps.find((step) => step.state === 'pending')
    if (next) {
      next.state = 'active'
      next.badge = 'in progress'
    }
  }
  return steps
}

export function countToolCalls(run: RunDetail): number {
  return run.events.filter((event) => event.kind === 'tool_proposed').length
}

export function lastIteration(run: RunDetail): number {
  let latest = 0
  for (const event of run.events) {
    if (event.kind === 'model_call_started') {
      latest = Math.max(latest, asNumber(event.payload.iteration) ?? 0)
    }
  }
  return latest
}
