import type { Call, Finding } from '../types'
import { clock } from '../format'

/** A strip of the call: turns by speaker, the disclosure deadlines, and where each finding sits. */
export function Timeline({ call, findings }: { call: Call; findings: Finding[] }) {
  const W = 1000
  const dur = Math.max(call.duration, 1)
  const x = (t: number) => (t / dur) * W
  const deadlines = [{ t: 15, label: '15 s disclosure' }, ...(call.line === 'medicare' ? [{ t: 60, label: '60 s disclaimer' }] : [])]
  const spans = call.turns.map((turn, i) => {
    const next = call.turns[i + 1]?.t ?? dur
    return { ...turn, i, end: Math.max(turn.t + 0.6, next - 0.3) }
  })
  return (
    <div data-testid="timeline" className="px-4 pb-3 pt-2">
      <svg viewBox={`0 0 ${W} 46`} className="h-[46px] w-full" preserveAspectRatio="none" role="img" aria-label="call timeline">
        <rect x={0} y={16} width={W} height={14} rx={3} fill="#1C2430" />
        {spans.map((s) =>
          s.speaker === 'tool' ? (
            <rect key={s.i} x={x(s.t) - 1} y={13} width={2} height={20} fill="#8B96A5" />
          ) : (
            <rect key={s.i} x={x(s.t)} y={16} width={Math.max(2, x(s.end) - x(s.t))} height={14} rx={2}
              fill={s.speaker === 'agent' ? '#3DD6B5' : '#8AB4FF'} opacity={s.speaker === 'agent' ? 0.55 : 0.4} />
          ),
        )}
        {deadlines.filter((d) => d.t < dur).map((d) => (
          <g key={d.t}>
            <line x1={x(d.t)} x2={x(d.t)} y1={4} y2={42} stroke="#F2B53D" strokeDasharray="3 3" strokeWidth={1.5} />
          </g>
        ))}
        {findings.filter((f) => f.t !== null).map((f, i) => (
          <circle key={i} cx={x(f.t as number)} cy={23} r={6} fill={f.severity === 'critical' ? '#FF5D5D' : '#F2B53D'} stroke="#0D1117" strokeWidth={2} />
        ))}
      </svg>
      <div className="relative mt-0.5 h-4 font-mono text-[10px] text-dim">
        <span className="absolute left-0">0:00</span>
        {deadlines.filter((d) => d.t < dur).map((d) => (
          <span key={d.t} className="absolute -translate-x-1/2 text-warn" style={{ left: `${(d.t / dur) * 100}%` }}>{d.label}</span>
        ))}
        <span className="absolute right-0">{clock(dur)}</span>
      </div>
    </div>
  )
}
