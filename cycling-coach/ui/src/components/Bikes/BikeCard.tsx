import { Star } from "lucide-react";
import type { BikeProfile } from "@/api";
import { Card } from "@/components/shared/Card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface BikeCardProps {
  bike: BikeProfile;
  rank: number;
  matchScore?: number;
  rationale?: string;
  isBestOverall?: boolean;
}

function ScoreRing({ score }: { score: number }) {
  const color =
    score >= 80 ? "text-positive border-positive" :
    score >= 65 ? "text-accent border-accent" :
    "text-muted border-muted";

  return (
    <div className="flex flex-col items-center gap-0.5 shrink-0">
      <div className={cn("w-12 h-12 rounded-full border-2 flex items-center justify-center font-heading font-bold text-sm", color)}>
        {score}
      </div>
      <p className="text-[10px] text-muted">match</p>
    </div>
  );
}

function Spec({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-muted">{label}: </span>
      <span className="text-text">{value}</span>
    </div>
  );
}

export function BikeCard({ bike, rank, matchScore, rationale, isBestOverall }: BikeCardProps) {
  return (
    <Card
      className={cn(
        "flex flex-col gap-3 relative",
        isBestOverall && "border-accent"
      )}
    >
      {isBestOverall && (
        <Badge className="absolute top-4 right-4 gap-1">
          <Star className="h-3 w-3" fill="currentColor" />
          Best Overall
        </Badge>
      )}

      <div className="flex items-start gap-3">
        <div
          className={cn(
            "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0",
            rank === 1 ? "bg-accent text-background" : "bg-background text-muted"
          )}
        >
          {rank}
        </div>

        <div className="flex-1 min-w-0">
          <p className="font-heading font-semibold text-sm text-text leading-tight">{bike.name}</p>
          <p className="text-xs capitalize text-muted">{bike.category || "—"}</p>
        </div>

        {matchScore !== undefined && <ScoreRing score={matchScore} />}
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
        <Spec label="Price" value={bike.price_usd ? `$${bike.price_usd.toLocaleString()}` : "—"} />
        <Spec label="Weight" value={bike.weight_kg ? `${bike.weight_kg} kg` : "—"} />
        <Spec label="Groupset" value={bike.components.groupset || "—"} />
        <Spec label="Brakes" value={bike.components.brakes || "—"} />
      </div>

      {bike.terrain_fit.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {bike.terrain_fit.map((t) => (
            <span key={t} className="text-xs px-1.5 py-0.5 rounded bg-background text-muted">
              {t}
            </span>
          ))}
        </div>
      )}

      {rationale && (
        <p className="text-xs leading-relaxed border-t border-border pt-2 text-muted">
          {rationale}
        </p>
      )}
    </Card>
  );
}
