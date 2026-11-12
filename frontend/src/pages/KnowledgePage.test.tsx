import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api } from '../api/client'
import type { IngestionOutcome, Source, SourceDiagnostic } from '../api/types'
import { makeSystem } from '../test/fixtures'
import { AppDataProvider } from '../state/AppData'
import { KnowledgePage } from './KnowledgePage'

function source(name: string, kind: 'preloaded' | 'uploaded', chunks: number, diagnostics: SourceDiagnostic[] = []): Source {
  return {
    source_id: `${kind}-${name}`,
    source_name: name,
    source_kind: kind,
    content_sha256: 'a'.repeat(64),
    chunk_count: chunks,
    diagnostics,
  }
}

const WARNING: SourceDiagnostic = {
  code: 'partial_extraction',
  message: 'Partial extraction: pages 4 and 9 have no text layer. No OCR is performed.',
  location: null,
}

function outcome(overrides: Partial<IngestionOutcome> = {}): IngestionOutcome {
  return {
    source_id: 'uploaded-x',
    status: 'created',
    chunk_count: 1,
    previous_chunk_count: 0,
    diagnostics: [],
    error_phase: null,
    error_message: null,
    requires_recovery: false,
    recovered: false,
    ...overrides,
  }
}

/** A stateful fake of the source endpoints. */
class FakeSources {
  preloaded = [source('architecture.md', 'preloaded', 34), source('demo-guide.txt', 'preloaded', 1)]
  uploaded: Source[] = [source('field-notes.md', 'uploaded', 6), source('quarterly-report.pdf', 'uploaded', 41, [WARNING])]

  install() {
    vi.spyOn(api, 'listRuns').mockResolvedValue([])
    vi.spyOn(api, 'getSystem').mockResolvedValue(
      makeSystem({
        collection_name: 'context-engine-workbench-m5-v1',
        max_uploads: 5,
        max_upload_bytes: 256 * 1024,
        max_pdf_upload_bytes: 10 * 1024 * 1024,
        max_pdf_pages: 100,
        max_pdf_text_characters: 1_048_576,
        chunk_max_input_tokens: 128,
        chunk_overlap_tokens: 16,
      }),
    )
    vi.spyOn(api, 'listSources').mockImplementation(async () => ({
      preloaded: [...this.preloaded],
      uploaded: [...this.uploaded],
    }))
  }
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/knowledge']}>
      <AppDataProvider>
        <KnowledgePage />
      </AppDataProvider>
    </MemoryRouter>,
  )
}

const file = (name: string) => new File(['content'], name, { type: 'text/plain' })
let backend: FakeSources

beforeEach(() => {
  backend = new FakeSources()
  backend.install()
})
afterEach(() => vi.restoreAllMocks())

describe('KnowledgePage rows', () => {
  it('lists preloaded and uploaded sources with type, chunk count and status', async () => {
    renderPage()

    const preloaded = await screen.findByRole('region', { name: 'Preloaded sources' })
    expect(within(preloaded).getByText('architecture.md')).toBeInTheDocument()
    expect(preloaded).toHaveTextContent('2 sources · 35 chunks')
    expect(within(preloaded).getAllByText('Ready')).toHaveLength(2)
    expect(within(preloaded).queryByRole('button', { name: /Delete/ })).not.toBeInTheDocument()
    expect(preloaded).toHaveTextContent('never removed by delete or clear')

    const uploaded = screen.getByRole('region', { name: 'Uploaded documents' })
    await waitFor(() => expect(uploaded).toHaveTextContent('2 of 5 slots used'))
    const success = within(uploaded).getByText('field-notes.md').closest('tr')!
    expect(success).toHaveTextContent('Markdown')
    expect(success).toHaveTextContent('6')
    expect(within(success).getByText('Ingested')).toBeInTheDocument()
  })

  it('shows extraction warnings with the server message and a warning status', async () => {
    renderPage()

    const row = (await screen.findByText('quarterly-report.pdf')).closest('tr')!
    expect(row).toHaveTextContent('PDF')
    expect(within(row).getByText('Ingested with warning')).toBeInTheDocument()
    expect(within(row).getByText(WARNING.message)).toBeInTheDocument()
  })

  it('shows read-only limits and index configuration from the system description', async () => {
    renderPage()

    const limits = await screen.findByRole('region', { name: 'Upload limits' })
    await waitFor(() => expect(limits).toHaveTextContent('5 files'))
    expect(limits).toHaveTextContent('256 KiB per file, UTF-8')
    expect(limits).toHaveTextContent('10 MiB, 100 pages, 1,048,576 extracted characters')
    const index = screen.getByRole('region', { name: 'Index' })
    expect(index).toHaveTextContent('context-engine-workbench-m5-v1')
    expect(index).toHaveTextContent('128 tokens, up to 16 overlap')
    expect(screen.getByRole('region', { name: 'Per-source permissions' })).toHaveTextContent('Planned')
  })

  it('reports a failure to load the sources', async () => {
    vi.spyOn(api, 'listSources').mockRejectedValue(new Error('Failed to fetch'))

    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('Failed to fetch')
  })
})

