"""Strava OAuth2 client with automatic token refresh and typed responses."""

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).parent.parent / ".env"
_STRAVA_API = "https://www.strava.com/api/v3"
_TOKEN_URL = "https://www.strava.com/oauth/token"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class StravaSettings(BaseSettings):
    """Loads Strava credentials from the .env file."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    strava_client_id: str
    strava_client_secret: str
    strava_access_token: str
    strava_refresh_token: str
    strava_token_expires_at: int = Field(default=0)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class AthleteProfile(BaseModel):
    """Simplified athlete profile returned by the Strava API."""

    id: int
    firstname: str
    lastname: str
    ftp: int | None = None
    weight: float | None = None


class Activity(BaseModel):
    """A single Strava activity with the fields relevant to training analysis."""

    id: int
    name: str
    type: str
    distance: float
    moving_time: int
    total_elevation_gain: float
    average_watts: float | None = None
    average_heartrate: float | None = None
    suffer_score: int | None = None
    start_date: str


class ActivityStream(BaseModel):
    """Time-series data for a single activity (power and HR)."""

    time: list[int]
    watts: list[int | None] | None = None
    heartrate: list[int | None] | None = None


# ---------------------------------------------------------------------------
# Token persistence helpers
# ---------------------------------------------------------------------------

def _write_token_to_env(access_token: str, refresh_token: str, expires_at: int) -> None:
    """Overwrite the token fields in .env so the refresh survives restarts."""
    if not _ENV_PATH.exists():
        return

    lines = _ENV_PATH.read_text().splitlines()
    updates = {
        "STRAVA_ACCESS_TOKEN": access_token,
        "STRAVA_REFRESH_TOKEN": refresh_token,
        "STRAVA_TOKEN_EXPIRES_AT": str(expires_at),
    }

    new_lines: list[str] = []
    seen: set[str] = set()

    for line in lines:
        key = line.split("=", 1)[0].strip()
        if key in updates:
            new_lines.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            new_lines.append(line)

    for key, value in updates.items():
        if key not in seen:
            new_lines.append(f"{key}={value}")

    _ENV_PATH.write_text("\n".join(new_lines) + "\n")


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class StravaClient:
    """Async Strava API client with automatic OAuth2 token refresh."""

    def __init__(self) -> None:
        self._settings = StravaSettings()
        self._access_token = self._settings.strava_access_token
        self._refresh_token = self._settings.strava_refresh_token
        self._expires_at = self._settings.strava_token_expires_at

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _is_token_expired(self) -> bool:
        """Return True if the access token has expired or expires within 60 s."""
        return int(time.time()) >= self._expires_at - 60

    async def _refresh_access_token(self) -> None:
        """Exchange the refresh token for a new access token and persist it."""
        payload = {
            "client_id": self._settings.strava_client_id,
            "client_secret": self._settings.strava_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(_TOKEN_URL, data=payload)

        if response.status_code != 200:
            raise RuntimeError(
                f"Token refresh failed ({response.status_code}): {response.text}"
            )

        data = response.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._expires_at = data["expires_at"]
        _write_token_to_env(self._access_token, self._refresh_token, self._expires_at)

    async def _auth_headers(self) -> dict[str, str]:
        """Return Authorization headers, refreshing the token first if needed."""
        if self._is_token_expired():
            await self._refresh_access_token()
        return {"Authorization": f"Bearer {self._access_token}"}

    # ------------------------------------------------------------------
    # Internal request helper
    # ------------------------------------------------------------------

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Issue an authenticated GET request and return parsed JSON."""
        headers = await self._auth_headers()
        url = f"{_STRAVA_API}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params or {})

        if response.status_code == 401:
            raise PermissionError(
                "Strava returned 401. Check that your credentials are valid."
            )
        if response.status_code == 429:
            raise RuntimeError(
                "Strava rate limit exceeded. Try again in a few minutes."
            )
        if not response.is_success:
            raise RuntimeError(
                f"Strava API error {response.status_code} for {path}: {response.text}"
            )
        return response.json()

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    async def get_athlete(self) -> AthleteProfile:
        """Fetch the authenticated athlete's profile.

        Returns:
            AthleteProfile with id, name, ftp, and weight fields.
        """
        data = await self._get("/athlete")
        return AthleteProfile(
            id=data["id"],
            firstname=data.get("firstname", ""),
            lastname=data.get("lastname", ""),
            ftp=data.get("ftp"),
            weight=data.get("weight"),
        )

    async def get_activities(self, days: int = 30) -> list[Activity]:
        """Fetch recent activities within the last *days* days.

        Args:
            days: How many days back to look. Defaults to 30.

        Returns:
            List of Activity objects ordered newest-first.
        """
        after = int(time.time()) - days * 86_400
        page = 1
        activities: list[Activity] = []

        while True:
            batch: list[dict[str, Any]] = await self._get(
                "/athlete/activities",
                params={"after": after, "per_page": 100, "page": page},
            )
            if not batch:
                break

            for raw in batch:
                activities.append(
                    Activity(
                        id=raw["id"],
                        name=raw.get("name", ""),
                        type=raw.get("type", ""),
                        distance=raw.get("distance", 0.0),
                        moving_time=raw.get("moving_time", 0),
                        total_elevation_gain=raw.get("total_elevation_gain", 0.0),
                        average_watts=raw.get("average_watts"),
                        average_heartrate=raw.get("average_heartrate"),
                        suffer_score=raw.get("suffer_score"),
                        start_date=raw.get("start_date", ""),
                    )
                )
            page += 1

        return activities

    async def get_activity_streams(self, activity_id: int) -> ActivityStream:
        """Fetch per-second power and heart-rate streams for a single activity.

        Args:
            activity_id: Strava activity ID.

        Returns:
            ActivityStream containing aligned time, watts, and heartrate lists.
        """
        keys = "time,watts,heartrate"
        data: dict[str, Any] = await self._get(
            f"/activities/{activity_id}/streams",
            params={"keys": keys, "key_by_type": "true"},
        )

        time_data: list[int] = data.get("time", {}).get("data", [])
        watts_data: list[int | None] | None = (
            data["watts"]["data"] if "watts" in data else None
        )
        hr_data: list[int | None] | None = (
            data["heartrate"]["data"] if "heartrate" in data else None
        )

        return ActivityStream(
            time=time_data,
            watts=watts_data,
            heartrate=hr_data,
        )
