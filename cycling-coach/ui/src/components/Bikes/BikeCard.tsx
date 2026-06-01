import type { BikeProfile } from "../../api";

interface BikeCardProps {
  bike: BikeProfile;
  rank: number;
  matchScore?: number;
  rationale?: string;
  isBestOverall?: boolean;
}

function ScoreRing({ score }: { score: number }) {
  const color =
    score >= 80
      ? "var(--color-positive)"
      : score >= 65
      ? "var(--color-accent)"
      : "var(--color-muted)";

  return (
    <div className="flex flex-col items-center gap-0.5">
      <div
        className="w-12 h-12 rounded-full border-2 flex items-center justify-center font-bold text-sm"
        style={{ borderColor: color, color }}
      >
        {score}
      </div>
      <p className="text-xs" style={{ color: "var(--color-muted)" }}>
        match
      </p>
    </div>
  );
}

export function BikeCard({
  bike,
  rank,
  matchScore,
  rationale,
  isBestOverall,
}: BikeCardProps) {
  return (
    <div
      className="rounded-lg border p-4 flex flex-col gap-3 relative"
      style={{
        background: "var(--color-surface)",
        borderColor: isBestOverall ? "var(--color-accent)" : "var(--color-border)",
      }}
    >
      {/* Best overall badge */}
      {isBestOverall && (
        <span
          className="absolute top-3 right-3 text-xs px-2 py-0.5 rounded-full font-semibold"
          style={{
            background: "rgba(249,115,22,0.18)",
            color: "var(--color-accent)",
          }}
        >
          ★ Best Overall
        </span>
      )}

      {/* Rank + name + score */}
      <div className="flex items-start gap-3">
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
          style={{
            background: rank === 1 ? "var(--color-accent)" : "var(--color-background)",
            color: rank === 1 ? "#fff" : "var(--color-muted)",
          }}
        >
          {rank}
        </div>

        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-white leading-tight">{bike.name}</p>
          <p className="text-xs capitalize" style={{ color: "var(--color-muted)" }}>
            {bike.category}
          </p>
        </div>

        {matchScore !== undefined && <ScoreRing score={matchScore} />}
      </div>

      {/* Quick specs */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
        <Spec label="Price" value={`$${bike.price_usd.toLocaleString()}`} />
        <Spec label="Weight" value={`${bike.weight_kg} kg`} />
        <Spec label="Groupset" value={bike.components.groupset} />
        <Spec label="Brakes" value={bike.components.brakes} />
        <Spec label="Stack" value={`${bike.geometry.stack} mm`} />
        <Spec label="Reach" value={`${bike.geometry.reach} mm`} />
      </div>

      {/* Terrain tags */}
      <div className="flex flex-wrap gap-1">
        {bike.terrain_fit.map((t) => (
          <span
            key={t}
            className="text-xs px-1.5 py-0.5 rounded"
            style={{
              background: "var(--color-background)",
              color: "var(--color-muted)",
            }}
          >
            {t}
          </span>
        ))}
      </div>

      {/* Claude's rationale */}
      {rationale && (
        <p className="text-xs leading-relaxed border-t pt-2" style={{ color: "#9ca3af", borderColor: "var(--color-border)" }}>
          {rationale}
        </p>
      )}
    </div>
  );
}

function Spec({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span style={{ color: "var(--color-muted)" }}>{label}: </span>
      <span style={{ color: "#e5e7eb" }}>{value}</span>
    </div>
  );
}
