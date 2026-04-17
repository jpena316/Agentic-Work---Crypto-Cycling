# Crypto Research Agent

A production-grade AI research tool that generates structured investment briefs 
for cryptocurrencies using live market data, technical analysis, and news sentiment.

Built with Claude (Anthropic), MCP (Model Context Protocol), FastAPI, and React.

---

## Architecture
React UI (port 5173)
│  HTTP REST
▼
FastAPI Backend (port 8000)
│  Direct Python calls
▼
MCP Server Tools
│  HTTP APIs
▼
CoinGecko + NewsAPI + Anthropic Claude

### Three Layers

**MCP Server** — A Python server exposing four tools Claude can call dynamically:
- `get_market_data` — Live price, market cap, volume, ATH drawdown from CoinGecko
- `run_technical_analysis` — SMA-7, SMA-30, RSI-14, volume trend, support/resistance
- `get_news_sentiment` — News sentiment scoring across 50 recent articles via NewsAPI
- `generate_investment_brief` — Orchestrates all three tools + calls Claude to synthesize

**FastAPI Backend** — REST API gateway between the UI and MCP tools:
- Keeps API keys server-side, never exposed to the browser
- In-memory TTL caching to protect against rate limits
- WebSocket endpoint for streaming brief generation

**React Frontend** — Dashboard UI with:
- Live market snapshot cards
- 30-day interactive price chart (Recharts)
- Technical signals with color-coded badges
- News sentiment panel with clickable headlines
- Investment brief generator powered by Claude

---

## Tech Stack

| Layer | Technology |
|---|---|
| MCP Server | Python, `mcp[cli]`, `httpx`, `pandas`, `ta` |
| Data Validation | Pydantic v2 |
| Backend | FastAPI, uvicorn |
| Frontend | React, TypeScript, Tailwind CSS |
| Charts | Recharts |
| Package Manager | uv |
| External APIs | CoinGecko, NewsAPI, Anthropic Claude |

---

## Project Structure
crypto-research-agent/
├── server/                    # MCP Server
│   ├── main.py                # Server entrypoint, tool registration
│   ├── config.py              # Settings via pydantic-settings
│   ├── tools/
│   │   ├── market_data.py     # Tool 1 — CoinGecko integration
│   │   ├── technical.py       # Tool 2 — pandas TA calculations
│   │   ├── news_sentiment.py  # Tool 3 — NewsAPI + sentiment scoring
│   │   └── brief_generator.py # Tool 4 — orchestration + Claude API
│   └── models/
│       └── schemas.py         # Pydantic I/O models for all tools
├── api/                       # FastAPI Backend
│   ├── main.py                # FastAPI app, CORS, router registration
│   ├── routers/               # REST endpoints
│   ├── services/              # MCP client, caching layer
│   └── models/                # Response schemas
├── ui/                        # React Frontend
│   └── src/
│       ├── components/        # Dashboard + Brief panel components
│       ├── hooks/             # Data fetching hooks
│       └── api.ts             # Axios client + TypeScript types
└── prompts/
└── investment_brief.txt   # Structured prompt template for Claude

---

## Setup

### Prerequisites
- Python 3.12
- Node.js 18+
- uv package manager
- API keys: Anthropic, NewsAPI

### Installation

```bash
# Clone the repo
git clone https://github.com/jpena316/Agentic-Work---Crypto-Cycling
cd Agentic-Work---Crypto-Cycling/crypto-research-agent

# Install Python dependencies
uv venv --python 3.12
uv pip install -e .

# Install frontend dependencies
cd ui && npm install && cd ..
```

### Environment Variables

Create a `.env` file in `crypto-research-agent/`:

ANTHROPIC_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
COINGECKO_API_KEY=         # optional, free tier works without

### Running

Open three terminal tabs:

**Tab 1 — FastAPI Backend:**
```bash
cd crypto-research-agent
uv run python -m api.main
```

**Tab 2 — React Frontend:**
```bash
cd crypto-research-agent/ui
npm run dev
```

Open `http://localhost:5173` in your browser.

**Optional — MCP Inspector (for tool testing):**
```bash
cd crypto-research-agent
npx @modelcontextprotocol/inspector .venv/bin/python -m server.main
```

---

## How It Works

1. User selects a cryptocurrency from the dropdown
2. The React frontend calls the FastAPI backend REST endpoints
3. FastAPI calls the MCP tool functions directly
4. Tools hit CoinGecko and NewsAPI for live data
5. Data is validated through Pydantic schemas before returning
6. User clicks Generate Brief — FastAPI calls the brief generator tool
7. Brief generator calls all three data tools, injects results into a prompt template
8. Claude synthesizes the data into a structured markdown research brief
9. Brief streams back to the UI and renders in real time

---

## Supported Tokens

Bitcoin, Ethereum, Solana, Cardano, XRP, Dogecoin, Polkadot, Chainlink

Any CoinGecko coin ID can be used with the API directly.

---

## Key Design Decisions

**Why MCP?** Clean separation between Claude's reasoning and data retrieval. 
Tools are independently testable without Claude in the loop.

**Why FastAPI between UI and MCP?** API keys stay server-side. 
Caching layer protects rate limits. Single entry point for all data.

**Why direct imports in mcp_client.py?** MCP server and API backend share 
the same codebase — direct imports are more efficient than full protocol round trips.

**Why Pydantic everywhere?** Every tool input and output is typed and validated. 
Claude never sees malformed data. Errors surface at the boundary, not inside logic.