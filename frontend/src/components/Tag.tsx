import type { ReactNode } from 'react'
import type { RunStatus } from '../api/types'
import ui from '../styles/ui.module.css'

export type Tone = 'neutral' | 'ok' | 'warn' | 'bad' | 'planned'

export function Tag({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  const toneClass = tone === 'neutral' ? '' : (ui[tone] ?? '')
  return <span className={`${ui.tag} ${toneClass}`.trim()}>{children}</span>
}

const STATUS_LABELS: Record<RunStatus, string> = {
  running: 'Running',
  awaiting_approval: 'Awaiting approval',
  success: 'Success',
  failed: 'Failed',
  limit_reached: 'Limit reached',
}

const STATUS_TONES: Record<RunStatus, Tone> = {
  running: 'warn',
  awaiting_approval: 'warn',
  success: 'ok',
  failed: 'bad',
  limit_reached: 'warn',
}

/** The status tag renders exactly what the API reports; success is never inferred. */
export function StatusTag({ status }: { status: RunStatus }) {
  return <Tag tone={STATUS_TONES[status]}>{STATUS_LABELS[status]}</Tag>
}
