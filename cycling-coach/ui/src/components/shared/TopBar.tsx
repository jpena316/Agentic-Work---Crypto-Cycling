import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Activity } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { healthCheck } from "@/api";

const TABS = [
  { path: "/overview", label: "Overview" },
  { path: "/today", label: "Today" },
  { path: "/bikes", label: "Bikes" },
];

// No auth system exists in this app (single-user, local dev tool) — initials
// are a static placeholder rather than pulled from a real identity provider.
const RIDER_INITIALS = "JP";

export function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [apiOnline, setApiOnline] = useState(false);

  useEffect(() => {
    healthCheck().then(setApiOnline);
  }, []);

  const activeTab = TABS.find((t) => t.path === location.pathname)?.path ?? "/overview";

  return (
    <header className="flex items-center justify-between gap-4 px-6 h-16 border-b border-border bg-surface">
      <div className="flex items-center gap-3 shrink-0">
        <Activity className="h-5 w-5 text-accent" strokeWidth={2.5} />
        <span className="font-heading font-bold text-base tracking-tight text-text">
          Cycling Coach
        </span>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => navigate(v)}>
        <TabsList>
          {TABS.map((tab) => (
            <TabsTrigger key={tab.path} value={tab.path}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <div className="flex items-center gap-3 shrink-0">
        <Badge variant={apiOnline ? "positive" : "destructive"} className="hidden sm:inline-flex">
          <span
            className={
              "h-1.5 w-1.5 rounded-full " + (apiOnline ? "bg-positive" : "bg-negative")
            }
          />
          {apiOnline ? "Strava Connected" : "API Offline"}
        </Badge>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/15 text-xs font-semibold text-accent font-heading">
          {RIDER_INITIALS}
        </div>
      </div>
    </header>
  );
}
