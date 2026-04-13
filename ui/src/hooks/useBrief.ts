import { useState } from 'react'
import { fetchBrief } from '../api'
import type { InvestmentBrief } from '../api'

export function useBrief() {
  const [data, setData] = useState<InvestmentBrief | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generate = async (token: string, horizon: string) => {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const result = await fetchBrief(token, horizon)
      setData(result)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return { data, loading, error, generate }
}