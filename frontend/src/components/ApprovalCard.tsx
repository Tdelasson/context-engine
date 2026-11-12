import { useEffect, useState } from 'react'
import type { ApprovalDecision, PendingApproval } from '../api/types'
import ui from '../styles/ui.module.css'
import styles from './RunThread.module.css'

interface ApprovalCardProps {
  pending: PendingApproval
  /** Wall-clock seconds of the approval request event, when the run's events are loaded. */
  requestedAt: number | null
  timeoutSeconds: number | null
  onDecide: (decision: ApprovalDecision, reason: string) => Promise<void>
}

function formatRemaining(seconds: number): string {
  const whole = Math.max(0, Math.ceil(seconds))
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, '0')}`
}

export function ApprovalCard({ pending, requestedAt, timeoutSeconds, onDecide }: ApprovalCardProps) {
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [now, setNow] = useState(() => Date.now() / 1000)

  useEffect(() => {
    if (requestedAt === null || timeoutSeconds === null) return
    const timer = setInterval(() => setNow(Date.now() / 1000), 1000)
    return () => clearInterval(timer)
  }, [requestedAt, timeoutSeconds])

  const decide = async (decision: ApprovalDecision) => {
    setBusy(true)
    setError(null)
    try {
      await onDecide(decision, reason)
    } catch (reasonForFailure) {
      setError(reasonForFailure instanceof Error ? reasonForFailure.message : String(reasonForFailure))
    } finally {
      setBusy(false)
    }
  }

  let timeoutText: string | null = null
  if (timeoutSeconds !== null) {
    timeoutText =
      requestedAt === null
        ? `Rejected automatically if unanswered after ${timeoutSeconds} s.`
        : `Rejected automatically if unanswered: ${formatRemaining(requestedAt + timeoutSeconds - now)} left of the ${formatRemaining(timeoutSeconds)} timeout.`
  }

  return (
    <section className={styles.approval} aria-label="Approval needed">
      <h3>Approval needed before this tool runs</h3>
      <p>
        The model proposed a tool that your configuration marks as requiring approval. Nothing has
        run yet.
      </p>
      <div className={styles.args}>
        <div className={ui.mono}>
          <strong>{pending.tool_name}</strong>
        </div>
        <div className={ui.mono}>{JSON.stringify(pending.arguments)}</div>
      </div>
      <div className={styles.actions}>
        <button type="button" className={`${ui.btn} ${ui.primary}`} disabled={busy} onClick={() => void decide('approved')}>
          Approve
        </button>
        <button type="button" className={`${ui.btn} ${ui.danger}`} disabled={busy} onClick={() => void decide('rejected')}>
          Reject
        </button>
        <input
          className={styles.reason}
          aria-label="Reason (optional)"
          placeholder="Reason (optional)"
          value={reason}
          maxLength={1000}
          onChange={(event) => setReason(event.target.value)}
        />
      </div>
      {error && <p role="alert" className={styles.error}>{error}</p>}
      {timeoutText && <p className={styles.timeout}>{timeoutText}</p>}
    </section>
  )
}
