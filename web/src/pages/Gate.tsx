import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { api, isOffline } from '../api'
import { Panel } from '../components/ui'
import { RULE_LABEL, WORKFLOW_LABEL } from '../format'
import type { GateResult, GateRow, Health } from '../types'

const STATUS: Record<GateRow['status'], { label: string; cls: string }> = {
  regressed: { label: 'regressed', cls: 'bg-critSoft text-crit' },
  still_failing: { label: 'still failing', cls: 'bg-warnSoft text-warn' },
  fixed: { label: 'fixed', cls: 'bg-signalSoft text-signal' },
  ok: { label: 'ok', cls: 'bg-raised text-dim' },
}
const ORDER: GateRow['status'][] = ['regressed', 'still_failing', 'fixed', 'ok']

export function Gate() {
  const [health, setHealth] = useState<Health | null>(null)
  const [candidate, setCandidate] = useState(() => new URLSearchParams(window.location.search).get('candidate') ?? 'v15')
  const [res, setRes] = useState<GateResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => { api.health().then(setHealth).catch((e) => setError(String(e))) }, [])
  const baseline = health?.baseline ?? 'v14'
  useEffect(() => {
    setRes(null)
    api.gate(baseline, candidate).then(setRes).catch((e) => setError(String(e)))
  }, [baseline, candidate])

  if (error) return <p className="p-8 text-crit">Could not load gate: {error}</p>
  const candidates = (health?.versions ?? []).filter((v) => v !== baseline)
  const rows = res ? [...res.rows].sort((a, b) => ORDER.indexOf(a.status) - ORDER.indexOf(b.status)) : []

  return (
    <main className="mx-auto max-w-[1180px] px-6 py-6">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[12px] uppercase tracking-[0.1em] text-dim">Regression gate · CI for calls</p>
          <h1 className="mt-1 text-[26px] font-semibold">Replay the suite on a candidate prompt before it ships</h1>
          <p className="mt-1 max-w-[720px] text-[14px] text-dim">
            Every call that failed on <span className="font-mono text-text">{baseline}</span> became a regression case; every passing call is a guard.
            A candidate is blocked if any guard breaks or a new critical finding appears.
          </p>
          {isOffline() && <p className="mt-1 text-[12px] text-warn">read-only snapshot (API offline)</p>}
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-line bg-panel p-1" role="tablist" aria-label="candidate">
          {candidates.map((v) => (
            <button key={v} role="tab" aria-selected={v === candidate} onClick={() => setCandidate(v)}
              className={`rounded-md px-3 py-1.5 font-mono text-[12px] ${v === candidate ? 'bg-raised text-text' : 'text-dim hover:text-text'}`}>
              {baseline} → {v}
            </button>
          ))}
        </div>
      </div>

      {res && (
        <>
          <motion.div
            key={res.candidate}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`mb-5 flex flex-wrap items-center gap-6 rounded-xl border p-5 ${res.verdict === 'BLOCK' ? 'border-crit/60 bg-critSoft/50' : 'border-signal/50 bg-signalSoft/60'}`}
            data-testid="verdict"
          >
            <div className={`font-mono text-[34px] font-bold ${res.verdict === 'BLOCK' ? 'text-crit' : 'text-signal'}`}>{res.verdict}</div>
            <div className="flex flex-1 flex-wrap gap-6 text-[13px]">
              {(['fixed', 'regressed', 'still_failing', 'ok'] as const).map((k) => (
                <div key={k}>
                  <p className="font-mono text-[24px] font-semibold tabular">{res.counts[k]}</p>
                  <p className="text-dim">{STATUS[k].label}</p>
                </div>
              ))}
              <div>
                <p className="font-mono text-[24px] font-semibold tabular">{res.counts.candidate_passing}/{res.counts.cases}</p>
                <p className="text-dim">cases passing on {res.candidate}</p>
              </div>
            </div>
            {res.reasons.length > 0 && (
              <ul className="w-full space-y-1 border-t border-crit/30 pt-3 text-[13px] text-crit">
                {res.reasons.map((r) => <li key={r}>✕ {r}</li>)}
              </ul>
            )}
          </motion.div>

          <Panel title={`${res.counts.cases} cases`} right={<span className="font-mono text-[11px] text-dim">callproof gate --baseline {res.baseline} --candidate {res.candidate}</span>}>
            <table className="w-full text-[13px]">
              <thead className="text-left text-[11px] uppercase tracking-[0.08em] text-dim">
                <tr className="border-b border-line">
                  <th className="px-4 py-2 font-semibold">Case</th>
                  <th className="px-2 py-2 font-semibold">Workflow</th>
                  <th className="px-2 py-2 font-semibold">Kind</th>
                  <th className="px-2 py-2 font-semibold">On {res.baseline}</th>
                  <th className="px-2 py-2 font-semibold">On {res.candidate}</th>
                  <th className="px-4 py-2 text-right font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.case_id}
                    className={`border-b border-line/60 ${r.status === 'regressed' ? 'bg-critSoft/30' : ''}`} data-testid={`case-${r.case_id}`}>
                    <td className="px-4 py-1.5 font-mono">{r.case_id}</td>
                    <td className="px-2 py-1.5">{WORKFLOW_LABEL[r.workflow]}</td>
                    <td className="px-2 py-1.5 text-dim">{r.kind}</td>
                    <td className="px-2 py-1.5 text-dim">{r.baseline_rules.map((x) => RULE_LABEL[x] ?? x).join(', ') || 'pass'}</td>
                    <td className={`px-2 py-1.5 ${r.candidate_rules.length ? 'text-crit' : 'text-dim'}`}>{r.candidate_rules.map((x) => RULE_LABEL[x] ?? x).join(', ') || 'pass'}</td>
                    <td className="px-4 py-1.5 text-right"><span className={`rounded px-2 py-0.5 font-mono text-[11px] ${STATUS[r.status].cls}`}>{STATUS[r.status].label}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </>
      )}
    </main>
  )
}
