"""Public API for the Humour Hub extension."""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import json
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile
from python_multipart.exceptions import MultipartParseError

import ai
from config import settings
import quota
from validation import (
    ALLOWED_LANGUAGES,
    ALLOWED_TONES,
    InputError,
    MAX_UPLOAD_BYTES,
    normalize_image,
    validate_option,
    validate_text,
)


app = FastAPI(title="Humour Hub API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_origin_regex=r"chrome-extension://[a-p]{32}",
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

_trends_cache: tuple[float, dict] | None = None
_trends_lock = asyncio.Lock()


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
    return _error(400, "invalid_request", "Check the request fields and try again.")


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    return _error(exc.status_code, "invalid_request", str(exc.detail))


def _client_ip(request: Request) -> str:
    if settings.trust_proxy_headers:
        # Render's Cloudflare edge overwrites this header. X-Forwarded-For can
        # contain client-supplied entries, so it is deliberately ignored.
        connecting_ip = request.headers.get("cf-connecting-ip", "")
        try:
            return str(ipaddress.ip_address(connecting_ip))
        except ValueError:
            pass
    return request.client.host if request.client else "unknown"


async def _bounded_body(request: Request, limit: int) -> bytes:
    length = request.headers.get("content-length")
    if length:
        try:
            if int(length) > limit:
                raise InputError("Request is too large.")
        except ValueError:
            raise InputError("Invalid content length.") from None
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            raise InputError("Request is too large.")
        chunks.append(chunk)
    return b"".join(chunks)


async def _input(request: Request) -> tuple[str, str, str, str, bytes | None]:
    content_type = request.headers.get("content-type", "").lower()
    if content_type.startswith("application/json"):
        try:
            data = json.loads(await _bounded_body(request, 16 * 1024))
        except (ValueError, UnicodeDecodeError):
            raise InputError("Invalid JSON request.") from None
        if not isinstance(data, dict):
            raise InputError("Request must be a JSON object.")
        image = None
    elif content_type.startswith("multipart/form-data"):
        request._body = await _bounded_body(request, MAX_UPLOAD_BYTES + 65536)
        try:
            form = await request.form()
        except (HTTPException, MultipartParseError):
            raise InputError("Malformed multipart request.") from None
        data = dict(form)
        uploaded = data.get("file")
        if uploaded is not None and not isinstance(uploaded, UploadFile):
            raise InputError("File must be an image upload.")
        image = None
        if uploaded is not None:
            try:
                content = await uploaded.read(MAX_UPLOAD_BYTES + 1)
            finally:
                await uploaded.close()
            image = normalize_image(content)
    else:
        raise InputError("Send JSON text or a multipart image upload.")
    text = validate_text(data.get("text", ""), required=image is None)
    language = validate_option(data.get("language"), ALLOWED_LANGUAGES, "language", "english")
    language = {"en": "english", "hi": "hindi"}.get(language, language)
    tone = validate_option(data.get("tone"), ALLOWED_TONES, "tone", "general")
    topic = validate_text(data.get("topic", ""))
    return text, language, tone, topic, image


async def _reserve(request: Request, *, legacy: bool = False) -> dict[str, Any]:
    if not settings.ai_configured:
        raise ai.AIUnavailable()
    if legacy:
        identity = "legacy:" + hashlib.sha256(_client_ip(request).encode()).hexdigest()
    else:
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer "):
            raise quota.InvalidSession()
        identity = quota.verify_session(settings, authorization.removeprefix("Bearer ").strip())
    return await quota.reserve_call(settings, identity, _client_ip(request))


async def _perform(request: Request, task: str, *, legacy: bool = False, supplied_text: str | None = None) -> dict | JSONResponse:
    try:
        if supplied_text is None:
            text, language, tone, topic, image = await _input(request)
        else:
            text = validate_text(supplied_text, required=True)
            language, tone, topic, image = "english", "student", "", None
        allowed = await _reserve(request, legacy=legacy)
        if task == "explain":
            return {"explanation": await ai.explain(settings, text, language, image), "quota": allowed}
        variations = await ai.remix(settings, text, language, tone, topic, image)
        return {"variations": variations, "quota": allowed}
    except InputError as exc:
        return _error(400, "invalid_input", str(exc))
    except quota.InvalidSession:
        return _error(401, "invalid_session", "Start a new session and try again.")
    except quota.QuotaExceeded as exc:
        return _error(429, "quota_exceeded", f"Daily {exc.scope} AI limit reached. Try again after 00:00 UTC.")
    except quota.QuotaUnavailable:
        return _error(503, "quota_unavailable", "AI is temporarily unavailable. Local editing still works.")
    except ai.AIUnavailable:
        return _error(503, "ai_unavailable", "AI is not available right now. Local editing still works.")
    except ai.AIProviderError:
        return _error(502, "provider_error", "The AI provider could not complete this request. Try again later.")


@app.get("/")
async def root() -> dict:
    return {"message": "Humour Hub API", "version": "1.0.0"}


@app.get("/api/v1/status")
async def status() -> dict:
    quota_available = await quota.is_available(settings)
    return {
        "status": "ok",
        "ai_available": settings.ai_configured and quota_available,
        "quota_available": quota_available,
        "quota_reset_at": quota.reset_at().isoformat(),
    }


@app.post("/api/v1/session")
async def session(request: Request) -> Any:
    try:
        token = quota.create_session(settings)
        identity = quota.verify_session(settings, token)
        remaining = await quota.remaining_quota(settings, identity, _client_ip(request))
        return {"token": token, "quota": remaining}
    except quota.QuotaUnavailable:
        return _error(503, "quota_unavailable", "AI is temporarily unavailable. Local editing still works.")


@app.post("/api/v1/explain")
async def explain(request: Request) -> Any:
    return await _perform(request, "explain")


@app.post("/api/v1/remix")
async def remix(request: Request) -> Any:
    return await _perform(request, "remix")


@app.get("/api/v1/trends")
async def trends() -> dict:
    global _trends_cache
    from trends import get_trends
    if _trends_cache and time.monotonic() - _trends_cache[0] < 60:
        return _trends_cache[1]
    async with _trends_lock:
        if _trends_cache and time.monotonic() - _trends_cache[0] < 60:
            return _trends_cache[1]
        result = await asyncio.to_thread(get_trends)
        _trends_cache = (time.monotonic(), result)
        return result


@app.get("/explain")
async def legacy_explain(request: Request, meme: str = Query(...)) -> Any:
    return await _perform(request, "explain", legacy=True, supplied_text=meme)


@app.get("/remix")
async def legacy_remix(request: Request, meme: str = Query(...)) -> Any:
    result = await _perform(request, "remix", legacy=True, supplied_text=meme)
    if isinstance(result, dict):
        return {**result, "remix": "\n".join(result["variations"])}
    return result


@app.post("/explain_image")
async def legacy_explain_image(request: Request) -> Any:
    return await _perform(request, "explain", legacy=True)


@app.post("/remix_image")
async def legacy_remix_image(request: Request) -> Any:
    result = await _perform(request, "remix", legacy=True)
    if isinstance(result, dict):
        return {**result, "remix": "\n".join(result["variations"])}
    return result


@app.get("/trending")
async def legacy_trending() -> dict:
    return await trends()
