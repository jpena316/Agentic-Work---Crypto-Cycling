import type { HeatmapCell } from "@/lib/metrics";
import { cn } from "@/lib/utils";

interface ContributionHeatmapProps {
  cells: HeatmapCell[];
}

const LEVEL_CLASS: Record<HeatmapCell["level"], string> = {
  0: "bg-border",
  1: "bg-accent/25",
  2: "bg-accent/50",
  3: "bg-accent/75",
  4: "bg-accent",
};

function formatDate(dateStr: string) {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function ContributionHeatmap({ cells }: ContributionHeatmapProps) {
  // Pad the front so the grid starts on a Sunday, GitHub-style.
  const firstDay = cells.length ? new Date(cells[0].date + "T00:00:00").getDay() : 0;
  const padding: null[] = Array.from({ length: firstDay }, () => null);
  const padded: (HeatmapCell | null)[] = [...padding, ...cells];

  return (
    <div className="flex flex-col gap-2">
      <div className="overflow-x-auto">
        <div
          className="grid gap-1 w-fit"
          style={{ gridTemplateRows: "repeat(7, 0.75rem)", gridAutoFlow: "column", gridAutoColumns: "0.75rem" }}
        >
          {padded.map((cell, i) =>
            cell ? (
              <div
                key={i}
                title={`${formatDate(cell.date)} · ${cell.tss.toFixed(0)} TSS (est.)`}
                className={cn("h-3 w-3 rounded-sm", LEVEL_CLASS[cell.level])}
              />
            ) : (
              <div key={i} className="h-3 w-3" />
            )
          )}
        </div>
      </div>
      <div className="flex items-center gap-1.5 text-xs text-muted">
        <span>Less</span>
        {([0, 1, 2, 3, 4] as const).map((lvl) => (
          <div key={lvl} className={cn("h-3 w-3 rounded-sm", LEVEL_CLASS[lvl])} />
        ))}
        <span>More</span>
        <span className="ml-2">· estimated daily training load (TSS)</span>
      </div>
    </div>
  );
}
