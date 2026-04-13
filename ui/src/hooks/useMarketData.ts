import { useState, useEffect } from 'react'
import { fetchMarketData } from '../api'
import type { MarketData } from '../api'

export function useMarketData(token: string) {
  const [data, setData] = useState<MarketData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    setLoading(true)
    setError(null)
    fetchMarketData(token)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [token])

  return { data, loading, error }
}