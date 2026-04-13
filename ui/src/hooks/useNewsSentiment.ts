import { useState, useEffect } from 'react'
import { fetchNewsSentiment } from '../api'
import type { NewsSentiment } from '../api'

export function useNewsSentiment(token: string) {
  const [data, setData] = useState<NewsSentiment | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    setLoading(true)
    setError(null)
    fetchNewsSentiment(token)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [token])

  return { data, loading, error }
}