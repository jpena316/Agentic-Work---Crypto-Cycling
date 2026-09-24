import { useMemo } from "react";
import { Play } from "lucide-react";
import type { BikeProfile, CoachingReport } from "@/api";
import { useDerivedMetrics } from "@/hooks/useDerivedMetrics";
import { Card } from "@/components/shared/Card";
import { StatTile } from "@/components/shared/StatTile";
import { WeekPlanList } from "@/components/shared/WeekPlanList";
import { Button } from "@/components/ui/button";
import { calculateTss } from "@/lib/metrics";

interface TodayProps {
  report: CoachingReport | null;
  bikeProfiles: BikeProfile[];
}

const CYCLING_TYPES = new Set(["Ride", "VirtualRide"]);

export function Today({ report, bikeProfiles }: TodayProps) {
  const { activities, ftp, todayPoint, isLoading } = useDerivedMetrics();

  const todayName = useMemo(
    () => new Date().toLocaleDateString(undefined, { weekday: "long" }),
    []
  );

  const plan = report?.training_plan ?? null;
  const todaySession = plan?.days.find((d) => d.day.toLowerCase() === todayName.toLowerCase()) ?? null;

  const lastRide = useMemo(() => {
    const cycling = activities.filter((a) => CYCLING_TYPES.has(a.type));
    if (cycling.length === 0) return null;
    return [...cycling].sort(
      (a, b) => new Date(b.start_date).getTime() - new Date(a.start_date).getTime()
    )[0];
  }, [activities]);

  const lastRideTss = lastRide?.average_watts
    ? Math.round(calculateTss(lastRide.average_watts, ftp, lastRide.moving_time))
    : null;

  const bestBike = report?.bike_recommendations
    ? bikeProfiles.find((b) => b.name === report.bike_recommendations!.best_overall)
    : null;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="font-heading text-xl font-bold text-text">Today</h1>
        <p className="text-sm text-muted mt-1">{todayName}</p>
      </div>

      <Card className="border-accent/30">
        {todaySession ? (
          <div className="flex flex-col gap-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-wider text-accent font-semibold mb-1">
                  {todaySession.intensity}
                </p>
                <h2 className="font-heading text-lg font-bold text-text">
                  {todaySession.workout_type}
                </h2>
                <p className="text-sm text-muted mt-1 max-w-lg">{todaySession.description}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-xs text-muted">Duration</p>
                <p className="font-heading text-xl font-bold text-text">
                  {todaySession.duration_mins > 0 ? `${todaySession.duration_mins} min` : "Off"}
                </p>
                {plan && (
                  <p className="text-xs text-muted mt-1">TSS target {plan.tss_target}</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <Button disabled className="gap-1.5">
                <Play className="h-3.5 w-3.5" fill="currentColor" />
                Start Ride
              </Button>
              <p className="text-xs text-muted">Ride tracking isn't connected yet.</p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted">
            Run an analysis from the Overview screen to generate today's session.
          </p>
        )}
      </Card>

      <div className="grid grid-cols-3 gap-4">
        <StatTile
          label="CTL (Fitness)"
          value={isLoading || !todayPoint ? "—" : todayPoint.ctl.toFixed(0)}
        />
        <StatTile
          label="ATL (Fatigue)"
          value={isLoading || !todayPoint ? "—" : todayPoint.atl.toFixed(0)}
        />
        <StatTile
          label="TSB (Form)"
          value={isLoading || !todayPoint ? "—" : todayPoint.tsb.toFixed(0)}
          trend={todayPoint ? (todayPoint.tsb >= 0 ? "up" : "down") : undefined}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          {plan ? (
            <WeekPlanList days={plan.days} todayName={todayName} />
          ) : (
            <Card>
              <p className="text-sm text-muted">No training plan yet — run an analysis to generate one.</p>
            </Card>
          )}
        </div>

        <div className="flex flex-col gap-4">
          <Card>
            <h2 className="font-heading text-sm font-semibold text-text mb-2">Bike for Today</h2>
            {bestBike ? (
              <div>
                <p className="font-heading font-semibold text-text">{bestBike.name}</p>
                <p className="text-xs text-muted capitalize">{bestBike.category}</p>
              </div>
            ) : (
              <p className="text-sm text-muted">Run an analysis to get a recommendation.</p>
            )}
          </Card>

          <Card>
            <h2 className="font-heading text-sm font-semibold text-text mb-2">Last Ride</h2>
            {lastRide ? (
              <div className="flex flex-col gap-1.5 text-sm">
                <p className="text-text font-medium truncate">{lastRide.name}</p>
                <div className="grid grid-cols-2 gap-1 text-xs text-muted">
                  <span>Distance: <span className="text-text">{(lastRide.distance / 1000).toFixed(1)} km</span></span>
                  <span>Time: <span className="text-text">{Math.round(lastRide.moving_time / 60)} min</span></span>
                  {lastRideTss !== null && (
                    <span>Est. TSS: <span className="text-text">{lastRideTss}</span></span>
                  )}
                  {lastRide.average_heartrate && (
                    <span>Avg HR: <span className="text-text">{Math.round(lastRide.average_heartrate)}</span></span>
                  )}
                  {lastRide.average_watts && (
                    <span>Avg Power: <span className="text-text">{Math.round(lastRide.average_watts)}W</span></span>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted">No rides yet.</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
