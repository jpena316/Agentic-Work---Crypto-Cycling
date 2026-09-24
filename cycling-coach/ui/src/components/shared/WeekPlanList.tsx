import type { TrainingDay } from "@/api";
import { Card } from "./Card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface WeekPlanListProps {
  days: TrainingDay[];
  todayName: string;
}

const INTENSITY_VARIANT: Record<string, "positive" | "default" | "destructive" | "secondary"> = {
  rest: "secondary",
  easy: "positive",
  recovery: "positive",
  moderate: "default",
  tempo: "default",
  threshold: "destructive",
  hard: "destructive",
  vo2max: "destructive",
};

export function WeekPlanList({ days, todayName }: WeekPlanListProps) {
  return (
    <Card>
      <h2 className="font-heading text-sm font-semibold text-text mb-3">This Week</h2>
      <div className="flex flex-col gap-1.5">
        {days.map((day) => {
          const isToday = day.day.toLowerCase() === todayName.toLowerCase();
          const variant = INTENSITY_VARIANT[day.intensity?.toLowerCase()] ?? "secondary";
          return (
            <div
              key={day.day}
              className={cn(
                "flex items-center justify-between gap-3 rounded-md px-3 py-2.5 border-l-2",
                isToday ? "bg-accent/10 border-l-accent" : "border-l-transparent"
              )}
            >
              <div className="flex items-center gap-3 min-w-0">
                <span
                  className={cn(
                    "text-sm font-medium w-24 shrink-0",
                    isToday ? "text-accent" : "text-text"
                  )}
                >
                  {day.day}
                </span>
                <span className="text-sm text-muted truncate">{day.workout_type}</span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs text-muted">
                  {day.duration_mins > 0 ? `${day.duration_mins} min` : "Off"}
                </span>
                <Badge variant={variant} className="capitalize">
                  {day.intensity}
                </Badge>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
