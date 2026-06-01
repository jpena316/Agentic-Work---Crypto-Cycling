# Cycling Coach — Pipeline

A full-stack AI coaching system that fetches live Strava data, runs four specialized agents, and delivers a performance analysis, 7-day training plan, and ranked bike recommendations through both an MCP interface and a FastAPI backend.

---

## Architecture Overview

```
React UI (Vite)
    │
    ▼
FastAPI  ──port 8001──  api/main.py
    │
    ▼
CyclingCoachOrchestrator  (orchestrator/orchestrator.py)
    │
    ├── Agent 1: DataRetrievalAgent      (no LLM — Strava API + Python)
    ├── Agent 2: PerformanceAnalysisAgent (Claude Sonnet)
    ├── Agent 3: TrainingPlanAgent        (Claude Sonnet)
    └── Agent 4: BikeRecommenderAgent    (Claude Sonnet + scraper)
                │
                ▼
          Shared context dict  ──►  Final coaching report
```

The same four-agent pipeline is also reachable through the **MCP server** (`server/main.py`), which exposes it as three callable tools for Claude Desktop or Claude Code.

---

## MCP Server

| Item | Value |
|------|-------|
| Entry point | `server/main.py` |
| Server name | `cycling-coach` |
| Transport | stdio |
| CLI command | `cycling-mcp` |

### MCP Tools

| Tool Name | Description |
|-----------|-------------|
| `run_coaching_session` | Triggers the full four-agent pipeline. Accepts `athlete_goals` and `bikes_under_consideration`. Takes 2–3 minutes. |
| `get_ride_summary` | Lightweight Strava data check — returns ride counts, total distance, elevation, and average duration without invoking any agents. |
| `get_bike_profiles` | Returns spec profiles for all eight bikes from `data/bikes/` (uses hardcoded fallback specs if JSON files are empty). |

Tool implementations live in `server/tools/coaching_tools.py`.

---

## Four-Agent Pipeline

Each agent receives the shared `context` dict, writes its outputs to designated keys, and passes the enriched dict to the next agent. Failures are isolated: a critical Agent 1 failure aborts early; failures in Agents 2–4 degrade to a partial report rather than halting execution.

### Agent 1 — Data Retrieval

| Item | Value |
|------|-------|
| File | `agents/data_retrieval.py` |
| Class | `DataRetrievalAgent` |
| LLM calls | None — pure Python and Strava API |
| External API | Strava (via `tools/strava_client.py`) |

Fetches the athlete profile and up to 45 days of activity history, filters to cycling rides (`Ride`, `VirtualRide`), then computes:

- Total rides, distance, elevation
- Average ride duration and longest ride
- Weekly TSS and 4-week TSS (using FTP from profile, or estimated at 95% of best 20-min power)
- Fitness trend via 4-week TSS trajectory (`improving` / `maintaining` / `declining`)

**Writes to context:** `athlete_profile`, `raw_activities`, `computed_metrics`

---

### Agent 2 — Performance Analysis

| Item | Value |
|------|-------|
| File | `agents/performance.py` |
| Class | `PerformanceAnalysisAgent` |
| LLM | Claude Sonnet 4.6 (`claude-sonnet-4-6`, `max_tokens=1500`) |
| Prompt | `prompts/performance_analysis.txt` |

Reads `computed_metrics`, `athlete_profile`, and `athlete_goals` from context, builds a structured prompt, and calls Claude with a system instruction to respond in JSON only. Validates that the response contains all required keys before storing it.

**Required response keys:** `strengths`, `weaknesses`, `fatigue_level`, `overtraining_risk`, `fitness_trend`, `key_observations`, `recommended_focus`

**Writes to context:** `performance_analysis`

---

### Agent 3 — Training Plan

| Item | Value |
|------|-------|
| File | `agents/training_plan.py` |
| Class | `TrainingPlanAgent` |
| LLM | Claude Sonnet (`claude-sonnet-4-20250514`, `max_tokens=2000`) |
| Prompt | `prompts/training_plan.txt` |

