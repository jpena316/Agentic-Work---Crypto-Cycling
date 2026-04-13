import axios from 'axios'

const BASE_URL = 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

// Types
export interface MarketData {
  token: string
  name: string
  symbol: string
  price_usd: number
  market_cap_usd: number
  volume_24h_usd: number
  price_change_24h_pct: number
  price_change_7d_pct: number
  circulating_supply: number
  ath_usd: number
  ath_drawdown_pct: number
  last_updated: string
}

export interface TechnicalSignals {
  sma_7: number
  sma_30: number
  sma_cross_signal: string
  rsi_14: number
  rsi_signal: string
  volume_trend: string
  volume_ratio: number
  price_trend: string
  support_level: number
  resistance_level: number
}

export interface TechnicalAnalysis {
  token: string
  days_analyzed: number
  current_price: number
  signals: TechnicalSignals
  summary: string
}

export interface NewsItem {
  title: string
  source: string
  published_at: string
  url: string
  sentiment: string
}

export interface NewsSentiment {
  token: string
  days_analyzed: number
  total_articles: number
  sentiment_breakdown: Record<string, number>
  sentiment_score: number
  top_headlines: NewsItem[]
}

export interface InvestmentBrief {
  token: string
  generated_at: string
  brief_markdown: string
}

// API calls
export const fetchMarketData = (token: string): Promise<MarketData> =>
  api.get(`/market/${token}`).then(r => r.data)

export const fetchTechnicalAnalysis = (token: string): Promise<TechnicalAnalysis> =>
  api.get(`/analysis/${token}`).then(r => r.data)

export const fetchNewsSentiment = (token: string): Promise<NewsSentiment> =>
  api.get(`/sentiment/${token}`).then(r => r.data)

export const fetchBrief = (token: string, horizon: string): Promise<InvestmentBrief> =>
  api.get(`/brief/${token}?horizon=${horizon}`).then(r => r.data)