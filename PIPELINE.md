# Crypto Research Agent — Pipeline

A full-stack AI research system that exposes live cryptocurrency analysis as MCP tools, consumed by a FastAPI backend and React frontend.

---

## Architecture Overview

```
React UI (Vite)
    │
    ▼
FastAPI  ──port 8000──  api/main.py
    │
    ▼  (direct Python import)
MCP Server tools
    │
    ├──► CoinGecko API  (market data, OHLCV)
    ├──► NewsAPI        (headlines & sentiment)
    └──► Anthropic API  (Claude — brief synthesis)
```

---

## MCP Server

| Item | Value |
|------|-------|
| Entry point | `server/main.py` |
| Server name | `crypto-research-agent` |
| Transport | stdio |
| CLI command | `crypto-agent` |

The server registers four tools and dispatches incoming `call_tool` requests to the corresponding handler functions.

---

## MCP Tools

| # | Tool Name | File | Role |
|---|-----------|------|------|
| 1 | `get_market_data` | `server/tools/market_data.py` | Fetches live price, market cap, 24h/7d changes, volume, circulating supply, and ATH drawdown from CoinGecko. Includes 3-attempt retry with exponential backoff for rate limits. |
| 2 | `run_technical_analysis` | `server/tools/technical.py` | Pulls 30-day OHLCV data from CoinGecko, builds a pandas DataFrame, and computes SMA-7, SMA-30, RSI-14, volume trend, price trend, and support/resistance levels. |
| 3 | `get_news_sentiment` | `server/tools/news_sentiment.py` | Queries NewsAPI for up to 50 recent headlines, scores each with a keyword-based sentiment model (positive/negative/neutral), and returns an aggregate score from −1.0 to +1.0. |
| 4 | `generate_investment_brief` | `server/tools/brief_generator.py` | Orchestrates tools 1–3, fills a prompt template from `prompts/investment_brief.txt`, and calls **Claude Sonnet** via the Anthropic SDK to synthesize a structured markdown research brief. |

---

## Claude's Two Roles

### Role 1 — MCP Host / Client

When connected via Claude Desktop or Claude Code, Claude acts as the MCP client: it reads the tool registry, decides which tools to call based on user intent, and interprets the returned JSON. All tool calls go over stdio transport.

### Role 2 — LLM Synthesizer (inside `generate_investment_brief`)

Within the `generate_investment_brief` tool, Claude is called programmatically via the Anthropic Python SDK (`claude-sonnet-4-20250514`, `max_tokens=2000`). It receives fully assembled market, technical, and sentiment data and produces a structured investment research brief in markdown.

```python
# server/tools/brief_generator.py  (simplified)
client = Anthropic(api_key=settings.anthropic_api_key)
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2000,
    messages=[{"role": "user", "content": filled_prompt}],
)
```

---

## Data Flow

```
User requests brief for "bitcoin"
        │
        ▼
generate_investment_brief(token="bitcoin", horizon="medium")
        │
        ├── get_market_data("bitcoin")        ──► CoinGecko /coins/{id}
        │       price, market cap, ATH drawdown
        │
        ├── run_technical_analysis("bitcoin") ──► CoinGecko /market_chart
        │       SMA-7, SMA-30, RSI-14, support/resistance
        │
        ├── get_news_sentiment("bitcoin")     ──► NewsAPI /everything
        │       50 headlines → sentiment score
        │
        └── Claude Sonnet (Anthropic API)
                prompt template + all three data outputs
                        │
                        ▼
                Structured markdown brief
```

---

## FastAPI Endpoints

Base URL: `http://localhost:8000`  |  Entry point: `api/main.py`

| Method | Path | File | Description | Cache TTL |
|--------|------|------|-------------|-----------|
| `GET` | `/health` | `api/main.py` | Service health check | — |
| `GET` | `/market/{token}` | `api/routers/market.py` | Live market data (price, cap, volume, changes, ATH drawdown) | 60 s |
| `GET` | `/market/{token}/history` | `api/routers/market.py` | Historical daily price series for charting (`?days=7–90`) | 5 min |
| `GET` | `/analysis/{token}` | `api/routers/analysis.py` | Technical analysis — SMA, RSI, trends, support/resistance (`?days=14–90`) | 5 min |
| `GET` | `/sentiment/{token}` | `api/routers/sentiment.py` | News sentiment score and top headlines (`?days=1–30`) | 15 min |
| `GET` | `/brief/{token}` | `api/routers/brief.py` | Full AI investment brief — market + technical + sentiment + Claude synthesis (`?horizon=short\|medium\|long`) | none |
| `WS` | `/brief/ws/{token}` | `api/routers/brief.py` | WebSocket endpoint — streams status updates then delivers completed brief | — |

The FastAPI layer uses an in-process cache (`api/services/cache.py`) keyed by token + parameters. The MCP tools are called directly as Python functions via `api/services/mcp_client.py` — no subprocess or network hop.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| MCP framework | `mcp[cli]` ≥ 1.0 |
| LLM | Anthropic SDK — `claude-sonnet-4-20250514` |
| Market data | CoinGecko REST API (free tier + optional Pro key) |
| News data | NewsAPI `/everything` endpoint |
| Technical indicators | `ta` library (SMA, RSI) + `pandas` |
| HTTP client | `httpx` (async) |
| API framework | FastAPI + uvicorn |
| Data validation | Pydantic v2 |
| Language / runtime | Python ≥ 3.12 |
| Frontend | React + Vite (port 5173) |
| Package manager | `hatch` / `pyproject.toml` |

---

## Project Structure

```
crypto-research-agent/
├── server/
│   ├── main.py                  # MCP server — tool registry & dispatcher
│   ├── config.py                # Settings (API keys, timeouts)
│   ├── models/schemas.py        # Pydantic I/O schemas for all four tools
│   └── tools/
│       ├── market_data.py       # Tool 1 — CoinGecko live data
│       ├── technical.py         # Tool 2 — OHLCV + indicators
│       ├── news_sentiment.py    # Tool 3 — NewsAPI + scoring
│       └── brief_generator.py  # Tool 4 — orchestrator + Claude call
├── api/
│   ├── main.py                  # FastAPI app — port 8000
│   ├── routers/
│   │   ├── market.py            # GET /market/{token}
│   │   ├── analysis.py          # GET /analysis/{token}
│   │   ├── sentiment.py         # GET /sentiment/{token}
│   │   └── brief.py             # GET /brief/{token}, WS /brief/ws/{token}
│   ├── services/
│   │   ├── mcp_client.py        # Thin wrapper calling MCP tool functions
│   │   └── cache.py             # In-process TTL cache
│   └── models/responses.py      # FastAPI response models
└── prompts/
    └── investment_brief.txt     # Prompt template for Claude
```
