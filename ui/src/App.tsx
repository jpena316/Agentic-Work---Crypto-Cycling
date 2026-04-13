import { useState } from 'react'
import TokenSelector from './components/TokenSelector'
import MarketSnapshot from './components/Dashboard/MarketSnapshot'
import TechnicalSignals from './components/Dashboard/TechnicalSignals'
import SentimentPanel from './components/Dashboard/SentimentPanel'
import BriefPanel from './components/Chat/BriefPanel'
import { useMarketData } from './hooks/useMarketData'
import { useTechnicalAnalysis } from './hooks/useTechnicalAnalysis'
import { useNewsSentiment } from './hooks/useNewsSentiment'

export default function App() {
  const [token, setToken] = useState('bitcoin')

  const market = useMarketData(token)
  const technical = useTechnicalAnalysis(token)
  const sentiment = useNewsSentiment(token)

  const loading = market.loading || technical.loading || sentiment.loading

  return (
    <div className="min-h-screen bg-background text-white">

      {/* Header */}
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-accent rounded-lg flex items-center justify-center text-xs font-bold">₿</div>
          <span className="font-semibold text-white">Crypto Research Agent</span>
        </div>
        <TokenSelector value={token} onChange={setToken} />
      </header>

      {/* Main layout */}
      <main className="flex h-[calc(100vh-65px)]">

        {/* Left — Dashboard */}
        <div className="w-[420px] border-r border-border p-5 overflow-y-auto flex flex-col gap-6">
          {loading && (
            <div className="flex items-center gap-2 text-muted text-sm">
              <div className="w-4 h-4 border border-accent border-t-transparent rounded-full animate-spin" />
              Loading {token} data...
            </div>
          )}

          {market.data && <MarketSnapshot data={market.data} />}
          {technical.data && <TechnicalSignals data={technical.data} />}
          {sentiment.data && <SentimentPanel data={sentiment.data} />}

          {(market.error || technical.error || sentiment.error) && (
            <div className="text-negative text-sm p-3 bg-negative/10 rounded-lg">
              {market.error || technical.error || sentiment.error}
            </div>
          )}
        </div>

        {/* Right — Brief */}
        <div className="flex-1 p-5">
          <BriefPanel token={token} />
        </div>

      </main>
    </div>
  )
}