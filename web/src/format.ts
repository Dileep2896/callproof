import type { Workflow } from './types'

export const WORKFLOW_LABEL: Record<Workflow, string> = {
  quote_bundle: 'Quote',
  vehicle_add: 'Vehicle add',
  mortgagee_change: 'Mortgagee',
  medicare_fronter: 'Medicare',
}

export const RULE_LABEL: Record<string, string> = {
  ai_disclosure: 'AI + recording disclosure',
  tpmo_disclaimer: 'Medicare disclaimer by 60 s',
  scope_guard: 'Scope guard',
  grounding: 'Grounded in the record',
  intake_complete: 'Intake complete',
  intake_faithful: 'Intake matches caller',
  verify_before_change: 'Verify before write',
}

export function clock(seconds: number): string {
  const s = Math.max(0, Math.round(seconds))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

export function money(v: number): string {
  return `$${v.toLocaleString('en-US', { maximumFractionDigits: 2 })}`
}

export interface Piece { text: string; mark: null | 'critical' | 'high' }

/** Split a turn's text into plain and highlighted pieces from [start, end) finding spans. */
export function splitSpans(text: string, spans: { start: number; end: number; severity: 'critical' | 'high' }[]): Piece[] {
  const valid = spans
    .filter((s) => s.end > s.start && s.start >= 0 && s.end <= text.length)
    .sort((a, b) => a.start - b.start)
  const out: Piece[] = []
  let at = 0
  for (const s of valid) {
    if (s.start < at) continue
    if (s.start > at) out.push({ text: text.slice(at, s.start), mark: null })
    out.push({ text: text.slice(s.start, s.end), mark: s.severity })
    at = s.end
  }
  if (at < text.length) out.push({ text: text.slice(at), mark: null })
  return out
}
