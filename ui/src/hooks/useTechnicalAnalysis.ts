import { useState, useEffect } from 'react'
import { fetchTechnicalAnalysis } from '../api'
import type { TechnicalAnalysis } from '../api'

export function useTechnicalAnalysis(token: string) {
  const [data, setData] = useState<TechnicalAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    setLoading(true)
    setError(null)
    fetchTechnicalAnalysis(token)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [token])

  return { data, loading, error }
}