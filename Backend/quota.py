"""Anonymous sessions with Upstash quotas or single-process local quotas."""

import asyncio
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import secrets

import httpx

from config import Settings


class QuotaUnavailable(Exception):
    pass


class QuotaExceeded(Exception):
    def __init__(self, scope: str):
        super().__init__(scope)
        self.scope = scope


class InvalidSession(Exception):
    pass


_memory_lock = asyncio.Lock()
_memory_counts: dict[str, int] = {}
_memory_day = ""


def reset_at() -> datetime:
    now = datetime.now(timezone.utc)
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


def _signature(settings: Settings, payload: str) -> str:
    digest = hmac.new(settings.session_secret.encode(), payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def create_session(settings: Settings) -> str:
    if not settings.quota_configured:
        raise QuotaUnavailable()
    identity = secrets.token_urlsafe(24)
    expiry = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
    payload = f"{identity}.{expiry}"
    return f"{payload}.{_signature(settings, payload)}"


def verify_session(settings: Settings, token: str) -> str:
    if not settings.quota_configured:
        raise QuotaUnavailable()
    try:
        identity, expiry_text, supplied_signature = token.split(".")
        expiry = int(expiry_text)
        payload = f"{identity}.{expiry_text}"
        if not identity or expiry < datetime.now(timezone.utc).timestamp():
            raise ValueError()
        if not hmac.compare_digest(_signature(settings, payload), supplied_signature):
            raise ValueError()
        return identity
    except (ValueError, AttributeError):
        raise InvalidSession() from None


def _keys(settings: Settings, identity: str, ip: str, day: str) -> list[str]:
    # Keyed hashes avoid storing either identifier and prevent easy IP reversal.
    session_hash = hmac.new(settings.session_secret.encode(), identity.encode(), hashlib.sha256).hexdigest()
    ip_hash = hmac.new(settings.session_secret.encode(), ip.encode(), hashlib.sha256).hexdigest()
    return [f"quota:{day}:session:{session_hash}", f"quota:{day}:ip:{ip_hash}", f"quota:{day}:global"]


async def _command(settings: Settings, command: list) -> object:
    if not settings.quota_configured:
        raise QuotaUnavailable()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                settings.upstash_url.rstrip("/"),
                headers={"Authorization": f"Bearer {settings.upstash_token}"},
                json=command,
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict) or "error" in body or "result" not in body:
                raise QuotaUnavailable()
            return body["result"]
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise QuotaUnavailable() from exc


async def is_available(settings: Settings) -> bool:
    if settings.quota_backend == "memory":
        return settings.quota_configured
    try:
        return await _command(settings, ["PING"]) == "PONG"
    except QuotaUnavailable:
        return False


async def remaining_quota(settings: Settings, identity: str, ip: str) -> dict:
    if settings.quota_backend == "memory":
        if not settings.quota_configured:
            raise QuotaUnavailable()
        async with _memory_lock:
            day = datetime.now(timezone.utc).strftime("%Y%m%d")
            counts = _memory_values(settings, identity, ip, day)
            limits = (settings.session_daily_limit, settings.ip_daily_limit, settings.global_daily_limit)
            return {"remaining": max(0, min(limit - count for limit, count in zip(limits, counts))), "reset_at": reset_at().isoformat()}
    counts = await _command(settings, ["MGET", *_keys(settings, identity, ip, datetime.now(timezone.utc).strftime("%Y%m%d"))])
    try:
        if not isinstance(counts, list) or len(counts) != 3:
            raise ValueError()
        balances = [limit - int(count or 0) for limit, count in zip((settings.session_daily_limit, settings.ip_daily_limit, settings.global_daily_limit), counts)]
        return {"remaining": max(0, min(balances)), "reset_at": reset_at().isoformat()}
    except (ValueError, TypeError) as exc:
        raise QuotaUnavailable() from exc


def _memory_values(settings: Settings, identity: str, ip: str, day: str) -> list[int]:
    global _memory_day
    if day != _memory_day:
        _memory_counts.clear()
        _memory_day = day
    return [_memory_counts.get(key, 0) for key in _keys(settings, identity, ip, day)]


LUA_RESERVE = """
local limits = {tonumber(ARGV[1]), tonumber(ARGV[2]), tonumber(ARGV[3])}
for i = 1, 3 do
  local n = tonumber(redis.call('GET', KEYS[i]) or '0')
  if n >= limits[i] then return {0, i, limits[1] - tonumber(redis.call('GET', KEYS[1]) or '0')} end
end
local ttl = tonumber(ARGV[4])
for i = 1, 3 do
  redis.call('INCR', KEYS[i])
  redis.call('EXPIRE', KEYS[i], ttl)
end
return {1, 0, limits[1] - tonumber(redis.call('GET', KEYS[1]))}
"""


async def reserve_call(settings: Settings, identity: str, ip: str) -> dict:
    if not settings.quota_configured:
        raise QuotaUnavailable()
    if settings.quota_backend == "memory":
        async with _memory_lock:
            day = datetime.now(timezone.utc).strftime("%Y%m%d")
            counts = _memory_values(settings, identity, ip, day)
            limits = (settings.session_daily_limit, settings.ip_daily_limit, settings.global_daily_limit)
            for count, limit, scope in zip(counts, limits, ("installation", "network", "service")):
                if count >= limit:
                    raise QuotaExceeded(scope)
            for key in _keys(settings, identity, ip, day):
                _memory_counts[key] = _memory_counts.get(key, 0) + 1
            return {"remaining": settings.session_daily_limit - counts[0] - 1, "reset_at": reset_at().isoformat()}
    now = datetime.now(timezone.utc)
    reset = reset_at()
    day = now.strftime("%Y%m%d")
    ttl = max(1, int((reset - now).total_seconds()) + 60)
    keys = _keys(settings, identity, ip, day)
    command = ["EVAL", LUA_RESERVE, 3, *keys, settings.session_daily_limit, settings.ip_daily_limit, settings.global_daily_limit, ttl]
    try:
        accepted, scope, remaining = await _command(settings, command)
        if not accepted:
            raise QuotaExceeded({1: "installation", 2: "network", 3: "service"}.get(int(scope), "service"))
        return {"remaining": int(remaining), "reset_at": reset.isoformat()}
    except QuotaExceeded:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError) as exc:
        raise QuotaUnavailable() from exc
