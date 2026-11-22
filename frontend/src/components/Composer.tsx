import { useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../api/client'
import type { RunSummary } from '../api/types'
import ui from '../styles/ui.module.css'
import styles from './RunThread.module.css'

interface ComposerProps {
  presets: readonly { name: string; prompt: string }[]
  /** A run is active: only one run may be active at a time. */
  locked: boolean
  modelId: string | null
  onStarted: (run: RunSummary) => void
}

export function Composer({ presets, locked, modelId, onStarted }: ComposerProps) {
  const [prompt, setPrompt] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (locked || busy || !prompt.trim()) return
    setBusy(true)
    setError(null)
    try {
      const run = await api.startRun(prompt)
      setPrompt('')
      onStarted(run)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className={styles.composer} onSubmit={(event) => void submit(event)}>
      <textarea
        className={styles.field}
        aria-label="Prompt"
        rows={2}
        value={prompt}
        disabled={locked}
        placeholder={
          locked
            ? 'A run is in progress. You can ask again when it finishes.'
            : 'Ask about the indexed documents, or give the calculator something to compute…'
        }
        onChange={(event) => setPrompt(event.target.value)}
      />
      <div className={styles.row}>
        <select
          className={styles.select}
          aria-label="Preset"
          disabled={locked}
          value=""
          onChange={(event) => {
            const preset = presets.find((item) => item.name === event.target.value)
            if (preset) setPrompt(preset.prompt)
          }}
        >
          <option value="">Preset…</option>
          {presets.map((preset) => (
            <option key={preset.name} value={preset.name}>
              {preset.name}
            </option>
          ))}
        </select>
        <span className={styles.readonly}>Sources: all indexed</span>
        {modelId && <span className={styles.readonly}>Model: {modelId}</span>}
        <span className={styles.spacer} />
        <button type="submit" className={`${ui.btn} ${ui.primary}`} disabled={locked || busy || !prompt.trim()}>
          Run agent ↑
        </button>
      </div>
      {error && <p role="alert" className={styles.error}>{error}</p>}
    </form>
  )
}
