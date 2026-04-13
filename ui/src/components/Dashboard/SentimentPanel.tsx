import type { NewsSentiment } from '../../api'

interface Props {
  data: NewsSentiment
}

export default function SentimentPanel({ data }: Props) {
  const score = data.sentiment_score
  const pct = ((score + 1) / 2) * 100

  const scoreColor = score > 0.1
    ? 'text-positive'
    : score < -0.1
    ? 'text-negative'
    : 'text-neutral'

  const sentimentLabel = score > 0.1 ? 'Positive' : score < -0.1 ? 'Negative' : 'Neutral'

  return (
    <div>
      <h2 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">
        News Sentiment
      </h2>
      <div className="bg-surface border border-border rounded-xl p-4">

        {/* Score bar */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted">{data.total_articles} articles · {data.days_analyzed}d</span>
          <span className={`text-sm font-bold ${scoreColor}`}>
            {score > 0 ? '+' : ''}{score.toFixed(2)} {sentimentLabel}
          </span>
        </div>
        <div className="w-full bg-border rounded-full h-1.5 mb-4">
          <div
            className="h-1.5 rounded-full bg-accent transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>

        {/* Breakdown */}
        <div className="flex gap-4 mb-4 text-xs">
          <span className="text-positive">↑ {data.sentiment_breakdown.positive} positive</span>
          <span className="text-negative">↓ {data.sentiment_breakdown.negative} negative</span>
          <span className="text-muted">→ {data.sentiment_breakdown.neutral} neutral</span>
        </div>

        {/* Headlines */}
        <div className="space-y-2">
          {data.top_headlines.slice(0, 4).map((item, i) => (
            <a
              key={i}
              href={item.url}
              target="_blank"
              rel="noreferrer"
              className="block text-xs text-gray-400 hover:text-white transition-colors leading-relaxed truncate"
            >
              <span className={
                item.sentiment === 'positive' ? 'text-positive mr-1' :
                item.sentiment === 'negative' ? 'text-negative mr-1' :
                'text-muted mr-1'
              }>●</span>
              {item.title}
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}