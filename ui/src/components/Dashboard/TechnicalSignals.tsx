import type { TechnicalAnalysis } from '../../api'

interface Props {
  data: TechnicalAnalysis
}

function SignalBadge({ value }: { value: string }) {
  const colors: Record<string, string> = {
    bullish: 'bg-positive/10 text-positive border-positive/20',
    bearish: 'bg-negative/10 text-negative border-negative/20',
    overbought: 'bg-negative/10 text-negative border-negative/20',
    oversold: 'bg-positive/10 text-positive border-positive/20',
    neutral: 'bg-neutral/10 text-neutral border-neutral/20',
    increasing: 'bg-positive/10 text-positive border-positive/20',
    decreasing: 'bg-negative/10 text-negative border-negative/20',
    stable: 'bg-neutral/10 text-neutral border-neutral/20',
    uptrend: 'bg-positive/10 text-positive border-positive/20',
    downtrend: 'bg-negative/10 text-negative border-negative/20',
    sideways: 'bg-neutral/10 text-neutral border-neutral/20',
  }
  const cls = colors[value] ?? 'bg-gray-500/10 text-gray-400 border-gray-500/20'
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${cls}`}>
      {value}
    </span>
  )
}

function Row({ label, value, badge }: { label: string, value: string, badge?: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <span className="text-sm text-muted">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm text-white font-medium">{value}</span>
        {badge && <SignalBadge value={badge} />}
      </div>
    </div>
  )
}

export default function TechnicalSignals({ data }: Props) {
  const s = data.signals
  return (
    <div>
      <h2 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">
        Technical Signals
      </h2>
      <div className="bg-surface border border-border rounded-xl p-4">
        <Row label="RSI (14)" value={s.rsi_14.toFixed(1)} badge={s.rsi_signal} />
        <Row label="SMA Cross" value={`$${s.sma_7.toLocaleString()} / $${s.sma_30.toLocaleString()}`} badge={s.sma_cross_signal} />
        <Row label="Volume Trend" value={`${s.volume_ratio}x avg`} badge={s.volume_trend} />
        <Row label="Price Trend" value={`${data.days_analyzed}d`} badge={s.price_trend} />
        <Row label="Support" value={`$${s.support_level.toLocaleString()}`} />
        <Row label="Resistance" value={`$${s.resistance_level.toLocaleString()}`} />
      </div>
      <p className="text-xs text-muted mt-2 leading-relaxed">{data.summary}</p>
    </div>
  )
}