import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useBrief } from '../../hooks/useBrief'

interface Props {
  token: string
}

const HORIZONS = [
  { value: 'short', label: 'Short (days)' },
  { value: 'medium', label: 'Medium (weeks)' },
  { value: 'long', label: 'Long (months)' },
]

export default function BriefPanel({ token }: Props) {
  const [horizon, setHorizon] = useState('medium')
  const { data, loading, error, generate } = useBrief()

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wide">
          Investment Brief
        </h2>
        <div className="flex items-center gap-3">
          <select
            value={horizon}
            onChange={e => setHorizon(e.target.value)}
            className="bg-surface border border-border text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-accent"
          >
            {HORIZONS.map(h => (
              <option key={h.value} value={h.value}>{h.label}</option>
            ))}
          </select>
          <button
            onClick={() => generate(token, horizon)}
            disabled={loading}
            className="bg-accent hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-medium px-4 py-1.5 rounded-lg transition-colors"
          >
            {loading ? 'Generating...' : 'Generate Brief'}
          </button>
        </div>
      </div>

      <div className="flex-1 bg-surface border border-border rounded-xl p-5 overflow-y-auto">
        {!data && !loading && !error && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <p className="text-muted text-sm">Select a token and click Generate Brief</p>
            <p className="text-muted text-xs mt-1">Takes 15-20 seconds — powered by Claude</p>
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-sm text-muted">Analyzing {token}...</p>
            <p className="text-xs text-muted mt-1">Fetching market data, technicals, and news</p>
          </div>
        )}

        {error && (
          <div className="text-negative text-sm p-4 bg-negative/10 rounded-lg">
            Error: {error}
          </div>
        )}

        {data && (
          <div className="brief-content">
            <ReactMarkdown>{data.brief_markdown}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}