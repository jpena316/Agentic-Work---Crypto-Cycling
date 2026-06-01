import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { BikeProfile, BikeRecommendations } from "../../api";
import { BikeCard } from "./BikeCard";

interface BikeRankingsProps {
  profiles: BikeProfile[];
  recommendations: BikeRecommendations | null;
}

const SCORE_COLOR = (score: number) =>
  score >= 80 ? "#22c55e" : score >= 65 ? "#f97316" : "#6b7280";

interface TooltipPayload {
  payload?: { name: string; score: number };
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayload[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <div
      className="rounded border px-3 py-2 text-xs"
      style={{
        background: "#1a1d27",
        borderColor: "var(--color-border)",
        color: "#e5e7eb",
      }}
    >
      <p className="font-semibold mb-0.5">{d.name}</p>
      <p style={{ color: SCORE_COLOR(d.score) }}>Match score: {d.score}</p>
    </div>
  );
}

export function BikeRankings({ profiles, recommendations }: BikeRankingsProps) {
  // Build display order: ranked first if we have recommendations, else alphabetical
  const orderedProfiles = recommendations
    ? [...profiles].sort((a, b) => {
        const ra = recommendations.ranked.indexOf(a.name);
        const rb = recommendations.ranked.indexOf(b.name);
        return (ra === -1 ? 999 : ra) - (rb === -1 ? 999 : rb);
      })
    : profiles;

  const chartData = recommendations
    ? recommendations.ranked
        .map((name) => ({
          name: name.length > 22 ? name.slice(0, 20) + "…" : name,
          fullName: name,
          score: recommendations.match_scores[name] ?? 0,
        }))
        .sort((a, b) => b.score - a.score)
    : [];

  return (
    <div className="flex flex-col gap-6">
      {/* Summary */}
      {recommendations?.summary && (
        <div
          className="rounded-lg border p-5"
          style={{
            background: "var(--color-surface)",
            borderColor: "rgba(249,115,22,0.3)",
          }}
        >
          <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--color-accent)" }}>
            Coach Summary
          </p>
          <p className="text-sm leading-relaxed" style={{ color: "#d1d5db" }}>
            {recommendations.summary}
          </p>
        </div>
      )}

      {/* Bar chart */}
      {chartData.length > 0 && (
        <div
          className="rounded-lg border p-5"
          style={{
            background: "var(--color-surface)",
            borderColor: "var(--color-border)",
          }}
        >
          <h3 className="text-sm font-semibold mb-4 text-white">Match Scores</h3>
          <ResponsiveContainer width="100%" height={chartData.length * 48 + 20}>
            <BarChart
              layout="vertical"
              data={chartData}
              margin={{ top: 0, right: 40, left: 8, bottom: 0 }}
            >
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "#6b7280" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} width={130} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
              <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                {chartData.map((entry) => (
                  <Cell key={entry.fullName} fill={SCORE_COLOR(entry.score)} />
                ))}
                <LabelList dataKey="score" position="right" style={{ fontSize: 11, fill: "#9ca3af" }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Empty state when no recommendations yet */}
      {!recommendations && profiles.length === 0 && (
        <div
          className="rounded-lg border p-8 text-center"
          style={{
            background: "var(--color-surface)",
            borderColor: "var(--color-border)",
          }}
        >
          <p className="text-4xl mb-3">🚲</p>
          <p className="text-base font-medium text-white mb-1">No Bikes Loaded</p>
          <p className="text-sm" style={{ color: "var(--color-muted)" }}>
            Bike profiles will appear here once the API is connected.
          </p>
        </div>
      )}

      {/* Bike cards */}
      {orderedProfiles.length > 0 && (
        <div>
          {!recommendations && (
            <p className="text-sm mb-4" style={{ color: "var(--color-muted)" }}>
              Run an analysis to see personalised rankings and match scores.
            </p>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {orderedProfiles.map((bike) => {
              const rank = recommendations
                ? recommendations.ranked.indexOf(bike.name) + 1
                : 0;
              return (
                <BikeCard
                  key={bike.name}
                  bike={bike}
                  rank={rank || orderedProfiles.indexOf(bike) + 1}
                  matchScore={recommendations?.match_scores[bike.name]}
                  rationale={recommendations?.rationale[bike.name]}
                  isBestOverall={recommendations?.best_overall === bike.name}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
