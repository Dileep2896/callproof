export type Workflow = 'quote_bundle' | 'vehicle_add' | 'mortgagee_change' | 'medicare_fronter'
export type Severity = 'critical' | 'high'

export interface Turn {
  speaker: 'agent' | 'caller' | 'tool'
  t: number
  text: string
  tool?: string | null
  args?: Record<string, unknown>
}

export interface Amount { label: string; value: number; period: string | null }

export interface Call {
  id: string
  scenario: string
  version: string
  workflow: Workflow
  line: 'pc' | 'medicare'
  title: string
  caller: string
  duration: number
  turns: Turn[]
  intake: Record<string, unknown>
  record: { source: string; carriers: string[]; prior_carrier?: string | null; amounts: Amount[] }
}

export interface Finding {
  rule: string
  severity: Severity
  message: string
  turn: number | null
  start: number
  end: number
  t: number | null
}

export interface Audit {
  call_id: string
  scenario: string
  version: string
  workflow: Workflow
  passed: boolean
  score: number
  findings: Finding[]
}

export interface CallRow {
  id: string
  scenario: string
  version: string
  workflow: Workflow
  title: string
  caller: string
  duration: number
  passed: boolean
  score: number
  rules: string[]
}

export interface GateRow {
  case_id: string
  workflow: Workflow
  kind: 'regression' | 'guard'
  status: 'ok' | 'fixed' | 'regressed' | 'still_failing'
  baseline_rules: string[]
  candidate_rules: string[]
  new_critical: string[]
}

export interface GateResult {
  baseline: string
  candidate: string
  verdict: 'PASS' | 'BLOCK'
  reasons: string[]
  counts: Record<string, number>
  rows: GateRow[]
}

export interface Health {
  ok: boolean
  agency: string
  versions: string[]
  baseline: string
  notes: Record<string, string>
}

export interface RuleInfo { id: string; severity: Severity; check: string }

export interface Impact {
  calls: number
  failing_calls: number
  findings: number
  critical: number
  high: number
  by_rule: Record<string, number>
  spoken_figures_checked: number
  grounding_findings: number
  mined_cases: number
  guard_cases: number
  gate: Record<string, { verdict: string } & Record<string, number | string>>
  rows: { label: string; before: string; after: string }[]
}

export interface Snapshot {
  health: Health
  rules: RuleInfo[]
  lists: Record<string, CallRow[]>
  calls: Record<string, { call: Call; audit: Audit }>
  suite: unknown[]
  gates: Record<string, GateResult>
  impact: Impact
}
