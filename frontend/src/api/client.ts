import { isRecord, asString } from './json'
import type {
  ApprovalDecision,
  ClearUploadsReport,
  DeleteSourceReport,
  IngestionReport,
  RecoveryReport,
  RunDetail,
  RunSummary,
  SourceListing,
  SystemInfo,
} from './types'

const BASE = '/api/v1'

/** A non-2xx API response, carrying the structured error the server reported. */
export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: unknown

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  // A string body is JSON; a FormData body sets its own multipart boundary.
  if (typeof init.body === 'string') headers['Content-Type'] = 'application/json'
  const response = await fetch(`${BASE}${path}`, { ...init, headers })
  if (!response.ok) throw await toApiError(response)
  return (await response.json()) as T
}

async function toApiError(response: Response): Promise<ApiError> {
  let code = 'http_error'
  let message = response.statusText || `Request failed with status ${response.status}`
  let details: unknown
  try {
    const body: unknown = await response.json()
    const error = isRecord(body) ? body.error : null
    if (isRecord(error)) {
      code = asString(error.code) ?? code
      message = asString(error.message) ?? message
      details = error.details
    }
  } catch {
    // The body was not JSON; keep the status text.
  }
  return new ApiError(response.status, code, message, details)
}

const runPath = (runId: string) => `/runs/${encodeURIComponent(runId)}`

export const api = {
  async listRuns(): Promise<RunSummary[]> {
    return (await request<{ runs: RunSummary[] }>('/runs')).runs
  },
  getRun(runId: string): Promise<RunDetail> {
    return request<RunDetail>(runPath(runId))
  },
  startRun(prompt: string): Promise<RunSummary> {
    return request<RunSummary>('/runs', { method: 'POST', body: JSON.stringify({ prompt }) })
  },
  decideApproval(runId: string, decision: ApprovalDecision, reason?: string): Promise<RunSummary> {
    const body = { decision, reason: reason?.trim() ? reason.trim() : null }
    return request<RunSummary>(`${runPath(runId)}/approval`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  getSystem(): Promise<SystemInfo> {
    return request<SystemInfo>('/system')
  },
  listSources(): Promise<SourceListing> {
    return request<SourceListing>('/sources')
  },
  uploadSources(files: readonly File[]): Promise<IngestionReport> {
    const body = new FormData()
    for (const file of files) body.append('files', file, file.name)
    return request<IngestionReport>('/sources', { method: 'POST', body })
  },
  deleteSource(sourceId: string): Promise<DeleteSourceReport> {
    return request<DeleteSourceReport>(`/sources/${encodeURIComponent(sourceId)}`, { method: 'DELETE' })
  },
  clearUploads(): Promise<ClearUploadsReport> {
    return request<ClearUploadsReport>('/sources', { method: 'DELETE' })
  },
  recoverSources(): Promise<RecoveryReport> {
    return request<RecoveryReport>('/sources/recover', { method: 'POST' })
  },
}
