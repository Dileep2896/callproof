import type { Audit, Call, CallRow, GateResult, Health, Impact, RuleInfo, Snapshot } from './types'

let snapshot: Promise<Snapshot> | null = null
let offline = false

export function isOffline() {
  return offline
}

export function resetApiCache() {
  snapshot = null
  offline = false
}

function loadSnapshot(): Promise<Snapshot> {
  snapshot ??= fetch('/snapshot.json').then((r) => {
    if (!r.ok) throw new Error('snapshot missing')
    return r.json() as Promise<Snapshot>
  })
  return snapshot
}

async function get<T>(path: string, fromSnap: (s: Snapshot) => T | undefined): Promise<T> {
  if (!offline) {
    try {
      const r = await fetch(path)
      if (r.ok && (r.headers.get('content-type') ?? '').includes('json')) return (await r.json()) as T
      if (r.status === 404 && (r.headers.get('content-type') ?? '').includes('json')) throw new Error('not found')
    } catch (e) {
      if ((e as Error).message === 'not found') throw e
    }
    offline = true
  }
  const v = fromSnap(await loadSnapshot())
  if (v === undefined) throw new Error('not found')
  return v
}

export const api = {
  health: () => get<Health>('/api/health', (s) => s.health),
  rules: () => get<RuleInfo[]>('/api/rules', (s) => s.rules),
  calls: (version: string) => get<CallRow[]>(`/api/calls?version=${encodeURIComponent(version)}`, (s) => s.lists[version]),
  call: (id: string) => get<{ call: Call; audit: Audit }>(`/api/calls/${encodeURIComponent(id)}`, (s) => s.calls[id]),
  gate: (baseline: string, candidate: string) =>
    get<GateResult>(
      `/api/gate?baseline=${encodeURIComponent(baseline)}&candidate=${encodeURIComponent(candidate)}`,
      (s) => s.gates[`${baseline}..${candidate}`],
    ),
  impact: () => get<Impact>('/api/impact', (s) => s.impact),
}
