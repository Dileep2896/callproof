import { useEffect, useRef, useState, type ReactNode } from 'react'
import { animate, motion, useInView, useReducedMotion } from 'framer-motion'
import { api } from '../api'
import type { Impact } from '../types'

function Reveal({ children, delay = 0, className = '' }: { children: ReactNode; delay?: number; className?: string }) {
  const reduce = useReducedMotion()
  return (
    <motion.div
      className={className}
      initial={reduce ? false : { opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  )
}

function Count({ to, suffix = '' }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true })
  const reduce = useReducedMotion()
  const [v, setV] = useState(reduce ? to : 0)
  useEffect(() => {
    if (!inView || reduce) { setV(to); return }
    const c = animate(0, to, { duration: 1.2, ease: 'easeOut', onUpdate: (x) => setV(Math.round(x)) })
    return () => c.stop()
  }, [inView, to, reduce])
  return <span ref={ref} className="tabular">{v}{suffix}</span>
}

function Section({ eyebrow, title, children }: { eyebrow: string; title: ReactNode; children?: ReactNode }) {
  return (
    <section className="border-t border-line py-20">
      <Reveal>
        <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-signal">{eyebrow}</p>
        <h2 className="mt-3 max-w-[860px] text-[38px] font-semibold leading-[1.12]">{title}</h2>
      </Reveal>
      {children}
    </section>
  )
}

const STEPS = [
  ['Transcript', 'diarized turns, timestamps, tool events'],
  ['7 rules', 'grounding, disclosures, scope, intake, verification'],
  ['Evidence', 'the exact words and the second they were said'],
  ['Regression case', 'every failed call joins the suite'],
  ['Gate', 'a candidate prompt ships only if nothing regresses'],
]

export function Story({ onOpen }: { onOpen: () => void }) {
  const [impact, setImpact] = useState<Impact | null>(null)
  useEffect(() => { api.impact().then(setImpact).catch(() => setImpact(null)) }, [])

  return (
    <main className="mx-auto max-w-[1100px] px-6">
      <section className="py-24" data-testid="story-hero">
        <Reveal>
          <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-signal">Callproof · AI voice agents for insurance agencies</p>
          <h1 className="mt-4 max-w-[900px] text-[56px] font-semibold leading-[1.04]">
            A call that sounds perfect can still quote a premium the rater never produced.
          </h1>
          <p className="mt-6 max-w-[680px] text-[18px] leading-relaxed text-dim">
            Voice agents now answer and place agency calls: quote intake, vehicle adds, mortgagee changes, Medicare lead
            qualification. Nobody listens to most of those calls. Callproof checks every one against the record it should agree with.
          </p>
        </Reveal>
      </section>

      <Section eyebrow="The problem" title={<>Three ways a good-sounding call goes wrong, and none of them show up in a transcript skim.</>}>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {[
            ['Hallucinated quote', '“$1,284 a year” when the rated quote says $1,248. Or the monthly figure read as annual.', 'crit'],
            ['Missed or late disclosure', 'No “recorded line, AI assistant” opening. A Medicare disclaimer that starts at 71 s, past the 60 s rule.', 'warn'],
            ['Incomplete intake', 'An endorsement without the lienholder address, or a VIN typed 6298 when the caller said 6289.', 'warn'],
          ].map(([t, d, tone], i) => (
            <Reveal key={t} delay={i * 0.1}>
              <div className={`h-full rounded-xl border p-5 ${tone === 'crit' ? 'border-crit/50 bg-critSoft/40' : 'border-warn/40 bg-warnSoft/40'}`}>
                <p className={`text-[17px] font-semibold ${tone === 'crit' ? 'text-crit' : 'text-warn'}`}>{t}</p>
                <p className="mt-2 text-[14.5px] leading-relaxed text-dim">{d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      <Section eyebrow="The decision" title={<>Deterministic checks against the record first. Judges second.</>}>
        <div className="mt-8 grid gap-6 md:grid-cols-2">
          <Reveal>
            <p className="text-[16px] leading-relaxed text-dim">
              A spoken dollar figure either matches the rater's output or it doesn't. A disclaimer either started by 60 s or it didn't.
              Those checks don't need a model, so they can't wave a bad call through, and they run on every call.
            </p>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="rounded-xl border border-line bg-panel p-5 text-[14px]">
              <p className="font-semibold">Considered instead: detecting runbook drift when a carrier portal adds a field.</p>
              <p className="mt-2 text-dim">Valuable, but an honest version needs real portal screens. The call audit can be built faithfully on transcripts plus the record, and it is reused on every account.</p>
            </div>
          </Reveal>
        </div>
      </Section>

      <Section eyebrow="How it works" title="From transcript to a gate that blocks bad prompts.">
        <div className="mt-12 flex flex-col gap-3 md:flex-row md:items-stretch">
          {STEPS.map(([t, d], i) => (
            <Reveal key={t} delay={i * 0.12} className="flex flex-1 items-center gap-3">
              <div className="h-full flex-1 rounded-xl border border-line bg-panel p-4">
                <p className="font-mono text-[11px] text-signal">0{i + 1}</p>
                <p className="mt-1 text-[16px] font-semibold">{t}</p>
                <p className="mt-1 text-[13px] leading-snug text-dim">{d}</p>
              </div>
              {i < STEPS.length - 1 && <span className="hidden text-dim md:block">→</span>}
            </Reveal>
          ))}
        </div>
      </Section>

      <Section eyebrow="Measured on the bundled seed week" title="What changes when every call is checked.">
        {impact ? (
          <div className="mt-10 space-y-8" data-testid="impact">
            <div className="grid gap-4 md:grid-cols-4">
              {[
                [impact.failing_calls, ` / ${impact.calls}`, 'calls failed on the production prompt'],
                [impact.critical, '', 'critical findings'],
                [impact.spoken_figures_checked, '', 'spoken dollar figures checked'],
                [impact.mined_cases, '', 'regression cases mined automatically'],
              ].map(([n, s, l]) => (
                <Reveal key={String(l)}>
                  <div className="rounded-xl border border-line bg-panel p-5">
                    <p className="font-mono text-[40px] font-semibold text-text"><Count to={Number(n)} suffix={String(s)} /></p>
                    <p className="mt-1 text-[13px] text-dim">{l}</p>
                  </div>
                </Reveal>
              ))}
            </div>
            <Reveal>
              <div className="overflow-hidden rounded-xl border border-line">
                {impact.rows.map((r) => (
                  <div key={r.label} className="grid grid-cols-[1.4fr_1fr_1fr] items-center border-b border-line/70 bg-panel px-5 py-3 text-[14px] last:border-b-0">
                    <span>{r.label}</span>
                    <span className="font-mono text-dim line-through decoration-crit/60">{r.before}</span>
                    <span className="font-mono text-signal">{r.after}</span>
                  </div>
                ))}
              </div>
            </Reveal>
            <p className="text-[12px] text-dim">All numbers come from one fictitious agency's seeded calls bundled with the repo, not from production traffic.</p>
          </div>
        ) : (
          <p className="mt-8 text-dim">Loading measured numbers…</p>
        )}
        <Reveal>
          <button onClick={onOpen} className="mt-12 rounded-lg bg-signal px-5 py-3 text-[15px] font-semibold text-night hover:brightness-110">
            Open the call console →
          </button>
        </Reveal>
      </Section>
    </main>
  )
}
