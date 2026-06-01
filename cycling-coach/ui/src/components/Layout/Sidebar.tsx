import { useState } from "react";
import type { BikeProfile } from "../../api";

export type View = "dashboard" | "bikes" | "plan";

interface SidebarProps {
  activeView: View;
  onViewChange: (view: View) => void;
  onRunAnalysis: (goals: string[], bikes: string[]) => void;
  isLoading: boolean;
  elapsedSeconds: number;
  availableBikes: BikeProfile[];
}

const NAV_ITEMS: { view: View; label: string; icon: string }[] = [
  { view: "dashboard", label: "Dashboard", icon: "📊" },
  { view: "bikes", label: "Bike Rankings", icon: "🚲" },
  { view: "plan", label: "Training Plan", icon: "📅" },
];

const DEFAULT_GOALS = [
  "Build endurance for a century ride",
  "Improve climbing ability",
  "Lose weight while maintaining power",
].join("\n");

export function Sidebar({
  activeView,
  onViewChange,
  onRunAnalysis,
  isLoading,
  elapsedSeconds,
  availableBikes,
}: SidebarProps) {
  const [goalsText, setGoalsText] = useState(DEFAULT_GOALS);
  const [selectedBikes, setSelectedBikes] = useState<Set<string>>(
    new Set(availableBikes.slice(0, 4).map((b) => b.name))
  );

  const toggleBike = (name: string) => {
    setSelectedBikes((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  const handleRun = () => {
    const goals = goalsText
      .split("\n")
      .map((g) => g.trim())
      .filter(Boolean);
    const bikes = Array.from(selectedBikes);
    if (goals.length && bikes.length) {
      onRunAnalysis(goals, bikes);
    }
  };

  const formatElapsed = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
  };

  return (
    <aside
      className="flex flex-col w-60 shrink-0 border-r overflow-y-auto"
      style={{
        background: "var(--color-surface)",
        borderColor: "var(--color-border)",
        height: "calc(100vh - 56px)",
      }}
    >
      {/* Navigation */}
      <nav className="p-3 border-b" style={{ borderColor: "var(--color-border)" }}>
        {NAV_ITEMS.map(({ view, label, icon }) => (
          <button
            key={view}
            onClick={() => onViewChange(view)}
            className="flex w-full items-center gap-2.5 px-3 py-2 rounded text-sm font-medium transition-colors"
            style={{
              background: activeView === view ? "rgba(249,115,22,0.12)" : "transparent",
              color: activeView === view ? "var(--color-accent)" : "#e5e7eb",
            }}
          >
            <span>{icon}</span>
            {label}
          </button>
        ))}
      </nav>

      {/* Run Analysis form */}
      <div className="flex flex-col gap-4 p-4 flex-1">
        <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--color-muted)" }}>
          Run Analysis
        </p>

        {/* Goals */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs" style={{ color: "var(--color-muted)" }}>
            Goals (one per line)
          </label>
          <textarea
            value={goalsText}
            onChange={(e) => setGoalsText(e.target.value)}
            rows={4}
            className="w-full rounded px-2.5 py-2 text-xs resize-none border outline-none focus:border-orange-500 transition-colors"
            style={{
              background: "var(--color-background)",
              borderColor: "var(--color-border)",
              color: "#e5e7eb",
            }}
            placeholder="Enter your goals…"
          />
        </div>

        {/* Bikes */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs" style={{ color: "var(--color-muted)" }}>
            Bikes to evaluate
          </label>
          <div className="flex flex-col gap-1.5">
            {availableBikes.map((bike) => (
              <label key={bike.name} className="flex items-start gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={selectedBikes.has(bike.name)}
                  onChange={() => toggleBike(bike.name)}
                  className="mt-0.5 accent-orange-500"
                />
                <span
                  className="text-xs leading-relaxed"
                  style={{ color: selectedBikes.has(bike.name) ? "#e5e7eb" : "var(--color-muted)" }}
                >
                  {bike.name}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Run button */}
        <button
          onClick={handleRun}
          disabled={isLoading || !goalsText.trim() || selectedBikes.size === 0}
          className="w-full py-2.5 rounded font-semibold text-sm transition-opacity disabled:opacity-50"
          style={{
            background: "var(--color-accent)",
            color: "#fff",
          }}
        >
          {isLoading ? `Running… ${formatElapsed(elapsedSeconds)}` : "▶ Run Analysis"}
        </button>

        {isLoading && (
          <p className="text-xs text-center" style={{ color: "var(--color-muted)" }}>
            Fetching Strava data + calling Claude. This takes 2–3 minutes.
          </p>
        )}
      </div>
    </aside>
  );
}
