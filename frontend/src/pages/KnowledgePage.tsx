import { useRef, useState } from 'react'
import type { DragEvent } from 'react'
import type { Source } from '../api/types'
import { Tag } from '../components/Tag'
import { useAppData } from '../state/AppData'
import { useSources } from '../state/useSources'
import type { UploadResult } from '../state/useSources'
import ui from '../styles/ui.module.css'
import styles from './KnowledgePage.module.css'

const TYPE_LABELS: Record<string, string> = { md: 'Markdown', txt: 'Text', pdf: 'PDF' }

function typeLabel(name: string): string {
  const extension = name.split('.').at(-1)?.toLowerCase() ?? ''
  return TYPE_LABELS[extension] ?? extension.toUpperCase()
}

function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${+(bytes / (1024 * 1024)).toFixed(1)} MiB`
  return `${+(bytes / 1024).toFixed(1)} KiB`
}

function setting(settings: Record<string, unknown> | undefined, key: string): number | null {
  const value = settings?.[key]
  return typeof value === 'number' ? value : null
}

export function KnowledgePage() {
  const { system } = useAppData()
  const sources = useSources()
  const { listing } = sources
  const settings = system?.settings
  const preloaded = listing?.preloaded ?? []
  const uploaded = listing?.uploaded ?? []
  const maxUploads = setting(settings, 'max_uploads')
  const rejected = sources.results.filter((result) => result.state === 'rejected')
  const [confirmingClear, setConfirmingClear] = useState(false)

  return (
    <main className={styles.main}>
      <div className={styles.topbar}>
        <strong>Knowledge</strong>
        <div>
          {sources.recoveryNeeded ? <Tag tone="bad">Recovery needed</Tag> : listing && <Tag tone="ok">Index ready</Tag>}{' '}
          {typeof settings?.collection_name === 'string' && <Tag>{settings.collection_name}</Tag>}
        </div>
      </div>

      <div className={styles.scroll}>
        <h1 className={styles.title}>Knowledge sources</h1>
        <p className={styles.sub}>The documents the agent can search, and how each one was indexed.</p>

        {sources.error && (
          <div role="alert" className={styles.failure}>
            {sources.error}
          </div>
        )}

        <div className={styles.columns}>
          <div>
            <section className={styles.panel} aria-label="Preloaded sources">
              <div className={styles.panelHead}>
                <span className={ui.eyebrow}>Project documents · preloaded</span>
                <span>
                  {preloaded.length} sources · {preloaded.reduce((sum, source) => sum + source.chunk_count, 0)} chunks
                </span>
              </div>
              <SourceTable>
                {preloaded.map((source) => (
                  <SourceRow key={source.source_id} source={source} readyLabel="Ready" />
                ))}
              </SourceTable>
              <p className={styles.rowmsg}>
                Preloaded sources are indexed on startup and are never removed by delete or clear.
              </p>
            </section>

            <section className={styles.panel} aria-label="Uploaded documents">
              <div className={styles.panelHead}>
                <span className={ui.eyebrow}>Uploaded documents</span>
                <span>
                  {maxUploads !== null ? `${uploaded.length} of ${maxUploads} slots used` : `${uploaded.length} uploaded`}{' '}
                  {uploaded.length > 0 &&
                    (confirmingClear ? (
                      <span className={styles.confirm}>
                        Delete all {uploaded.length} uploads?{' '}
                        <button
                          type="button"
                          className={`${ui.btn} ${ui.quiet} ${ui.danger}`}
                          disabled={sources.busy}
                          onClick={() => {
                            setConfirmingClear(false)
                            void sources.clear()
                          }}
                        >
                          Confirm clear
                        </button>
                        <button type="button" className={`${ui.btn} ${ui.quiet}`} onClick={() => setConfirmingClear(false)}>
                          Cancel
                        </button>
                      </span>
                    ) : (
                      <button
                        type="button"
                        className={`${ui.btn} ${ui.quiet} ${ui.danger}`}
                        disabled={sources.busy}
                        onClick={() => setConfirmingClear(true)}
                      >
                        Clear uploads
                      </button>
                    ))}
                </span>
              </div>
              <SourceTable>
                {uploaded.map((source) => (
                  <SourceRow
                    key={source.source_id}
                    source={source}
                    readyLabel="Ingested"
                    result={sources.results.find((item) => item.name === source.source_name)}
                    disabled={sources.busy}
                    onDelete={() => sources.remove(source.source_id)}
                  />
                ))}
                {rejected.map((result) => (
                  <RejectedRow key={`rejected-${result.name}`} result={result} />
                ))}
                {uploaded.length === 0 && rejected.length === 0 && (
                  <tr>
                    <td colSpan={5} className={styles.empty}>
                      No uploaded documents.
                    </td>
                  </tr>
                )}
              </SourceTable>
              <DropZone busy={sources.busy} onFiles={(files) => void sources.upload(files)} />
            </section>
          </div>

          <div>
            <section className={styles.panel} aria-label="Upload limits">
              <div className={styles.panelHead}>
                <span className={ui.eyebrow}>Upload limits</span>
                <Tag>enforced by the server</Tag>
              </div>
              <dl className={styles.kv}>
                <dt>Uploads</dt>
                <dd>{maxUploads ?? '—'} files</dd>
                <dt>Text / Markdown</dt>
                <dd>{limit(settings, 'max_upload_bytes')} per file, UTF-8</dd>
                <dt>PDF</dt>
                <dd>
                  {limit(settings, 'max_pdf_upload_bytes')}, {setting(settings, 'max_pdf_pages') ?? '—'} pages,{' '}
                  {setting(settings, 'max_pdf_text_characters')?.toLocaleString('en-US') ?? '—'} extracted characters
                </dd>
                <dt>Same name</dt>
                <dd>Replaces the earlier revision</dd>
              </dl>
            </section>

            <section className={styles.panel} aria-label="Index">
              <div className={styles.panelHead}>
                <span className={ui.eyebrow}>Index</span>
                <Tag>read-only</Tag>
              </div>
              <dl className={styles.kv}>
                <dt>Collection</dt>
                <dd className={ui.mono}>{String(settings?.collection_name ?? '—')}</dd>
                <dt>Embedding model</dt>
                <dd className={ui.mono}>{String(settings?.embedding_model_id ?? '—')}</dd>
                <dt>Chunking</dt>
                <dd>
                  {setting(settings, 'chunk_max_input_tokens') ?? '—'} tokens, up to{' '}
                  {setting(settings, 'chunk_overlap_tokens') ?? '—'} overlap
                </dd>
                <dt>Strategy</dt>
                <dd>{String(settings?.retrieval_strategy ?? '—')}</dd>
                <dt>State</dt>
                <dd>
                  {sources.recoveryNeeded ? <Tag tone="bad">recovery needed</Tag> : <Tag tone="ok">ready</Tag>}
                </dd>
              </dl>
              <p className={styles.rowmsg}>
                A failed index write blocks search until it is recovered. Startup recovers interrupted writes;
                recovery can also be run here.
              </p>
              <button
                type="button"
                className={ui.btn}
                disabled={sources.busy}
                onClick={() => void sources.recover()}
              >
                Recover source index
              </button>
              {sources.recoveryOutcomes.length > 0 && (
                <ul className={styles.outcomes} aria-label="Recovery outcomes">
                  {sources.recoveryOutcomes.map((outcome) => (
                    <li key={outcome.source_id}>
                      <span className={ui.mono}>{outcome.source_id.slice(0, 16)}</span> {outcome.status}
                      {outcome.recovered ? ' · recovered' : ''}
                      {outcome.error_message ? ` · ${outcome.error_message}` : ''}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className={styles.panel} aria-label="Per-source permissions">
              <div className={styles.panelHead}>
                <span className={ui.eyebrow}>Per-source permissions</span>
                <Tag tone="planned">Planned</Tag>
              </div>
              <p className={styles.rowmsg}>
                Choosing which sources a run may retrieve from is part of the longer-term design. Today every run
                searches all indexed sources.
              </p>
            </section>
          </div>
        </div>
      </div>
    </main>
  )
}

function limit(settings: Record<string, unknown> | undefined, key: string): string {
  const value = setting(settings, key)
  return value === null ? '—' : formatBytes(value)
}

function SourceTable({ children }: { children: React.ReactNode }) {
  return (
    <table className={styles.grid}>
      <thead>
        <tr>
          <th>Source</th>
          <th>Type</th>
          <th className={styles.n}>Chunks</th>
          <th>Status</th>
          <th />
        </tr>
      </thead>
      <tbody>{children}</tbody>
    </table>
  )
}

interface SourceRowProps {
  source: Source
  readyLabel: string
  result?: UploadResult
  disabled?: boolean
  onDelete?: () => Promise<void>
}

const RESULT_NOTES: Record<string, string> = {
  replaced: 'Replaced an earlier revision with the same name',
  unchanged: 'Unchanged: identical content was already indexed',
}

function SourceRow({ source, readyLabel, result, disabled, onDelete }: SourceRowProps) {
  const [confirming, setConfirming] = useState(false)
  const warned = source.diagnostics.length > 0
  const note = result ? RESULT_NOTES[result.state] : undefined

  return (
    <tr>
      <td>
        {source.source_name}
        {note && <span className={styles.rowmsg}>{note}</span>}
        {source.diagnostics.map((diagnostic, index) => (
          <span key={`${diagnostic.code}-${index}`} className={`${styles.rowmsg} ${styles.warn}`}>
            {diagnostic.message}
          </span>
        ))}
      </td>
      <td>{typeLabel(source.source_name)}</td>
      <td className={styles.n}>{source.chunk_count}</td>
      <td>{warned ? <Tag tone="warn">{readyLabel} with warning</Tag> : <Tag tone="ok">{readyLabel}</Tag>}</td>
      <td>
        {onDelete &&
          (confirming ? (
            <span className={styles.confirm}>
              Delete {source.source_name}?{' '}
              <button
                type="button"
                className={`${ui.btn} ${ui.quiet} ${ui.danger}`}
                disabled={disabled}
                onClick={() => {
                  setConfirming(false)
                  void onDelete()
                }}
              >
                Confirm delete
              </button>
              <button type="button" className={`${ui.btn} ${ui.quiet}`} onClick={() => setConfirming(false)}>
                Cancel
              </button>
            </span>
          ) : (
            <button
              type="button"
              className={`${ui.btn} ${ui.quiet}`}
              disabled={disabled}
              aria-label={`Delete ${source.source_name}`}
              onClick={() => setConfirming(true)}
            >
              Delete
            </button>
          ))}
      </td>
    </tr>
  )
}

function RejectedRow({ result }: { result: UploadResult }) {
  return (
    <tr>
      <td>
        {result.name}
        <span className={`${styles.rowmsg} ${styles.bad}`}>{result.message}</span>
      </td>
      <td>{typeLabel(result.name)}</td>
      <td className={styles.n}>—</td>
      <td>
        <Tag tone="bad">Rejected</Tag>
      </td>
      <td />
    </tr>
  )
}

function DropZone({ busy, onFiles }: { busy: boolean; onFiles: (files: File[]) => void }) {
  const input = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)

  const drop = (event: DragEvent) => {
    event.preventDefault()
    setOver(false)
    if (!busy && event.dataTransfer.files.length > 0) onFiles([...event.dataTransfer.files])
  }

  return (
    <div
      className={`${styles.dropzone} ${over ? styles.over : ''}`}
      onDragOver={(event) => {
        event.preventDefault()
        setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={drop}
    >
      Drop .txt, .md or .pdf files here, or{' '}
      <button type="button" className={`${ui.btn} ${ui.quiet}`} disabled={busy} onClick={() => input.current?.click()}>
        choose files
      </button>
      <input
        ref={input}
        type="file"
        multiple
        hidden
        accept=".txt,.md,.pdf"
        aria-label="Choose files"
        data-testid="file-input"
        onChange={(event) => {
          const files = [...(event.target.files ?? [])]
          event.target.value = ''
          if (files.length > 0) onFiles(files)
        }}
      />
    </div>
  )
}
