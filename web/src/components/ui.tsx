import type { ReactNode } from 'react'
import type { Severity } from '../types'

export function Panel({ title, right, children, className = '' }: { title?: ReactNode; right?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-xl border border-line bg-panel ${className}`}>
      {title && (
        <header className="flex items-center justify-between border-b border-line px-4 py-2.5">
          <h2 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-dim">{title}</h2>
          {right}
        </header>
      )}
      {children}
    </section>
  )
}

export function SevBadge({ severity }: { severity: Severity }) {
  const cls = severity === 'critical' ? 'bg-critSoft text-crit' : 'bg-warnSoft text-warn'
  return <span className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase ${cls}`}>{severity}</span>
}

export function StatusDot({ passed }: { passed: boolean }) {
  return <span aria-hidden className={`inline-block h-2 w-2 shrink-0 rounded-full ${passed ? 'bg-signal' : 'bg-crit'}`} />
}

export function ScoreRing({ score, size = 54 }: { score: number; size?: number }) {
  const r = size / 2 - 5
  const c = 2 * Math.PI * r
  const color = score === 100 ? '#3DD6B5' : score >= 60 ? '#F2B53D' : '#FF5D5D'
  return (
    <svg width={size} height={size} role="img" aria-label={`score ${score}`}>
      <circle cx={size / 2} cy={size / 2} r={r} stroke="#2A3441" strokeWidth={5} fill="none" />
      <circle
        cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={5} fill="none" strokeLinecap="round"
        strokeDasharray={`${(c * score) / 100} ${c}`} transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text x="50%" y="54%" textAnchor="middle" dominantBaseline="middle" fill="#E6EAF0" fontSize={size * 0.3} fontWeight={600}>
        {score}
      </text>
    </svg>
  )
}
