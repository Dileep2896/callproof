import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { api, isOffline } from '../api'
import { Panel, ScoreRing, SevBadge, StatusDot } from '../components/ui'
import { Timeline } from '../components/Timeline'
import { RULE_LABEL, WORKFLOW_LABEL, clock, money, splitSpans } from '../format'
import type { Audit, Call, CallRow, Health } from '../types'

function initialParam(name: string): string | null {
  return new URLSearchParams(window.location.search).get(name)
}

export function Console() {
  const [health, setHealth] = useState<Health | null>(null)
  const [version, setVersion] = useState(() => initialParam('version') ?? 'v14')
  const [rows, setRows] = useState<CallRow[]>([])
  const [selected, setSelected] = useState<string | null>(initialParam('call'))
  const [detail, setDetail] = useState<{ call: Call; audit: Audit } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => { api.health().then(setHealth).catch((e) => setError(String(e))) }, [])
  useEffect(() => {
    api.calls(version).then((r) => {
      setRows(r)
      setSelected((cur) => {
        if (cur && r.some((x) => x.id === cur)) return cur
        const scen = cur?.split('-')[0]
        const same = r.find((x) => x.scenario === scen)
        return same?.id ?? r.find((x) => !x.passed)?.id ?? r[0]?.id ?? null
      })
    }).catch((e) => setError(String(e)))
  }, [version])
  useEffect(() => {
    if (selected) api.call(selected).then(setDetail).catch((e) => setError(String(e)))
  }, [selected])

  const failing = rows.filter((r) => !r.passed).length
  const groups = useMemo(() => {
    const g = new Map<string, CallRow[]>()
    for (const r of rows) g.set(r.workflow, [...(g.get(r.workflow) ?? []), r])
    return [...g.entries()]
  }, [rows])

  if (error) return <p className="p-8 text-crit">Could not load data: {error}</p>

  return (
    <main className="mx-auto max-w-[1440px] px-6 py-5">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[12px] uppercase tracking-[0.1em] text-dim">{health?.agency ?? 'Agency'} · voice agent calls</p>
          <h1 className="mt-1 text-[26px] font-semibold leading-tight">
            <span className="tabular">{failing}</span> of <span className="tabular">{rows.length}</span> calls failed the audit
          </h1>
          {isOffline() && <p className="mt-1 text-[12px] text-warn">read-only snapshot (API offline)</p>}
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-line bg-panel p-1" role="tablist" aria-label="prompt version">
          {(health?.versions ?? ['v14']).map((v) => (
            <button
              key={v}
              role="tab"
              aria-selected={v === version}
              onClick={() => setVersion(v)}
              className={`rounded-md px-3 py-1.5 font-mono text-[12px] ${v === version ? 'bg-raised text-text' : 'text-dim hover:text-text'}`}
            >
              {v}{v === health?.baseline ? ' · prod' : ''}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-[290px_minmax(0,1fr)_350px] gap-4">
        <Panel title="Calls" right={<span className="font-mono text-[11px] text-dim">{version}</span>}>
          <div className="max-h-[calc(100vh-190px)] overflow-y-auto py-1">
            {groups.map(([wf, list]) => (
              <div key={wf} className="py-1">
                <p className="px-4 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-dim">{WORKFLOW_LABEL[wf as CallRow['workflow']]}</p>
                {list.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => setSelected(r.id)}
                    data-testid={`row-${r.scenario}`}
                    className={`flex w-full items-center gap-2.5 px-4 py-1.5 text-left text-[13px] ${r.id === selected ? 'bg-raised' : 'hover:bg-raised/60'}`}
                  >
                    <StatusDot passed={r.passed} />
                    <span className="w-8 font-mono text-[11px] text-dim">{r.scenario}</span>
                    <span className="min-w-0 flex-1 truncate">{r.caller}</span>
                    {!r.passed && <span className="font-mono text-[11px] text-crit">{r.rules.length}</span>}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </Panel>

        {detail ? <CallView key={detail.call.id} call={detail.call} audit={detail.audit} /> : <Panel><p className="p-6 text-dim">Loading…</p></Panel>}

        {detail ? <Findings call={detail.call} audit={detail.audit} /> : <div />}
      </div>
    </main>
  )
}

function CallView({ call, audit }: { call: Call; audit: Audit }) {
  const byTurn = new Map<number, Audit['findings']>()
  for (const f of audit.findings) if (f.turn !== null) byTurn.set(f.turn, [...(byTurn.get(f.turn) ?? []), f])
  return (
    <Panel className="min-w-0">
      <div className="flex items-center gap-4 border-b border-line px-4 py-3">
        <ScoreRing score={audit.score} />
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[11px] text-dim">{call.id} · {WORKFLOW_LABEL[call.workflow]} · {clock(call.duration)}</p>
          <h2 className="truncate text-[18px] font-semibold">{call.title}</h2>
          <p className="text-[13px] text-dim">Caller: {call.caller}</p>
        </div>
        <span className={`rounded-md px-2.5 py-1 font-mono text-[12px] font-semibold ${audit.passed ? 'bg-signalSoft text-signal' : 'bg-critSoft text-crit'}`}>
          {audit.passed ? 'PASS' : `FAIL · ${audit.findings.length}`}
        </span>
      </div>
      <Timeline call={call} findings={audit.findings} />
      <ol className="max-h-[calc(100vh-345px)] space-y-2 overflow-y-auto px-4 pb-4" data-testid="transcript">
        {call.turns.map((turn, i) => {
          const fs = byTurn.get(i) ?? []
          if (turn.speaker === 'tool') {
            return (
              <li key={i} className={`flex items-center gap-2 font-mono text-[11px] ${fs.length ? 'text-crit' : 'text-dim'}`}>
                <span className="w-10 text-right">{clock(turn.t)}</span>
                <span className="rounded border border-line px-1.5 py-0.5">tool</span>
                {turn.tool}
                {fs.length > 0 && <span>· {fs[0].message}</span>}
              </li>
            )
          }
          const pieces = splitSpans(turn.text, fs.map((f) => ({ start: f.start, end: f.end, severity: f.severity })))
          const flagged = fs.length > 0
          return (
            <motion.li
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(i * 0.025, 0.4), duration: 0.25 }}
              className="flex gap-3"
            >
              <span className="w-10 shrink-0 pt-1 text-right font-mono text-[11px] text-dim">{clock(turn.t)}</span>
              <div className={`min-w-0 flex-1 rounded-lg border px-3 py-2 text-[14px] leading-relaxed ${flagged ? 'border-crit/60 bg-critSoft/40' : 'border-line bg-raised/50'}`}>
                <p className={`mb-0.5 text-[11px] font-semibold uppercase tracking-[0.08em] ${turn.speaker === 'agent' ? 'text-signal' : 'text-caller'}`}>
                  {turn.speaker === 'agent' ? 'Voice agent' : 'Caller'}
                </p>
                <p>
                  {pieces.map((p, k) =>
                    p.mark ? (
                      <mark key={k} className={`rounded px-0.5 ${p.mark === 'critical' ? 'bg-crit/25 text-crit' : 'bg-warn/25 text-warn'} underline decoration-2 underline-offset-2`}>{p.text}</mark>
                    ) : (
                      <span key={k}>{p.text}</span>
                    ),
                  )}
                </p>
                {fs.map((f, k) => (
                  <p key={k} className={`mt-1.5 text-[12px] ${f.severity === 'critical' ? 'text-crit' : 'text-warn'}`}>↳ {f.message}</p>
                ))}
              </div>
            </motion.li>
          )
        })}
      </ol>
    </Panel>
  )
}

function Findings({ call, audit }: { call: Call; audit: Audit }) {
  return (
    <div className="flex min-w-0 flex-col gap-4">
      <Panel title="Findings" right={<span className="font-mono text-[11px] text-dim">7 rules</span>}>
        <div className="space-y-2 p-3" data-testid="findings">
          {audit.findings.length === 0 && (
            <p className="rounded-lg bg-signalSoft px-3 py-2 text-[13px] text-signal">All 7 rules pass. This call becomes a guard case in the suite.</p>
          )}
          {audit.findings.map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + i * 0.08 }}
              className="rounded-lg border border-line bg-raised/60 p-3"
            >
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="text-[13px] font-semibold">{RULE_LABEL[f.rule] ?? f.rule}</span>
                <SevBadge severity={f.severity} />
              </div>
              <p className="text-[12.5px] leading-snug text-dim">{f.message}</p>
              {f.t !== null && <p className="mt-1 font-mono text-[11px] text-dim">at {clock(f.t)}</p>}
            </motion.div>
          ))}
          {!audit.passed && (
            <p className="px-1 pt-1 text-[12px] text-dim">Mined as regression case <span className="font-mono text-text">{call.scenario}</span>: every future prompt must pass it.</p>
          )}
        </div>
      </Panel>
      <Panel title={`Record · ${call.record.source}`}>
        <dl className="divide-y divide-line text-[12.5px]">
          {call.record.amounts.map((a) => (
            <div key={a.label} className="flex justify-between gap-3 px-4 py-1.5">
              <dt className="text-dim">{a.label}</dt>
              <dd className="font-mono">{money(a.value)}{a.period ? <span className="text-dim"> /{a.period === 'six_months' ? '6mo' : a.period === 'month' ? 'mo' : 'yr'}</span> : ''}</dd>
            </div>
          ))}
          {call.record.carriers.length > 0 && (
            <div className="flex justify-between gap-3 px-4 py-1.5"><dt className="text-dim">carriers quoted</dt><dd className="text-right">{call.record.carriers.join(', ')}</dd></div>
          )}
          {call.record.amounts.length === 0 && call.record.carriers.length === 0 && <p className="px-4 py-2 text-dim">No figures: the agent must not quote any.</p>}
        </dl>
      </Panel>
      <Panel title="Structured intake">
        <dl className="divide-y divide-line text-[12.5px]">
          {Object.entries(call.intake).map(([k, v]) => {
            const empty = v === '' || v === null || v === undefined
            return (
              <div key={k} className="flex justify-between gap-3 px-4 py-1.5">
                <dt className="text-dim">{k}</dt>
                <dd className={`truncate text-right font-mono ${empty ? 'text-crit' : ''}`}>{empty ? 'missing' : String(v)}</dd>
              </div>
            )
          })}
        </dl>
      </Panel>
    </div>
  )
}
