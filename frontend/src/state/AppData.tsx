import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../api/client'
import type { RunSummary, SystemInfo } from '../api/types'

interface AppDataValue {
  runs: RunSummary[]
  system: SystemInfo | null
  error: string | null
  refresh: () => Promise<void>
}

const AppDataContext = createContext<AppDataValue | null>(null)

/** Holds the run list and the read-only system description shared by the shell and pages. */
export function AppDataProvider({ children }: { children: ReactNode }) {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [system, setSystem] = useState<SystemInfo | null>(null)
  const [error, setError] = useState<string | null>(null)

  const apply = useCallback(([nextRuns, nextSystem]: [RunSummary[], SystemInfo]) => {
    setRuns(nextRuns)
    setSystem(nextSystem)
    setError(null)
  }, [])
  const fail = useCallback((reason: unknown) => {
    setError(reason instanceof Error ? reason.message : String(reason))
  }, [])

  const refresh = useCallback(async () => {
    try {
      apply(await Promise.all([api.listRuns(), api.getSystem()]))
    } catch (reason) {
      fail(reason)
    }
  }, [apply, fail])

  useEffect(() => {
    let cancelled = false
    Promise.all([api.listRuns(), api.getSystem()])
      .then((data) => {
        if (!cancelled) apply(data)
      })
      .catch((reason: unknown) => {
        if (!cancelled) fail(reason)
      })
    return () => {
      cancelled = true
    }
  }, [apply, fail])

  const value = useMemo(() => ({ runs, system, error, refresh }), [runs, system, error, refresh])
  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>
}

export function useAppData(): AppDataValue {
  const value = useContext(AppDataContext)
  if (!value) throw new Error('useAppData must be used inside AppDataProvider.')
  return value
}
