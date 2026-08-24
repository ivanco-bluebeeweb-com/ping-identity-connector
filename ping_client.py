"""Thin PingOne Platform API + Auth API REST client.

Auth model: OAuth2 client-credentials with a Worker Application's client_id +
client_secret, scoped to one environment_id. Base URLs are region-specific.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

_REGION_HOSTS = {
    "NA": ("auth.pingone.com", "api.pingone.com"),
    "EU": ("auth.pingone.eu", "api.pingone.eu"),
    "AP": ("auth.pingone.asia", "api.pingone.asia"),
    "CA": ("auth.pingone.ca", "api.pingone.ca"),
}


class PingError(RuntimeError):
    """A safe provider-facing error; never includes credentials."""

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class PingClient:
    """REST client for the PingOne Platform API, scoped to one environment."""

    def __init__(
        self,
        environment_id: str,
        client_id: str,
        client_secret: str,
        region: str = "NA",
        *,
        timeout: float = 30.0,
    ):
        env_id = (environment_id or "").strip()
        if not env_id:
            raise PingError("Environment ID is required.")
        if not client_id or not client_secret:
            raise PingError("Worker Client ID and Client Secret are required.")
        region_key = (region or "NA").strip().upper()
        if region_key not in _REGION_HOSTS:
            raise PingError(f"Unknown region '{region}'. Use one of: NA, EU, AP, CA.")
        self.environment_id = env_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region_key
        auth_host, api_host = _REGION_HOSTS[region_key]
        self.auth_url = f"https://{auth_host}/{env_id}/as/token"
        self.base_url = f"https://{api_host}/v1/environments/{env_id}"
        self.timeout = timeout
        self._access_token = ""
        self._token_expiry = 0.0

    async def _ensure_token(self) -> str:
        if self._access_token and time.time() < self._token_expiry - 30:
            return self._access_token
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(
                    self.auth_url,
                    data={"grant_type": "client_credentials"},
                    auth=(self.client_id, self.client_secret),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            except httpx.HTTPError as exc:
                raise PingError(f"Could not reach PingOne auth endpoint: {exc}", retryable=True) from exc
        if resp.status_code == 401:
            raise PingError("Invalid Worker Client ID or Client Secret.")
        if resp.status_code >= 400:
            raise PingError(f"PingOne auth failed ({resp.status_code}): {resp.text[:300]}")
        data = resp.json()
        self._access_token = data.get("access_token", "")
        self._token_expiry = time.time() + float(data.get("expires_in", 3600))
        if not self._access_token:
            raise PingError("PingOne auth response did not include an access token.")
        return self._access_token

    async def request(self, method: str, path: str, params: dict | None = None, json_body: dict | None = None) -> tuple[Any, dict]:
        token = await self._ensure_token()
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.request(method, url, params=params, json=json_body, headers=headers)
            except httpx.HTTPError as exc:
                raise PingError(f"Could not reach PingOne: {exc}", retryable=True) from exc
        if resp.status_code == 401:
            raise PingError("Authentication failed -- credentials may be invalid or revoked.")
        if resp.status_code == 403:
            raise PingError("Forbidden -- the Worker Application may be missing a required role (e.g. Identity Data Admin).")
        if resp.status_code == 404:
            raise PingError("Not found.")
        if resp.status_code == 429:
            raise PingError("Rate limited by PingOne. Try again shortly.", retryable=True)
        if resp.status_code >= 500:
            raise PingError(f"PingOne server error ({resp.status_code}).", retryable=True)
        if resp.status_code >= 400:
            raise PingError(f"PingOne request failed ({resp.status_code}): {resp.text[:300]}")
        if resp.status_code == 204 or not resp.content:
            return None, dict(resp.headers)
        return resp.json(), dict(resp.headers)

    async def verify_connection(self) -> dict:
        """Cheap call used by connect_ping to prove the environment+credentials actually work."""
        data, _ = await self.request("GET", "")
        return data or {}
