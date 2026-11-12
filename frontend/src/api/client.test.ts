import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api } from './client'

function respond(status: number, body: unknown) {
  return vi.fn().mockImplementation(
    async () => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }),
  )
}

afterEach(() => vi.unstubAllGlobals())

describe('api client', () => {
  it('posts the prompt to start a run', async () => {
    const fetchMock = respond(202, { run_id: 'r1' })
    vi.stubGlobal('fetch', fetchMock)

    await api.startRun('hello')

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/runs')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({ prompt: 'hello' })
  })

  it('sends an explicit approval decision with an optional trimmed reason', async () => {
    const fetchMock = respond(200, { run_id: 'r1' })
    vi.stubGlobal('fetch', fetchMock)

    await api.decideApproval('r 1', 'rejected', '  too risky ')
    await api.decideApproval('r1', 'approved', '   ')

    const first = fetchMock.mock.calls[0] as [string, RequestInit]
    const second = fetchMock.mock.calls[1] as [string, RequestInit]
    expect(first[0]).toBe('/api/v1/runs/r%201/approval')
    expect(JSON.parse(first[1].body as string)).toEqual({ decision: 'rejected', reason: 'too risky' })
    expect(JSON.parse(second[1].body as string)).toEqual({ decision: 'approved', reason: null })
  })

  it('turns the structured error envelope into an ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      respond(409, { error: { code: 'run_already_active', message: 'busy', details: { active_run_id: 'r0' } } }),
    )

    const failure = await api.startRun('x').catch((reason: unknown) => reason)

    expect(failure).toBeInstanceOf(ApiError)
    expect(failure).toMatchObject({
      status: 409,
      code: 'run_already_active',
      message: 'busy',
      details: { active_run_id: 'r0' },
    })
  })

  it('falls back to the status text when the error body is not JSON', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 502, statusText: 'Bad Gateway' })))

    await expect(api.getSystem()).rejects.toMatchObject({ status: 502, code: 'http_error', message: 'Bad Gateway' })
  })

  it('unwraps the run list', async () => {
    vi.stubGlobal('fetch', respond(200, { runs: [{ run_id: 'a' }] }))

    expect(await api.listRuns()).toEqual([{ run_id: 'a' }])
  })
})
