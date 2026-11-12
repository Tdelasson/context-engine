import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import { subscribeToRunEvents } from '../api/stream'
import { isActive } from '../api/types'
import type { RunDetail, RunEvent } from '../api/types'

/** Events whose arrival changes fields that live outside the event list (status, pending approval, results). */
const REFRESH_KINDS = new Set(['tool_approval_requested', 'tool_approval_resolved', 'run_finished'])

function mergeEvents(current: readonly RunEvent[], incoming: readonly RunEvent[]): RunEvent[] {
  const bySequence = new Map<number, RunEvent>()
  for (const event of [...current, ...incoming]) bySequence.set(event.sequence, event)
  return [...bySequence.values()].sort((a, b) => a.sequence - b.sequence)
}

export function lastSequence(events: readonly RunEvent[]): number {
  return events.reduce((latest, event) => Math.max(latest, event.sequence), 0)
}

export interface RunDetailState {
  run: RunDetail | null
  error: string | null
  reload: () => void
}

/**
 * Load one run and follow its events while it is active. Reloading the page restores the
 * run from the API; the stream replays events recorded since the loaded snapshot.
 */
export function useRunDetail(runId: string): RunDetailState {
  const [run, setRun] = useState<RunDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reloadCount, setReloadCount] = useState(0)

  useEffect(() => {
    let cancelled = false
    let unsubscribe: (() => void) | undefined

    const load = async (): Promise<RunDetail | null> => {
      const detail = await api.getRun(runId)
      if (cancelled) return null
      setError(null)
      setRun((previous) => ({
        ...detail,
        events: mergeEvents(previous?.events ?? [], detail.events),
      }))
      return detail
    }

    load()
      .then((detail) => {
        if (!detail || !isActive(detail.status)) return
        unsubscribe = subscribeToRunEvents(runId, lastSequence(detail.events), {
          onEvent: (event) => {
            setRun((previous) =>
              previous ? { ...previous, events: mergeEvents(previous.events, [event]) } : previous,
            )
            if (REFRESH_KINDS.has(event.kind)) void load().catch(() => undefined)
          },
          onEnd: () => void load().catch(() => undefined),
        })
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : String(reason))
      })

    return () => {
      cancelled = true
      unsubscribe?.()
    }
  }, [runId, reloadCount])

  const reload = useCallback(() => setReloadCount((count) => count + 1), [])
  return { run, error, reload }
}
