import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import market, analysis, sentiment, brief


app = FastAPI(
    title="Crypto Research Agent API",
    description="FastAPI backend connecting the React UI to the MCP server tools",
    version="0.1.0",
)

# CORS — allows the React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(market.router)
app.include_router(analysis.router)
app.include_router(sentiment.router)
app.include_router(brief.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "crypto-research-agent-api"}


def main():
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()