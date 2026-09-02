import type { GroundedAnswer } from './types'

const API_URL = 'http://localhost:8002/ask'

export async function askQuestion(question: string, company?: string): Promise<GroundedAnswer> {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      filters: company ? { company } : null,
    }),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`${response.status} ${response.statusText}: ${text}`)
  }

  return response.json()
}
