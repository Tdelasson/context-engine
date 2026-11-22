import { describe, expect, it, vi } from 'vitest'
import { EVENT_KINDS, subscribeToRunEvents } from './stream'
import type { EventSourceLike } from './stream'
import type { RunEvent } from './types'

class FakeSource implements EventSourceLike {
  readonly listeners = new Map<string, (event: MessageEvent<string>) => void>()
  closed = false
  onerror: ((event: Event) => void) | null = null

  constructor(readonly url: string) {}

  addEventListener(type: string, listener: (event: MessageEvent<string>) => void) {
    this.listeners.set(type, listener)
  }

  close() {
    this.closed = true
  }

  emit(event: RunEvent) {
    this.listeners.get(event.kind)?.({ data: JSON.stringify(event) } as MessageEvent<string>)
  }
}

const event = (sequence: number, kind: string): RunEvent => ({
  run_id: 'r1',
  sequence,
  timestamp: sequence,
  kind,
  payload: {},
})

describe('subscribeToRunEvents', () => {
  it('requests events after the given sequence and listens for every event kind', () => {
    let source!: FakeSource
    subscribeToRunEvents('r 1', 7, { onEvent: vi.fn(), onEnd: vi.fn() }, (url) => (source = new FakeSource(url)))

    expect(source.url).toBe('/api/v1/runs/r%201/events?after=7')
    expect([...source.listeners.keys()]).toEqual([...EVENT_KINDS])
  })

  it('delivers events in arrival order and ends the stream after run_finished', () => {
    let source!: FakeSource
    const onEvent = vi.fn()
    const onEnd = vi.fn()
    subscribeToRunEvents('r1', 0, { onEvent, onEnd }, (url) => (source = new FakeSource(url)))

    source.emit(event(1, 'run_started'))
    source.emit(event(2, 'model_call_started'))
    expect(onEnd).not.toHaveBeenCalled()
    source.emit(event(3, 'run_finished'))
    source.emit(event(4, 'run_started'))

    expect(onEvent.mock.calls.map(([received]) => (received as RunEvent).sequence)).toEqual([1, 2, 3])
    expect(onEnd).toHaveBeenCalledTimes(1)
    expect(source.closed).toBe(true)
  })

  it('stops following and ignores errors once unsubscribed', () => {
    let source!: FakeSource
    const onError = vi.fn()
    const stop = subscribeToRunEvents('r1', 0, { onEvent: vi.fn(), onEnd: vi.fn(), onError }, (url) => (source = new FakeSource(url)))

    source.onerror?.(new Event('error'))
    expect(onError).toHaveBeenCalledTimes(1)
    stop()
    source.onerror?.(new Event('error'))

    expect(source.closed).toBe(true)
    expect(onError).toHaveBeenCalledTimes(1)
  })
})
