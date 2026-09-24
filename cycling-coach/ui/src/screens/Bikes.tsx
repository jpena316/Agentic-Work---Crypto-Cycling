import { Plus, Bike as BikeIcon } from "lucide-react";
import type { BikeProfile, BikeRecommendations } from "@/api";
import { Card } from "@/components/shared/Card";
import { BikeCard } from "@/components/Bikes/BikeCard";

interface BikesProps {
  profiles: BikeProfile[];
  recommendations: BikeRecommendations | null;
}

export function Bikes({ profiles, recommendations }: BikesProps) {
  const orderedProfiles = recommendations
    ? [...profiles].sort((a, b) => {
        const ra = recommendations.ranked.indexOf(a.name);
        const rb = recommendations.ranked.indexOf(b.name);
        return (ra === -1 ? 999 : ra) - (rb === -1 ? 999 : rb);
      })
    : profiles;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="font-heading text-xl font-bold text-text">Bikes</h1>
        <p className="text-sm text-muted mt-1">
          Candidate bikes ranked against your riding profile.
        </p>
      </div>

      {recommendations?.summary && (
        <Card className="border-accent/30">
          <p className="text-xs font-semibold uppercase tracking-wider text-accent mb-2">
            Coach Summary
          </p>
          <p className="text-sm leading-relaxed text-text">{recommendations.summary}</p>
        </Card>
      )}

      {profiles.length === 0 ? (
        <Card className="text-center py-10">
          <BikeIcon className="h-8 w-8 text-muted mx-auto mb-3" />
          <p className="text-base font-medium text-text mb-1">No Bikes Loaded</p>
          <p className="text-sm text-muted">
            Bike profiles will appear here once the API is connected.
          </p>
        </Card>
      ) : (
        <>
          {!recommendations && (
            <p className="text-sm text-muted">
              Run an analysis from the Overview screen to see personalised rankings and match scores.
            </p>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {orderedProfiles.map((bike, i) => {
              const rank = recommendations
                ? recommendations.ranked.indexOf(bike.name) + 1
                : i + 1;
              return (
                <BikeCard
                  key={bike.name}
                  bike={bike}
                  rank={rank || i + 1}
                  matchScore={recommendations?.match_scores[bike.name]}
                  rationale={recommendations?.rationale[bike.name]}
                  isBestOverall={recommendations?.best_overall === bike.name}
                />
              );
            })}

            <Card className="flex flex-col items-center justify-center gap-2 border-dashed text-center min-h-[180px] cursor-default">
              <Plus className="h-6 w-6 text-muted" />
              <p className="text-sm text-muted">Add a bike</p>
              <p className="text-xs text-muted">Coming soon</p>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
