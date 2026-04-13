import type { MarketData } from '../../api'

interface Props {
  data: MarketData
}

function fmt(n: number, decimals = 2) {
  return n.toLocaleString('en-US', { maximumFractionDigits: decimals })
}

function fmtLarge(n: number) {
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`
  return `$${fmt(n)}`
}

function PctBadge({ value }: { value: number }) {
  const positive = value >= 0
  return (
    <span className={`text-sm font-medium ${positive ? 'text-positive' : 'text-negative'}`}>
      {positive ? '+' : ''}{value.toFixed(2)}%
    </span>
  )
}

function Card({ label, value, sub }: { label: string, value: string, sub?: React.ReactNode }) {
  return (
    <div className="bg-surface border border-border rounded-xl p-4">
      <p className="text-xs text-muted uppercase tracking-wide mb-1">{label}</p>
      <p className="text-xl font-bold text-white">{value}</p>
      {sub && <div className="mt-1">{sub}</div>}
    </div>
  )
}

export default function MarketSnapshot({ data }: Props) {
  return (
    <div>
      <h2 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">
        Market Snapshot
      </h2>
      <div className="grid grid-cols-2 gap-3">
        <Card
          label="Price"
          value={`$${fmt(data.price_usd)}`}
          sub={
            <div className="flex gap-3">
              <span className="text-xs text-muted">24h: <PctBadge value={data.price_change_24h_pct} /></span>
              <span className="text-xs text-muted">7d: <PctBadge value={data.price_change_7d_pct} /></span>
            </div>
          }
        />
        <Card label="Market Cap" value={fmtLarge(data.market_cap_usd)} />
        <Card label="24h Volume" value={fmtLarge(data.volume_24h_usd)} />
        <Card
          label="ATH Drawdown"
          value={`${data.ath_drawdown_pct.toFixed(1)}%`}
          sub={<span className="text-xs text-muted">ATH: ${fmt(data.ath_usd)}</span>}
        />
      </div>
    </div>
  )
}