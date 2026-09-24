import { useEffect, useRef, useState } from "react";
import { Play } from "lucide-react";
import type { BikeProfile } from "@/api";
import { Card } from "./Card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";

interface RunAnalysisPanelProps {
  onRunAnalysis: (goals: string[], bikes: string[]) => void;
  isLoading: boolean;
  elapsedSeconds: number;
  availableBikes: BikeProfile[];
}

const DEFAULT_GOALS = [
  "Build endurance for a century ride",
  "Improve climbing ability",
  "Lose weight while maintaining power",
].join("\n");

function formatElapsed(s: number) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
}

export function RunAnalysisPanel({
  onRunAnalysis,
  isLoading,
  elapsedSeconds,
  availableBikes,
}: RunAnalysisPanelProps) {
  const [goalsText, setGoalsText] = useState(DEFAULT_GOALS);
  const [selectedBikes, setSelectedBikes] = useState<Set<string>>(new Set());
  const seededRef = useRef(false);

  // availableBikes loads asynchronously (starts empty), so the default
  // selection is seeded here once bikes actually arrive rather than in
  // useState's initializer, which only runs on the very first render.
  useEffect(() => {
    if (!seededRef.current && availableBikes.length > 0) {
      seededRef.current = true;
      setSelectedBikes(new Set(availableBikes.slice(0, 4).map((b) => b.name)));
    }
  }, [availableBikes]);

  const toggleBike = (name: string) => {
    setSelectedBikes((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
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

  return (
    <Card>
      <p className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">
        Run Analysis
      </p>

      <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-4 items-start">
        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-muted">Goals (one per line)</label>
          <Textarea
            value={goalsText}
            onChange={(e) => setGoalsText(e.target.value)}
            rows={3}
            className="text-xs resize-none"
            placeholder="Enter your goals…"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-muted">Bikes to evaluate</label>
          <div className="flex flex-col gap-1.5 max-h-24 overflow-y-auto pr-1">
            {availableBikes.map((bike) => (
              <label key={bike.name} className="flex items-center gap-2 cursor-pointer">
                <Checkbox
                  checked={selectedBikes.has(bike.name)}
                  onCheckedChange={() => toggleBike(bike.name)}
                />
                <span
                  className={
                    "text-xs leading-relaxed " +
                    (selectedBikes.has(bike.name) ? "text-text" : "text-muted")
                  }
                >
                  {bike.name}
                </span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-1.5 min-w-[160px]">
          <Button
            onClick={handleRun}
            disabled={isLoading || !goalsText.trim() || selectedBikes.size === 0}
            className="gap-1.5"
          >
            <Play className="h-3.5 w-3.5" fill="currentColor" />
            {isLoading ? `Running… ${formatElapsed(elapsedSeconds)}` : "Run Analysis"}
          </Button>
          {isLoading && (
            <p className="text-xs text-muted leading-snug">
              Fetching Strava data + calling Claude. This takes 2–3 minutes.
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}
