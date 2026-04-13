import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
  } from 'recharts'
  import { useEffect, useState } from 'react'
  import { fetchPriceHistory } from '../../api'
  import type { PricePoint } from '../../api'
  
  interface Props {
    token: string
  }
  
  function formatDate(timestamp: number) {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })
  }
  
  function formatPrice(price: number) {
    if (price >= 1000) return `$${(price / 1000).toFixed(1)}k`
    return `$${price.toFixed(2)}`
  }
  
  export default function PriceChart({ token }: Props) {
    const [data, setData] = useState<PricePoint[]>([])
    const [loading, setLoading] = useState(false)
  
    useEffect(() => {
      if (!token) return
      setLoading(true)
      fetchPriceHistory(token, 30)
        .then(setData)
        .catch(console.error)
        .finally(() => setLoading(false))
    }, [token])
  
    if (loading) {
      return (
        <div className="h-40 flex items-center justify-center text-muted text-sm">
          Loading chart...
        </div>
      )
    }
  
    if (!data.length) return null
  
    const prices = data.map(d => d.price)
    const minPrice = Math.min(...prices)
    const maxPrice = Math.max(...prices)
    const isPositive = prices[prices.length - 1] >= prices[0]
  
    return (
      <div>
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">
          30-Day Price
        </h2>
        <div className="bg-surface border border-border rounded-xl p-4">
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor={isPositive ? '#22c55e' : '#ef4444'}
                    stopOpacity={0.3}
                  />
                  <stop
                    offset="95%"
                    stopColor={isPositive ? '#22c55e' : '#ef4444'}
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatDate}
                tick={{ fontSize: 10, fill: '#6b7280' }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[minPrice * 0.98, maxPrice * 1.02]}
                tickFormatter={formatPrice}
                tick={{ fontSize: 10, fill: '#6b7280' }}
                tickLine={false}
                axisLine={false}
                width={55}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1d27',
                  border: '1px solid #2a2d3a',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                labelFormatter={formatDate}
                formatter={(value: number) => [`$${value.toLocaleString()}`, 'Price']}
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke={isPositive ? '#22c55e' : '#ef4444'}
                strokeWidth={2}
                fill="url(#priceGradient)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }