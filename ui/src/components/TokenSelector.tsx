interface Props {
    value: string
    onChange: (token: string) => void
  }
  
  const TOKENS = [
    { id: 'bitcoin', label: 'Bitcoin (BTC)' },
    { id: 'ethereum', label: 'Ethereum (ETH)' },
    { id: 'solana', label: 'Solana (SOL)' },
    { id: 'cardano', label: 'Cardano (ADA)' },
    { id: 'ripple', label: 'XRP (XRP)' },
    { id: 'dogecoin', label: 'Dogecoin (DOGE)' },
    { id: 'polkadot', label: 'Polkadot (DOT)' },
    { id: 'chainlink', label: 'Chainlink (LINK)' },
  ]
  
  export default function TokenSelector({ value, onChange }: Props) {
    return (
      <div className="flex items-center gap-4">
        <label className="text-sm text-gray-400 font-medium">Token</label>
        <select
          value={value}
          onChange={e => onChange(e.target.value)}
          className="bg-surface border border-border text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-accent cursor-pointer"
        >
          {TOKENS.map(t => (
            <option key={t.id} value={t.id}>{t.label}</option>
          ))}
        </select>
      </div>
    )
  }