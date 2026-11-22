import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { ApprovalDecision, RunDetail, RunSummary } from '../api/types'
import ui from '../styles/ui.module.css'
import { ApprovalCard } from './ApprovalCard'
import styles from './RunThread.module.css'
import { StatusTag, Tag } from './Tag'

interface RunCardProps {
  run: RunSummary
  index: number
  selected: boolean
  /** The loaded detail of the selected run, used for the approval countdown. */
  detail: RunDetail | null
  approvalTimeoutSeconds: number | null
  onChanged: () => void
}

function requestedAt(detail: RunDetail | null): number | null {
  const event = detail?.events.findLast((item) => item.kind === 'tool_approval_requested')
  return event ? event.timestamp : null
}

export function RunCard({ run, index, selected, detail, approvalTimeoutSeconds, onChanged }: RunCardProps) {
  const failed = run.status === 'failed' || run.status === 'limit_reached'
  const active = run.status === 'running' || run.status === 'awaiting_approval'

  const decide = async (decision: ApprovalDecision, reason: string) => {
    await api.decideApproval(run.run_id, decision, reason)
    onChanged()
  }

  return (
    <section className={`${styles.run} ${selected ? styles.selected : ''}`} aria-label={`Run ${index + 1}`}>
      <div className={styles.who}>
        <span className={ui.eyebrow}>You</span>
        <span className={ui.eyebrow}>Run {index + 1}</span>
      </div>
      <p className={styles.prompt}>{run.prompt}</p>
      <div className={styles.agent}>[ ] Context Engine</div>

      {run.status === 'running' && (
        <p className={styles.waiting}>Waiting for the model…</p>
      )}

      {run.status === 'awaiting_approval' && run.pending_approval && (
        <ApprovalCard
          pending={run.pending_approval}
          requestedAt={requestedAt(detail)}
          timeoutSeconds={approvalTimeoutSeconds}
          onDecide={decide}
        />
      )}

      {failed && (
        <div className={styles.failure}>
          <strong>
            {run.status === 'limit_reached'
              ? 'Iteration limit reached.'
              : `Run failed in ${run.error_phase ?? 'the runtime'}.`}
          </strong>
          {run.error_message && <div className={ui.mono}>{run.error_message}</div>}
        </div>
      )}

      {run.final_response &&
        (failed ? (
          <p className={styles.answer}>
            Model text after the failure (not shown as a successful answer): “{run.final_response}”
          </p>
        ) : (
          <p className={styles.answer}>{run.final_response}</p>
        ))}

      <div className={styles.runbar}>
        <StatusTag status={run.status} />
        {run.model_iterations > 0 && (
          <span>
            {run.model_iterations} of {run.max_model_iterations} model iterations
          </span>
        )}
        {active && <Tag tone="warn">live</Tag>}
        <span className={styles.spacer} />
        {selected ? <strong>Technical view open</strong> : <Link to={`/runs/${run.run_id}`}>Technical view →</Link>}
      </div>
    </section>
  )
}
