import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { asString } from '../api/json'
import { isActive } from '../api/types'
import type { RunDetail, SystemInfo } from '../api/types'
import { formatCount, formatDuration, formatOffset, formatScore } from '../derive/format'
import { countToolCalls, deriveLifecycle, lastIteration } from '../derive/lifecycle'
import type { StepState } from '../derive/lifecycle'
import { deriveRetrieval } from '../derive/retrieval'
import { deriveTimings, deriveTokenUsage, deriveTransitions } from '../derive/timeline'
import ui from '../styles/ui.module.css'
import styles from './Inspector.module.css'
import { StatusTag, Tag } from './Tag'
import type { Tone } from './Tag'

const STEP_TONES: Record<StepState, Tone> = {
  complete: 'ok',
  active: 'warn',
  pending: 'planned',
  failed: 'bad',
  skipped: 'planned',
}

const TABS = [
  ['lifecycle', 'Lifecycle'],
  ['retrieval', 'Retrieval'],
  ['evidence', 'Evidence'],
  ['trace', 'Trace'],
  ['config', 'Configuration'],
  ['states', 'Runtime states'],
] as const

interface InspectorProps {
  run: RunDetail
  system: SystemInfo | null
  section: string | null
}

function currentState(run: RunDetail): string {
  const finished = run.events.findLast((event) => event.kind === 'run_finished')
  if (finished) return asString(finished.payload.terminal_status) ?? '—'
  const transition = run.events.findLast((event) => event.kind === 'state_transitioned')
  return transition ? (asString(transition.payload.to_status) ?? '—') : '—'
}

