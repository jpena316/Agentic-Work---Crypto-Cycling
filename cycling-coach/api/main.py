"""FastAPI application entry point for the Cycling Coach API."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import analysis, bikes, plan, rides

app = FastAPI(
    title="Cycling Coach API",
    description="FastAPI backend connecting the React UI to the cycling coach agents",
    version="0.1.0",
)

# CORS — allows the React frontend (Vite dev server) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rides.router)
app.include_router(analysis.router)
app.include_router(plan.router)
app.include_router(bikes.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "cycling-coach-api"}


def main() -> None:
    uvicorn.run("api.main:app", host="0.0.0.0", port=8001, reload=True)


if __name__ == "__main__":
    main()
