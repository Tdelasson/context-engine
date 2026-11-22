export function formatDuration(seconds: number | null): string {
  if (seconds === null) return '—'
  if (seconds < 1) return `${Math.round(seconds * 1000)} ms`
  return `${seconds.toFixed(2)} s`
}

export function formatOffset(seconds: number): string {
  return `+${seconds.toFixed(2)} s`
}

export function formatCount(value: number | null): string {
  return value === null ? '—' : value.toLocaleString('en-US')
}

export function formatScore(value: number): string {
  return value.toFixed(4)
}