describe('KnowledgePage upload', () => {
  it('uploads each chosen file, refreshes the list and notes a replaced revision', async () => {
    const upload = vi.spyOn(api, 'uploadSources').mockImplementation(async ([chosen]) => {
      const name = chosen!.name
      const existing = backend.uploaded.some((item) => item.source_name === name)
      backend.uploaded = [...backend.uploaded.filter((item) => item.source_name !== name), source(name, 'uploaded', 3)]
      return {
        source_ids: [`uploaded-${name}`],
        source_names: [name],
        chunk_count: 3,
        outcomes: [outcome({ source_id: `uploaded-${name}`, status: existing ? 'replaced' : 'created' })],
      }
    })
    renderPage()
    await screen.findByText('field-notes.md')

    await userEvent.upload(screen.getByTestId('file-input'), [file('field-notes.md'), file('new-doc.txt')])

    await waitFor(() => expect(upload).toHaveBeenCalledTimes(2))
    expect(upload.mock.calls.map(([files]) => files.map((item) => item.name))).toEqual([['field-notes.md'], ['new-doc.txt']])
    const replaced = (await screen.findByText('new-doc.txt')).closest('tr')!
    expect(within(replaced).getByText('Text')).toBeInTheDocument()
    expect(screen.getByText('Replaced an earlier revision with the same name')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Uploaded documents' })).toHaveTextContent('3 of 5 slots used')
  })

  it('shows a rejected upload with the server message and leaves the list unchanged', async () => {
    vi.spyOn(api, 'uploadSources').mockRejectedValue(
      new ApiError(422, 'source_rejected', 'Only UTF-8 .txt/.md files and text-based .pdf files are supported.', {
        requires_recovery: false,
      }),
    )
    renderPage()
    await screen.findByText('field-notes.md')

    await userEvent.upload(screen.getByTestId('file-input'), file('scanned-contract.pdf'))

    const row = (await screen.findByText('scanned-contract.pdf')).closest('tr')!
    expect(within(row).getByText('Rejected')).toBeInTheDocument()
    expect(within(row).getByText(/Only UTF-8 .txt\/.md files/)).toBeInTheDocument()
    expect(within(row).getByText('—')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Uploaded documents' })).toHaveTextContent('2 of 5 slots used')
    expect(screen.queryByText('Recovery needed')).not.toBeInTheDocument()
  })
})

describe('KnowledgePage delete, clear and recover', () => {
  it('asks for confirmation before deleting one upload', async () => {
    const remove = vi.spyOn(api, 'deleteSource').mockImplementation(async (id) => {
      backend.uploaded = backend.uploaded.filter((item) => item.source_id !== id)
      return { outcome: outcome({ status: 'deleted' }) }
    })
    renderPage()
    await screen.findByText('field-notes.md')

    await userEvent.click(screen.getByRole('button', { name: 'Delete field-notes.md' }))
    expect(screen.getByText(/Delete field-notes.md\?/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(remove).not.toHaveBeenCalled()

    await userEvent.click(screen.getByRole('button', { name: 'Delete field-notes.md' }))
    await userEvent.click(screen.getByRole('button', { name: 'Confirm delete' }))

    expect(remove).toHaveBeenCalledWith('uploaded-field-notes.md')
    await waitFor(() => expect(screen.queryByText('field-notes.md')).not.toBeInTheDocument())
    expect(screen.getByText('quarterly-report.pdf')).toBeInTheDocument()
  })

  it('asks for confirmation before clearing every upload and keeps preloaded sources', async () => {
    const clear = vi.spyOn(api, 'clearUploads').mockImplementation(async () => {
      const ids = backend.uploaded.map((item) => item.source_id)
      backend.uploaded = []
      return { deleted_source_ids: ids }
    })
    renderPage()
    await screen.findByText('field-notes.md')

    await userEvent.click(screen.getByRole('button', { name: 'Clear uploads' }))
    expect(clear).not.toHaveBeenCalled()
    expect(screen.getByText(/Delete all 2 uploads\?/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Confirm clear' }))

    await waitFor(() => expect(clear).toHaveBeenCalledTimes(1))
    expect(await screen.findByText('No uploaded documents.')).toBeInTheDocument()
    expect(screen.getByText('architecture.md')).toBeInTheDocument()
  })

  it('shows a recovery-needed state from the server signal and clears it after recovery', async () => {
    vi.spyOn(api, 'uploadSources').mockRejectedValue(
      new ApiError(422, 'source_rejected', 'store: write failed. Restart/recover the index before searching or retrying.', {
        requires_recovery: true,
      }),
    )
    const recover = vi.spyOn(api, 'recoverSources').mockResolvedValue({
      outcomes: [outcome({ source_id: 'uploaded-broken-source-id', status: 'created', requires_recovery: true, recovered: true })],
    })
    renderPage()
    await screen.findByText('field-notes.md')

    await userEvent.upload(screen.getByTestId('file-input'), file('big.md'))

    expect((await screen.findAllByText('Recovery needed')).length).toBeGreaterThan(0)
    expect(screen.getByText(/Restart\/recover the index/)).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Recover source index' }))

    expect(recover).toHaveBeenCalledTimes(1)
    await waitFor(() => expect(screen.queryByText('Recovery needed')).not.toBeInTheDocument())
    expect(screen.getByRole('list', { name: 'Recovery outcomes' })).toHaveTextContent('recovered')
  })

  it('keeps the recovery-needed state when recovery does not complete', async () => {
    vi.spyOn(api, 'recoverSources').mockResolvedValue({
      outcomes: [outcome({ status: 'failed', requires_recovery: true, recovered: false, error_message: 'store unavailable' })],
    })
    vi.spyOn(api, 'deleteSource').mockRejectedValue(
      new ApiError(500, 'source_operation_failed', 'store: delete failed', { requires_recovery: true }),
    )
    renderPage()
    await screen.findByText('field-notes.md')
    await userEvent.click(screen.getByRole('button', { name: 'Delete field-notes.md' }))
    await userEvent.click(screen.getByRole('button', { name: 'Confirm delete' }))
    expect((await screen.findAllByText('Recovery needed')).length).toBeGreaterThan(0)

    await userEvent.click(screen.getByRole('button', { name: 'Recover source index' }))

    expect(await screen.findByText(/store unavailable/)).toBeInTheDocument()
    expect(screen.getAllByText('Recovery needed').length).toBeGreaterThan(0)
  })
})
