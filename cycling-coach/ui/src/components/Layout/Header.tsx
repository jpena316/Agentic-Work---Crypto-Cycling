interface HeaderProps {
  isAnalysisRunning: boolean;
  apiOnline: boolean;
}

export function Header({ isAnalysisRunning, apiOnline }: HeaderProps) {
  return (
    <header
      className="flex items-center justify-between px-6 h-14 border-b"
      style={{
        background: "var(--color-surface)",
        borderColor: "var(--color-border)",
      }}
    >
      <div className="flex items-center gap-3">
        <span className="text-2xl">🚴</span>
        <span className="font-semibold text-lg tracking-tight text-white">
          Cycling Coach
        </span>
        <span
          className="text-xs px-2 py-0.5 rounded font-medium"
          style={{
            background: "rgba(249,115,22,0.15)",
            color: "var(--color-accent)",
          }}
        >
          AI-Powered
        </span>
      </div>

      <div className="flex items-center gap-4">
        {isAnalysisRunning && (
          <div className="flex items-center gap-2 text-sm" style={{ color: "var(--color-accent)" }}>
            <span className="animate-spin">⟳</span>
            <span>Analysis running…</span>
          </div>
        )}
        <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--color-muted)" }}>
          <span
            className="w-2 h-2 rounded-full"
            style={{ background: apiOnline ? "var(--color-positive)" : "var(--color-negative)" }}
          />
          {apiOnline ? "API connected" : "API offline"}
        </div>
      </div>
    </header>
  );
}
