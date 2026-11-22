import { useEffect } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { isActive } from '../api/types'
import type { RunDetail } from '../api/types'
import { Composer } from '../components/Composer'
import { Inspector } from '../components/Inspector'
import { RunCard } from '../components/RunCard'
import styles from '../components/RunThread.module.css'
import { Tag } from '../components/Tag'
import { useAppData } from '../state/AppData'
import { useRunDetail } from '../state/useRunDetail'

/** `/runs` shows the thread; `/runs/:runId` also opens the technical view of that run. */
export function RunsPage() {
  const { runId } = useParams()
  if (runId) return <SelectedRun key={runId} runId={runId} />
  return <RunsLayout selectedId={null} detail={null} detailError={null} />
}

function SelectedRun({ runId }: { runId: string }) {
  const { refresh } = useAppData()
  const { run, error } = useRunDetail(runId)
  const status = run?.status

  // Keep the shared run list (sidebar and thread cards) current as the run changes state.
  useEffect(() => {
    if (status) void refresh()
  }, [status, refresh])

  return <RunsLayout selectedId={runId} detail={run} detailError={error} />
}

interface RunsLayoutProps {
  selectedId: string | null
  detail: RunDetail | null
  detailError: string | null
}

function RunsLayout({ selectedId, detail, detailError }: RunsLayoutProps) {
  const { runs, system, error, refresh } = useAppData()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const locked = runs.some((run) => isActive(run.status))
  const timeout = system?.settings.approval_timeout_seconds
  const approvalTimeoutSeconds = typeof timeout === 'number' ? timeout : null
  const modelId = typeof system?.settings.model_id === 'string' ? system.settings.model_id : null
  const strategy = system?.settings.retrieval_strategy

  return (
    <div className={`${styles.page} ${selectedId ? styles.pageWithInspector : ''}`}>
      <main className={styles.main}>
        <div className={styles.topbar}>
          <div>
            Runs / <strong>This session</strong>
          </div>
          <div>
            {modelId && <Tag>{modelId}</Tag>} {typeof strategy === 'string' && <Tag>{strategy} retrieval</Tag>}
          </div>
        </div>
        <div className={styles.scroll}>
          <div className={styles.notice}>
            <strong>Each prompt is a fresh run.</strong> One run is active at a time. Runs are kept by the
            server for this process only.
          </div>
          {error && (
            <div role="alert" className={styles.failure}>
              Could not reach the API: {error}
            </div>
          )}
          {runs.map((run, index) => (
            <RunCard
              key={run.run_id}
              run={run}
              index={index}
              selected={run.run_id === selectedId}
              detail={run.run_id === selectedId ? detail : null}
              approvalTimeoutSeconds={approvalTimeoutSeconds}
              onChanged={() => void refresh()}
            />
          ))}
          {runs.length === 0 && !error && <p>No runs yet. Ask something below.</p>}
        </div>
        <Composer
          presets={(system?.prompt_presets ?? []).map(({ name, prompt }) => ({ name, prompt }))}
          locked={locked}
          modelId={modelId}
          onStarted={(run) => {
            void refresh()
            navigate(`/runs/${run.run_id}`)
          }}
        />
      </main>
      {selectedId && detailError && <aside role="alert">Could not load run: {detailError}</aside>}
      {selectedId && !detailError && !detail && <aside aria-busy="true">Loading run…</aside>}
      {selectedId && detail && <Inspector run={detail} system={system} section={params.get('section')} />}
    </div>
  )
}