Reads `performance_analysis`, `computed_metrics`, `athlete_profile`, and `athlete_goals`. Calls Claude to produce a complete 7-day training plan as a validated JSON object, then runs structural validation via `tools/validators.py`.

**Required response keys:** `week_focus`, `tss_target`, `days` (7-element array), `coaching_notes`

**Per-day required keys:** `day`, `workout_type`, `duration_mins`, `intensity`, `description`, `rationale`

**Writes to context:** `training_plan`

---

### Agent 4 — Bike Recommender

| Item | Value |
|------|-------|
| File | `agents/bike_recommender.py` |
| Class | `BikeRecommenderAgent` |
| LLM | Claude Sonnet 4.6 (`claude-sonnet-4-6`, `max_tokens=4000`) |
| Prompt | `prompts/bike_recommendation.txt` |
| Spec source | `data/bikes/*.json` → Playwright scraper → hardcoded fallback |

Loads bike specs from JSON files (scraping live product pages if files are empty), infers a **rider signature** from all prior context keys, then calls Claude to rank all eight bikes by fit to that signature.

**Rider signature fields:** `dominant_terrain`, `riding_style`, `fitness_level`, `goals`, `training_focus`, `ftp`, `weight_kg`, `avg_ride_duration_mins`, `rides_per_week`, `elevation_per_km`, `weekly_tss`, `fitness_trend`

**Required response keys:** `ranked`, `match_scores`, `rationale`, `best_overall`, `summary`

**Writes to context:** `bike_profiles`, `rider_signature`, `bike_recommendations`

---

## Orchestrator

| Item | Value |
|------|-------|
| File | `orchestrator/orchestrator.py` |
| Class | `CyclingCoachOrchestrator` |
| Context factory | `orchestrator/context.py` → `create_context()` |

Runs all four agents sequentially, logs timing per agent, catches unhandled exceptions without crashing the pipeline, then assembles the final report with status `"success"` / `"partial"` / `"failed"` based on which outputs were produced.

---

## Shared Context Object

Defined and initialized in `orchestrator/context.py`. Every agent reads from and writes to this single dict.

```python
{
    # Agent 1 outputs
    "athlete_profile":      None,   # AthleteProfile dict from Strava
    "raw_activities":       [],     # All activities (unfiltered)
    "computed_metrics":     None,   # Aggregated training stats

    # Agent 2 outputs
    "performance_analysis": None,   # LLM-generated structured analysis
    "rider_signature":      None,   # Riding style classification

    # Agent 3 outputs
    "training_plan":        None,   # 7-day structured plan dict

    # Agent 4 outputs
    "bike_profiles":        [],     # Loaded/scraped spec dicts
    "bike_recommendations": None,   # Ranked recommendations + scores

    # Inputs (set once, read-only for agents)
    "athlete_goals":              [...],
    "bikes_under_consideration":  [...],

    # System
    "errors":   [],   # Error strings appended by any agent
    "metadata": {
        "run_id":    "<uuid>",
        "created_at": "<iso-timestamp>",
    },
}
```

---

## Bikes Under Evaluation

Eight bikes with hardcoded fallback specs in `agents/bike_recommender.py`:

| Key | Name | Category | Price (USD) | Weight |
|-----|------|----------|-------------|--------|
| `trek_madone_slr7_gen8` | Trek Madone SLR 7 Gen 8 | Aero road | $7,499 | 7.1 kg |
| `cervelo_caledonia` | Cervélo Caledonia 5 | Endurance road | $6,499 | 7.8 kg |
| `cervelo_soloist` | Cervélo Soloist | Aero road | $6,999 | 7.3 kg |
| `specialized_tarmac_sl8` | Specialized Tarmac SL8 Expert | All-around road | $5,750 | 6.9 kg |
| `canyon_aeroad_cf_slx8` | Canyon Aeroad CF SLX 8 AXS Speed | Aero road | $5,499 | 7.5 kg |
| `canyon_endurace_cf_slx8` | Canyon Endurace CF SLX 8 Di2 | Endurance road | $4,999 | 7.9 kg |
| `canyon_endurace_cf_slx7` | Canyon Endurace CF SLX 7 AXS | Endurance road | $3,999 | 8.2 kg |
| `factor_monza` | Factor Monza Shimano Ultegra | Aero road | $5,299 | 7.2 kg |