export function Inspector({ run, system, section }: InspectorProps) {
  useEffect(() => {
    if (section) document.getElementById(section)?.scrollIntoView?.({ block: 'start' })
  }, [section, run.run_id])

  const active = isActive(run.status)
  const lifecycle = deriveLifecycle(run)
  const retrieval = deriveRetrieval(run, system?.settings ?? null)
  const transitions = deriveTransitions(run.events)
  const timings = deriveTimings(run.events)
  const tokens = deriveTokenUsage(run.events)
  const longest = Math.max(0, ...timings.map((timing) => timing.durationSeconds ?? 0))
  const settings = system?.settings ?? null

  return (
    <aside className={styles.inspector} aria-label="Technical view">
      <header className={styles.head}>
        <div className={styles.title}>
          <h2>Technical view · {run.run_id.slice(0, 8)}</h2>
          <span>
            <StatusTag status={run.status} /> <Link to="/runs">Close ✕</Link>
          </span>
        </div>
        <div className={styles.sub}>{run.prompt}</div>
        <nav className={styles.tabs} aria-label="Inspector sections">
          {TABS.map(([id, label]) => (
            <Link key={id} to={`?section=${id}`} className={section === id ? styles.on : ''}>
              {label}
            </Link>
          ))}
        </nav>
      </header>

      <div className={styles.sect}>
        {active && (
          <div className={`${ui.eyebrow} ${styles.live}`}>
            {run.status === 'awaiting_approval' ? 'Live — paused for a decision' : 'Live — receiving run events'}
          </div>
        )}
        {(run.status === 'failed' || run.status === 'limit_reached') && (
          <div className={styles.failure}>
            <strong>Failing phase: {run.error_phase ?? 'unknown'}</strong>
            {run.error_message && <div className={ui.mono}>{run.error_message}</div>}
          </div>
        )}
        <div className={styles.facts}>
          <Fact value={run.outcome ?? '—'} label="Outcome" />
          <Fact value={`${Math.max(run.model_iterations, lastIteration(run))} of ${run.max_model_iterations}`} label="Model iterations" />
          <Fact value={String(countToolCalls(run))} label="Tool calls" />
          <Fact value={currentState(run)} label={active ? 'Current state' : 'Terminal state'} />
        </div>
      </div>

      <section className={styles.sect} id="lifecycle" aria-label="Execution lifecycle">
        <div className={ui.eyebrow}>Execution lifecycle</div>
        <ol className={styles.steps}>
          {lifecycle.map((step) => (
            <li key={step.id} className={step.state === 'pending' ? styles.pending : ''}>
              <span>{step.title}</span>
              <Tag tone={STEP_TONES[step.state]}>{step.badge}</Tag>
              {step.detail && <span className={styles.detail}>{step.detail}</span>}
            </li>
          ))}
        </ol>
      </section>

      <section className={styles.sect} id="retrieval" aria-label="Retrieval pipeline">
        <div className={styles.eyebrowRow}>
          <span className={ui.eyebrow}>Retrieval pipeline</span>
          {retrieval && <Tag>strategy: {retrieval.strategy}</Tag>}
        </div>
        {retrieval ? (
          <div className={styles.pipe}>
            {retrieval.stages.map((stage) => (
              <div key={stage.id} className={`${styles.stage} ${stage.enabled ? '' : styles.off}`}>
                <span className={styles.stageName}>{stage.name}</span>
                {stage.enabled ? (
                  <span className={ui.mono}>{formatDuration(stage.durationSeconds)}</span>
                ) : (
                  <Tag>off</Tag>
                )}
                <span className={styles.stageMeta}>{stage.summary}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className={styles.note}>
            {active
              ? 'Retrieval stages are not streamed live. They appear once the run has finished.'
              : 'This run has no successful document search.'}
          </p>
        )}
      </section>

      <section className={styles.sect} id="evidence" aria-label="Retrieved evidence">
        <div className={styles.eyebrowRow}>
          <span className={ui.eyebrow}>Retrieved evidence</span>
          {retrieval && <span>{retrieval.evidence.length} passages</span>}
        </div>
        {retrieval?.evidence.map((item) => (
          <article key={item.documentId} className={styles.ev}>
            <div className={styles.evHead}>
              <strong>{asString(item.metadata.source_name) ?? item.documentId}</strong>
              {asString(item.metadata.source_kind) && <Tag>{asString(item.metadata.source_kind)}</Tag>}
              <span className={styles.spacer} />
              <span className={ui.mono}>score {formatScore(item.score)}</span>
            </div>
            <div className={`${ui.mono} ${styles.muted}`}>{item.documentId}</div>
            <p className={styles.content}>{item.content}</p>
            {item.truncated && <Tag tone="warn">content truncated</Tag>}
            {item.stages.length > 0 && (
              <table className={styles.grid}>
                <thead>
                  <tr>
                    <th>Stage</th>
                    <th className={styles.n}>Score</th>
                    <th className={styles.n}>Rank</th>
                  </tr>
                </thead>
                <tbody>
                  {item.stages.map((stage) => (
                    <tr key={`${stage.strategy}-${stage.rank}`}>
                      <td>
                        {stage.strategy} <span className={styles.muted}>({stage.scoreKind})</span>
                      </td>
                      <td className={styles.n}>{formatScore(stage.score)}</td>
                      <td className={styles.n}>{stage.rank}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </article>
        ))}
        {retrieval?.selection && (
          <>
            <div className={`${ui.eyebrow} ${styles.subhead}`}>
              Selection diagnostics · {retrieval.selection.status}
            </div>
            <table className={styles.grid}>
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th className={styles.n}>Rank</th>
                  <th>Decision</th>
                </tr>
              </thead>
              <tbody>
                {retrieval.selection.candidates.map((candidate) => (
                  <tr key={candidate.candidateId}>
                    <td className={ui.mono}>{candidate.candidateId}</td>
                    <td className={styles.n}>{candidate.originalRank}</td>
                    <td>{candidate.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
        {!retrieval && <p className={styles.note}>No evidence to show.</p>}
      </section>

      <section className={styles.sect} id="trace" aria-label="Tool execution trace">
        <div className={styles.eyebrowRow}>
          <span className={ui.eyebrow}>Tool execution trace</span>
          <span>{run.traces.length} invocation{run.traces.length === 1 ? '' : 's'}</span>
        </div>
        {run.traces.length === 0 && (
          <p className={styles.note}>
            {run.pending_approval
              ? `Pending: ${run.pending_approval.tool_name} ${JSON.stringify(run.pending_approval.arguments)} — not executed.`
              : 'No tool invocations recorded yet.'}
          </p>
        )}
        {run.traces.map((trace, index) => (
          <dl key={`${trace.invocation_id ?? 'trace'}-${index}`} className={styles.kv}>
            <dt>tool</dt>
            <dd className={ui.mono}>{trace.tool_name}</dd>
            <dt>arguments</dt>
            <dd className={ui.mono}>{JSON.stringify(trace.arguments)}</dd>
            <dt>policy</dt>
            <dd>{trace.policy_decision ?? 'not reached'}</dd>
            <dt>approval</dt>
            <dd>{trace.approval_decision ?? 'not required'}</dd>
            <dt>status</dt>
            <dd>
              <Tag tone={trace.status === 'success' ? 'ok' : 'bad'}>{trace.status}</Tag>
            </dd>
            {trace.error && (
              <>
                <dt>error</dt>
                <dd className={ui.mono}>
                  {trace.error.error_type}: {trace.error.message}
                </dd>
              </>
            )}
          </dl>
        ))}
      </section>

      <section className={styles.sect} id="config" aria-label="Run configuration">
        <div className={styles.eyebrowRow}>
          <span className={ui.eyebrow}>Run configuration</span>
          <Tag>read-only</Tag>
        </div>
        {settings ? (
          <dl className={styles.kv}>
            <dt>model</dt>
            <dd className={ui.mono}>{run.model_id}</dd>
            <dt>limits</dt>
            <dd>
              {String(settings.max_model_iterations)} model iterations · {String(settings.max_output_tokens)} output
              tokens per call
            </dd>
            <dt>registered tools</dt>
            <dd className={ui.mono}>{system?.tools.map((tool) => tool.name).join(', ')}</dd>
            <dt>retrieval strategy</dt>
            <dd className={ui.mono}>{String(settings.retrieval_strategy)}</dd>
            <dt>embedding model</dt>
            <dd className={ui.mono}>{String(settings.embedding_model_id)}</dd>
            <dt>reranking</dt>
            <dd>{settings.reranking_enabled ? 'on' : 'off'}</dd>
            <dt>evidence selection</dt>
            <dd>{settings.evidence_selection_enabled ? 'on' : 'off'}</dd>
            <dt>tools requiring approval</dt>
            <dd className={ui.mono}>
              {Array.isArray(settings.approval_required_tools) && settings.approval_required_tools.length > 0
                ? settings.approval_required_tools.join(', ')
                : 'none'}
            </dd>
            <dt>approval timeout</dt>
            <dd>{String(settings.approval_timeout_seconds)} s</dd>
          </dl>
        ) : (
          <p className={styles.note}>Configuration unavailable.</p>
        )}
      </section>

      <section className={styles.sect} id="states" aria-label="Runtime states">
        <div className={styles.eyebrowRow}>
          <span className={ui.eyebrow}>Runtime states</span>
          <Tag tone={active ? 'warn' : 'ok'}>{active ? 'Filling in live' : 'Recorded from run events'}</Tag>
        </div>

        <div className={styles.subhead}>State-machine timeline</div>
        <ol className={styles.timeline}>
          {transitions.map((transition) => (
            <li key={transition.sequence}>
              <span className={styles.t}>{formatOffset(transition.offsetSeconds)}</span>
              <span className={ui.mono}>
                {transition.from} → {transition.to}
              </span>
            </li>
          ))}
          {transitions.length === 0 && <li className={styles.muted}>No transitions yet</li>}
        </ol>

        <div className={styles.subhead}>Step timings</div>
        <div className={styles.timing}>
          {timings.map((timing) => (
            <TimingRow key={timing.id} label={timing.label} seconds={timing.durationSeconds} running={timing.running} longest={longest} />
          ))}
          {timings.length === 0 && <span className={styles.muted}>No steps timed yet</span>}
        </div>

        <div className={styles.subhead}>Token usage</div>
        <table className={styles.grid}>
          <thead>
            <tr>
              <th>Model call</th>
              <th className={styles.n}>Input</th>
              <th className={styles.n}>Output</th>
            </tr>
          </thead>
          <tbody>
            {tokens.calls.map((call) => (
              <tr key={call.iteration}>
                <td>Model call {call.iteration}</td>
                <td className={styles.n}>{formatCount(call.input)}</td>
                <td className={styles.n}>{formatCount(call.output)}</td>
              </tr>
            ))}
            {tokens.calls.length > 0 && (
              <tr>
                <td>
                  <strong>Total</strong>
                </td>
                <td className={styles.n}>
                  <strong>{formatCount(tokens.totalInput)}</strong>
                </td>
                <td className={styles.n}>
                  <strong>{formatCount(tokens.totalOutput)}</strong>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </aside>
  )
}

function Fact({ value, label }: { value: string; label: string }) {
  return (
    <div className={styles.fact}>
      <b>{value}</b>
      <span>{label}</span>
    </div>
  )
}

function TimingRow({
  label,
  seconds,
  running,
  longest,
}: {
  label: string
  seconds: number | null
  running: boolean
  longest: number
}) {
  const width = running || seconds === null || longest === 0 ? 100 : Math.max(4, Math.round((seconds * 100) / longest))
  return (
    <>
      <span>{label}</span>
      <i className={running ? styles.barPending : styles.bar} style={{ width: `${width}%` }} />
      <span className={ui.mono}>{running ? 'running…' : formatDuration(seconds)}</span>
    </>
  )
}
