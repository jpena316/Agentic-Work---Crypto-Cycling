#!/usr/bin/env python3
"""One-time Strava OAuth2 authorization flow.

Run this script once to exchange an authorization code for a valid access
token and refresh token, then write them to .env automatically.

Usage:
    python tools/strava_auth.py
"""

import json
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

_ENV_PATH = Path(__file__).parent.parent / ".env"
_REDIRECT_URI = "http://localhost:8000/callback"
_AUTH_BASE = "https://www.strava.com/oauth/authorize"
_TOKEN_URL = "https://www.strava.com/oauth/token"
_PORT = 8000


# ---------------------------------------------------------------------------
# .env helpers (stdlib-only — no python-dotenv)
# ---------------------------------------------------------------------------

def _read_env() -> dict[str, str]:
    """Parse .env into a plain dict, skipping comments and blank lines."""
    env: dict[str, str] = {}
    if not _ENV_PATH.exists():
        return env
    for raw in _ENV_PATH.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def _write_tokens_to_env(
    access_token: str,
    refresh_token: str,
    expires_at: int,
) -> None:
    """Upsert the three token fields in .env, preserving every other line."""
    updates = {
        "STRAVA_ACCESS_TOKEN": access_token,
        "STRAVA_REFRESH_TOKEN": refresh_token,
        "STRAVA_TOKEN_EXPIRES_AT": str(expires_at),
    }

    existing_lines = _ENV_PATH.read_text().splitlines() if _ENV_PATH.exists() else []
    new_lines: list[str] = []
    seen: set[str] = set()

    for line in existing_lines:
        key = line.split("=", 1)[0].strip()
        if key in updates:
            new_lines.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            new_lines.append(line)

    # Append any keys that weren't already in the file
    for key, value in updates.items():
        if key not in seen:
            new_lines.append(f"{key}={value}")

    _ENV_PATH.write_text("\n".join(new_lines) + "\n")


# ---------------------------------------------------------------------------
# Local callback server
# ---------------------------------------------------------------------------

class _CallbackHandler(BaseHTTPRequestHandler):
    """Handles exactly one GET request — the OAuth2 redirect from Strava."""

    # Shared state written by the handler, read by main()
    auth_code: str | None = None
    auth_error: str | None = None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)

        # Only handle /callback; ignore favicon etc.
        if not parsed.path.startswith("/callback"):
            self._respond(404, "Not found.")
            return

        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            _CallbackHandler.auth_code = params["code"][0]
            self._respond(
                200,
                "Authorization successful! You can close this tab and return to the terminal.",
            )
        elif "error" in params:
            _CallbackHandler.auth_error = params["error"][0]
            self._respond(
                400,
                f"Authorization failed: {_CallbackHandler.auth_error}. Return to the terminal.",
            )
        else:
            self._respond(400, "Unexpected callback — no code or error parameter.")

        # Shut the server down from a daemon thread so do_GET can return first
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def _respond(self, status: int, message: str) -> None:
        body = (
            f"<html><body style='font-family:sans-serif;padding:2rem'>"
            f"<h2>{message}</h2></body></html>"
        ).encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        # Suppress the default access-log noise
        pass


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the full one-time authorization flow."""

    # --- Step 1: load credentials ---
    print("\n[1/5] Reading credentials from .env ...")
    env = _read_env()
    client_id = env.get("STRAVA_CLIENT_ID", "").strip()
    client_secret = env.get("STRAVA_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        print("ERROR: STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in .env")
        raise SystemExit(1)

    print(f"      Client ID: {client_id}")

    # --- Step 2: build authorization URL ---
    print("[2/5] Building authorization URL ...")
    query = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": _REDIRECT_URI,
            "response_type": "code",
            "approval_prompt": "force",   # always prompt so scope is confirmed
            "scope": "activity:read_all",
        }
    )
    auth_url = f"{_AUTH_BASE}?{query}"

    print(f"\n      If your browser doesn't open automatically, visit:\n")
    print(f"      {auth_url}\n")

    # --- Step 3: start local server, then open browser ---
    print("[3/5] Starting local callback server on port 8000 ...")
    server = HTTPServer(("127.0.0.1", _PORT), _CallbackHandler)

    print("      Opening browser ...")
    webbrowser.open(auth_url)

    print("      Waiting for Strava to redirect to http://localhost:8000/callback ...")
    print("      (Authorize the app in your browser, then return here.)\n")

    # serve_forever() blocks until the handler calls server.shutdown()
    server.serve_forever()

    # --- Step 4: check what the handler captured ---
    if _CallbackHandler.auth_error:
        print(f"ERROR: Authorization denied by Strava — {_CallbackHandler.auth_error}")
        raise SystemExit(1)

    code = _CallbackHandler.auth_code
    if not code:
        print("ERROR: Callback received but contained no authorization code.")
        raise SystemExit(1)

    print("[4/5] Authorization code received. Exchanging for tokens ...")

    # --- Step 5: exchange code for tokens ---
    payload = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
    ).encode()

    req = urllib.request.Request(
        _TOKEN_URL,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            token_data: dict = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        print(f"ERROR: Token exchange failed (HTTP {exc.code}): {body}")
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print(f"ERROR: Network error during token exchange: {exc.reason}")
        raise SystemExit(1)

    access_token: str = token_data["access_token"]
    refresh_token: str = token_data["refresh_token"]
    expires_at: int = token_data["expires_at"]

    print("\n      Tokens received:")
    print(f"        access_token  : {access_token}")
    print(f"        refresh_token : {refresh_token}")
    print(f"        expires_at    : {expires_at}")

    # --- Step 6: persist to .env ---
    print(f"\n[5/5] Writing tokens to {_ENV_PATH} ...")
    _write_tokens_to_env(access_token, refresh_token, expires_at)
    print("      Done!\n")
    print("Your Strava client is authorized. You can now run the coaching agent.\n")


if __name__ == "__main__":
    main()