Bike specs are loaded from `data/bikes/{key}.json`. Empty files trigger a Playwright scrape of the manufacturer's product page; if scraping fails, the hardcoded fallback spec is used.

---

## FastAPI Endpoints

Base URL: `http://localhost:8001`  |  Entry point: `api/main.py`

| Method | Path | File | Description | Cache TTL |
|--------|------|------|-------------|-----------|
| `GET` | `/health` | `api/main.py` | Service health check | — |
| `GET` | `/rides/summary` | `api/routers/rides.py` | Lightweight Strava summary — ride count, distance, elevation, avg duration (`?days=1–365`) | 5 min |
| `GET` | `/rides/activities` | `api/routers/rides.py` | Full raw activity list from Strava (`?days=1–365`) | 5 min |
| `POST` | `/analysis/run` | `api/routers/analysis.py` | Trigger the full four-agent pipeline. Body: `{ athlete_goals, bikes }`. Stores result in session for subsequent GET calls. Expect 2–3 min. | none |
| `GET` | `/plan/current` | `api/routers/plan.py` | Returns the 7-day training plan from the most recent `/analysis/run`. Returns 404 if no run has completed. | in-memory |
| `GET` | `/bikes/profiles` | `api/routers/bikes.py` | Spec profiles for all eight bikes | 24 h |
| `GET` | `/bikes/recommendations` | `api/routers/bikes.py` | Ranked bike recommendations from the most recent run. Returns 404 if no run has completed. | in-memory |

The session store (`api/services/session.py`) holds the last completed report in memory. It is cleared on server restart.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| MCP framework | `mcp[cli]` ≥ 1.0 |
| LLM | Anthropic SDK — `claude-sonnet-4-6` / `claude-sonnet-4-20250514` |
| Strava integration | `stravalib` ≥ 1.5 |
| Bike spec scraping | Playwright + BeautifulSoup4 |
| HTTP client | `httpx` (async) |
| API framework | FastAPI + uvicorn |
| Data processing | `pandas`, `numpy` |
| Data validation | Pydantic v2 |
| Language / runtime | Python ≥ 3.12 |
| Frontend | React + Vite (port 5173) |
| Package manager | `hatch` / `pyproject.toml` |

---

## Project Structure

```
cycling-coach/
├── orchestrator/
│   ├── orchestrator.py          # CyclingCoachOrchestrator — runs all 4 agents
│   └── context.py               # create_context() — shared state factory
├── agents/
│   ├── base_agent.py            # Abstract BaseAgent (run, _add_error)
│   ├── data_retrieval.py        # Agent 1 — Strava fetch + TSS metrics
│   ├── performance.py           # Agent 2 — Claude performance analysis
│   ├── training_plan.py         # Agent 3 — Claude 7-day training plan
│   └── bike_recommender.py      # Agent 4 — Claude bike ranking
├── server/
│   ├── main.py                  # MCP server — 3 tools
│   └── tools/coaching_tools.py  # MCP tool implementations + schemas
├── api/
│   ├── main.py                  # FastAPI app — port 8001
│   ├── routers/
│   │   ├── rides.py             # GET /rides/summary, /rides/activities
│   │   ├── analysis.py          # POST /analysis/run
│   │   ├── plan.py              # GET /plan/current
│   │   └── bikes.py             # GET /bikes/profiles, /bikes/recommendations
│   └── services/
│       ├── cache.py             # In-process TTL cache
│       └── session.py           # In-memory session store for last report
├── tools/
│   ├── strava_client.py         # Strava API wrapper
│   ├── metrics.py               # calculate_tss, classify_fitness_trend
│   ├── scraper.py               # Playwright bike spec scraper
│   └── validators.py            # Training plan structural validation
├── data/
│   └── bikes/                   # Per-bike JSON spec files (8 files)
└── prompts/
    ├── performance_analysis.txt  # Prompt template for Agent 2
    ├── training_plan.txt         # Prompt template for Agent 3
    └── bike_recommendation.txt   # Prompt template for Agent 4
```
