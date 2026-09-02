import { useState } from 'react'
import { askQuestion } from './api'
import { COMPANY_NAMES, type CompanyFilter, type GroundedAnswer } from './types'

const TABS: CompanyFilter[] = ['ALL', 'VRT', 'SNOW']

type Status = 'idle' | 'loading' | 'error'

function App() {
  const [company, setCompany] = useState<CompanyFilter>('ALL')
  const [question, setQuestion] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState('')
  const [result, setResult] = useState<GroundedAnswer | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || status === 'loading') return

    setStatus('loading')
    setError('')

    try {
      const companyName = company === 'ALL' ? undefined : COMPANY_NAMES[company]
      const answer = await askQuestion(question.trim(), companyName)
      setResult(answer)
      setStatus('idle')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setStatus('error')
    }
  }

  return (
    <div className="min-h-screen bg-bg font-sans">
      <div className="mx-auto max-w-[1100px] px-6 py-16">
        <header className="mb-12">
          <h1 className="inline-block border-b-2 border-cyan pb-2 text-sm font-semibold uppercase tracking-[0.2em] text-white">
            Financial Research Assistant
          </h1>
          <nav className="mt-6 flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setCompany(tab)}
                className={`border px-4 py-1.5 font-mono text-xs uppercase tracking-wider transition-colors ${
                  company === tab
                    ? 'border-cyan bg-cyan/10 text-cyan'
                    : 'border-grid text-muted hover:border-muted hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </header>

        <form onSubmit={handleSubmit} className="mb-10">
          <div className="flex items-stretch gap-0">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about the corpus..."
              className="flex-1 border border-grid bg-panel px-4 py-3 font-mono text-sm text-white outline-none placeholder:text-muted focus:border-cyan"
            />
          </div>
          <div className="mt-3 flex justify-end">
            <button
              type="submit"
              disabled={status === 'loading'}
              className="border border-cyan px-6 py-2 font-mono text-xs uppercase tracking-wider text-cyan transition-colors hover:bg-cyan/10 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Run Query
            </button>
          </div>
        </form>

        <section className="border-l-2 border-cyan bg-panel px-6 py-8 min-h-[160px]">
          {status === 'loading' && (
            <p className="font-mono text-sm text-white">
              <span className="cursor-blink">▌</span>
            </p>
          )}

          {status === 'error' && (
            <p className="font-mono text-sm text-amber whitespace-pre-wrap">{error}</p>
          )}

          {status === 'idle' && !result && (
            <p className="flex h-full items-center justify-center py-8 text-center font-mono text-sm text-muted">
              Enter a question to query the corpus.
            </p>
          )}

          {status === 'idle' && result && (
            <p className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-white">
              {result.answer}
            </p>
          )}
        </section>

        {status === 'idle' && result && result.citations.length > 0 && (
          <section className="mt-8">
            <h2 className="mb-3 font-sans text-xs font-semibold uppercase tracking-[0.2em] text-muted">
              Sources
            </h2>
            <div className="flex flex-col gap-2">
              {result.citations.map((c) => (
                <div key={c.marker} className="flex gap-3 font-mono text-xs">
                  <span className="text-amber">{c.marker}</span>
                  <span className="text-muted">
                    {c.company} · {c.doc_type} · {c.fiscal_period} · {c.section}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

export default App
