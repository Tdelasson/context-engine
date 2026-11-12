import { useCallback, useEffect, useState } from 'react'
import { ApiError, api } from '../api/client'
import { isRecord } from '../api/json'
import type { IngestionOutcome, SourceListing } from '../api/types'

export interface UploadResult {
  name: string
  /** Outcome the server reported, or `rejected` when it refused the file. */
  state: 'created' | 'replaced' | 'unchanged' | 'rejected'
  /** The server's message for a rejection. */
  message: string | null
}

export interface SourcesState {
  listing: SourceListing | null
  /** Per-file results of the latest upload batch. */
  results: UploadResult[]
  recoveryOutcomes: IngestionOutcome[]
  /** The server reported that a failed index write needs recovery. */
  recoveryNeeded: boolean
  busy: boolean
  error: string | null
  upload: (files: readonly File[]) => Promise<void>
  remove: (sourceId: string) => Promise<void>
  clear: () => Promise<void>
  recover: () => Promise<void>
}

const OUTCOME_STATES = new Set(['created', 'replaced', 'unchanged'])

function needsRecovery(failure: unknown): boolean {
  return failure instanceof ApiError && isRecord(failure.details) && failure.details.requires_recovery === true
}

function describe(failure: unknown): string {
  return failure instanceof Error ? failure.message : String(failure)
}

/** Loads the indexed sources and runs the upload, delete, clear and recover actions. */
export function useSources(): SourcesState {
  const [listing, setListing] = useState<SourceListing | null>(null)
  const [results, setResults] = useState<UploadResult[]>([])
  const [recoveryOutcomes, setRecoveryOutcomes] = useState<IngestionOutcome[]>([])
  const [recoveryNeeded, setRecoveryNeeded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    api
      .listSources()
      .then((next) => {
        if (!cancelled) setListing(next)
      })
      .catch((failure: unknown) => {
        if (!cancelled) setError(describe(failure))
      })
    return () => {
      cancelled = true
    }
  }, [])

  const reload = useCallback(async () => {
    setListing(await api.listSources())
  }, [])

  /** Runs one action, then refreshes the list. Failures are shown, never swallowed. */
  const act = useCallback(
    async (action: () => Promise<void>) => {
      setBusy(true)
      setError(null)
      try {
        await action()
      } catch (failure) {
        if (needsRecovery(failure)) setRecoveryNeeded(true)
        setError(describe(failure))
      }
      try {
        await reload()
      } catch (failure) {
        setError(describe(failure))
      } finally {
        setBusy(false)
      }
    },
    [reload],
  )

  const upload = useCallback(
    (files: readonly File[]) =>
      act(async () => {
        // One request per file so each file gets its own outcome or rejection message.
        const next: UploadResult[] = []
        setResults(next)
        for (const file of files) {
          try {
            const report = await api.uploadSources([file])
            const status = report.outcomes[0]?.status ?? ''
            next.push({
              name: file.name,
              state: OUTCOME_STATES.has(status) ? (status as UploadResult['state']) : 'created',
              message: null,
            })
          } catch (failure) {
            if (needsRecovery(failure)) setRecoveryNeeded(true)
            next.push({ name: file.name, state: 'rejected', message: describe(failure) })
          }
          setResults([...next])
        }
      }),
    [act],
  )

  const remove = useCallback(
    (sourceId: string) =>
      act(async () => {
        await api.deleteSource(sourceId)
        setResults([])
      }),
    [act],
  )

  const clear = useCallback(
    () =>
      act(async () => {
        await api.clearUploads()
        setResults([])
      }),
    [act],
  )

  const recover = useCallback(
    () =>
      act(async () => {
        const report = await api.recoverSources()
        setRecoveryOutcomes(report.outcomes)
        setRecoveryNeeded(report.outcomes.some((outcome) => outcome.requires_recovery && !outcome.recovered))
      }),
    [act],
  )

  return { listing, results, recoveryOutcomes, recoveryNeeded, busy, error, upload, remove, clear, recover }
}
