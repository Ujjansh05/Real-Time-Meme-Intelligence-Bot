"""Observed meme-interest feeds stored in Upstash Redis.

``get_trends()`` is the synchronous, JSON-serializable API used by FastAPI.
The scheduled collector calls ``collect_all()``. No generated claims enter this feed.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any


USER_AGENT = "HumourHubTrends/2.0 (https://github.com/Ujjansh05/Real-Time-Meme-Intelligence-Bot)"
SOURCES = {"wikipedia": "Wikipedia interest", "reddit": "Reddit", "bluesky": "Bluesky"}
SOCIAL_MAX_AGE = timedelta(hours=48)
WIKIPEDIA_MAX_AGE = timedelta(hours=48)
WIKI_ARTICLES = (
    "Internet_meme", "Doge_(meme)", "Distracted_boyfriend", "Drakeposting",
    "Rickrolling", "This_Is_Fine", "Woman_yelling_at_a_cat", "Pepe_the_Frog",
)
ADULT_LABELS = {"porn", "sexual", "nudity", "graphic-media", "nsfl"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _json_request(url: str, *, method: str = "GET", data: bytes | None = None,
                  headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(url, data=data, method=method,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


class TrendStore:
    """Small Redis REST adapter; each write uses one atomic Redis SET command."""

    def __init__(self, url: str | None = None, token: str | None = None):
        self.url = (url or os.getenv("UPSTASH_REDIS_REST_URL") or "").rstrip("/")
        self.token = token or os.getenv("UPSTASH_REDIS_REST_TOKEN") or ""
        if not self.url.startswith("https://") or not self.token:
            raise ValueError("Upstash Redis REST credentials are required")

    def command(self, *parts: Any) -> Any:
        response = _json_request(self.url, method="POST",
            data=json.dumps(parts, separators=(",", ":")).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        if "error" in response:
            raise RuntimeError("Trend storage command failed")
        return response.get("result")

    def get_json(self, key: str) -> dict[str, Any] | None:
        raw = self.command("GET", key)
        if raw is None:
            return None
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("Invalid trend snapshot")
        return value

    def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        self.command("SET", key, json.dumps(value, ensure_ascii=False, separators=(",", ":")),
                     "EX", ttl_seconds)


def _key(source: str, suffix: str) -> str:
    return f"humourhub:trends:v1:{source}:{suffix}"


def _safe_title(text: Any) -> str:
    return " ".join(str(text or "").split())[:220]


def _social_rank(source: str, current: list[dict[str, Any]],
                 previous: dict[str, Any] | None, observed_at: str) -> list[dict[str, Any]]:
    if not previous:
        return []
    earlier = {item["id"]: item for item in previous.get("items", []) if "id" in item}
    ranked = []
    for item in current:
        old = earlier.get(item["id"])
        if old is None:
            continue
        growth = max(0, item["engagement"] - old.get("engagement", 0))
        if growth <= 0:
            continue
        ranked.append({"title": item["title"], "url": item["url"], "source": source,
                       "score": growth, "score_label": "engagement gained", "observed_at": observed_at})
    return sorted(ranked, key=lambda item: (-item["score"], item["title"]))[:10]


def collect_wikipedia() -> tuple[list[dict[str, Any]], int]:
    """Compare yesterday's article views with the seven previous complete days."""
    yesterday = (_now() - timedelta(days=1)).date()
    start = (yesterday - timedelta(days=7)).strftime("%Y%m%d")
    end = yesterday.strftime("%Y%m%d")
    items = []
    fetched = 0
    complete = 0
    for article in WIKI_ARTICLES:
        encoded = urllib.parse.quote(article, safe="()_")
        url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
               f"en.wikipedia.org/all-access/all-agents/{encoded}/daily/{start}/{end}")
        try:
            points = _json_request(url).get("items", [])
        except (urllib.error.URLError, ValueError):
            continue
        fetched += 1
        by_day = {point["timestamp"][:8]: point["views"] for point in points
                  if isinstance(point.get("views"), int)}
        dates = [(yesterday - timedelta(days=offset)).strftime("%Y%m%d") for offset in range(8)]
        if any(day not in by_day for day in dates):
            continue
        complete += 1
        baseline = sum(by_day[day] for day in dates[1:]) / 7
        score = round((by_day[dates[0]] - baseline) / max(1, baseline), 3)
        if score <= 0:
            continue
        title = article.replace("_", " ")
        items.append({"title": title, "url": f"https://en.wikipedia.org/wiki/{encoded}",
                      "source": "wikipedia", "score": score,
                      "score_label": "readership growth vs prior 7 days",
                      "views": by_day[dates[0]], "observed_at": _iso(_now())})
    items.sort(key=lambda item: (-item["score"], item["title"]))
    if fetched == 0:
        raise urllib.error.URLError("No Wikipedia pageview series available")
    return items[:10], complete


def _reddit_token() -> str:
    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    user_agent = os.getenv("REDDIT_USER_AGENT", "")
    if os.getenv("REDDIT_API_APPROVED", "").lower() != "true" or not all((client_id, secret, user_agent)):
        raise ValueError("Approved Reddit API access is not configured")
    basic = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    payload = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    response = _json_request("https://www.reddit.com/api/v1/access_token", method="POST", data=payload,
        headers={"Authorization": f"Basic {basic}", "User-Agent": user_agent,
                 "Content-Type": "application/x-www-form-urlencoded"})
    return response["access_token"]


def collect_reddit() -> list[dict[str, Any]]:
    token = _reddit_token()
    agent = os.getenv("REDDIT_USER_AGENT", USER_AGENT)
    communities = [name.strip() for name in (os.getenv("REDDIT_COMMUNITIES") or "memes,dankmemes").split(",")
                   if name.strip().replace("_", "").isalnum()][:5]
    found: dict[str, dict[str, Any]] = {}
    for community in communities:
        url = f"https://oauth.reddit.com/r/{community}/new?limit=75"
        listing = _json_request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": agent})
        for child in listing.get("data", {}).get("children", []):
            post = child.get("data", {})
            if post.get("over_18") or post.get("is_self") or post.get("removed_by_category"):
                continue
            post_id = post.get("id")
            permalink = post.get("permalink", "")
            if not post_id or not permalink.startswith("/r/"):
                continue
            found[post_id] = {"id": post_id, "title": _safe_title(post.get("title")),
                "url": f"https://www.reddit.com{permalink}",
                "engagement": max(0, int(post.get("score") or 0)) + max(0, int(post.get("num_comments") or 0))}
    return list(found.values())


def collect_bluesky() -> list[dict[str, Any]]:
    handle = os.getenv("BLUESKY_HANDLE", "")
    password = os.getenv("BLUESKY_APP_PASSWORD", "")
    if not handle or not password:
        raise ValueError("Bluesky service account is not configured")
    auth = _json_request("https://bsky.social/xrpc/com.atproto.server.createSession", method="POST",
        data=json.dumps({"identifier": handle, "password": password}).encode(),
        headers={"Content-Type": "application/json"})
    bearer = auth["accessJwt"]
    queries = [query.strip() for query in (os.getenv("BLUESKY_QUERIES") or "meme,memes").split(",")
               if query.strip()][:5]
    found: dict[str, dict[str, Any]] = {}
    for query in queries:
        url = ("https://bsky.social/xrpc/app.bsky.feed.searchPosts?" +
               urllib.parse.urlencode({"q": query, "sort": "latest", "limit": 75}))
        response = _json_request(url, headers={"Authorization": f"Bearer {bearer}"})
        for post in response.get("posts", []):
            record = post.get("record", {})
            self_labels = record.get("labels") or {}
            labels = ((post.get("labels") or []) + (post.get("author", {}).get("labels") or [])
                      + (self_labels.get("values", []) if isinstance(self_labels, dict) else []))
            if any(label.get("val") in ADULT_LABELS for label in labels):
                continue
            uri = post.get("uri", "")
            author = post.get("author", {}).get("handle", "")
            if not uri.startswith("at://") or "/app.bsky.feed.post/" not in uri or not author:
                continue
            rkey = uri.rsplit("/", 1)[-1]
            title = _safe_title(record.get("text"))
            if not title:
                continue
            found[uri] = {"id": uri, "title": title,
                "url": f"https://bsky.app/profile/{urllib.parse.quote(author)}/post/{urllib.parse.quote(rkey)}",
                "engagement": sum(max(0, int(post.get(field) or 0)) for field in
                    ("likeCount", "repostCount", "replyCount", "quoteCount"))}
    return list(found.values())


def collect_source(source: str, store: TrendStore | None = None) -> dict[str, Any]:
    """Collect one source, preserving the previous good feed on failure."""
    if source not in SOURCES:
        raise ValueError("Unknown source")
    store = store or TrendStore()
    observed_at = _iso(_now())
    try:
        if source == "wikipedia":
            ranked, comparable_articles = collect_wikipedia()
            status = "ok" if comparable_articles else "insufficient_data"
        else:
            sample = collect_reddit() if source == "reddit" else collect_bluesky()
            previous = store.get_json(_key(source, "sample"))
            ranked = _social_rank(source, sample, previous, observed_at)
            earlier_ids = {item.get("id") for item in previous.get("items", [])} if previous else set()
            status = "ok" if any(item["id"] in earlier_ids for item in sample) else "insufficient_data"
            store.set_json(_key(source, "sample"), {"observed_at": observed_at, "items": sample}, 48 * 3600)
        snapshot = {"source": source, "label": SOURCES[source], "observed_at": observed_at,
                    "status": status, "items": ranked}
        latest_ttl = 7 * 24 * 3600 if source == "wikipedia" else 48 * 3600
        store.set_json(_key(source, "latest"), snapshot, latest_ttl)
        store.command("DEL", _key(source, "error"))
        return snapshot
    except (urllib.error.URLError, KeyError, ValueError, TypeError, RuntimeError, OSError) as exc:
        # Do not put provider responses, account names, or URLs into public status.
        message = "Source access is not configured" if isinstance(exc, ValueError) else "Collection failed"
        store.set_json(_key(source, "error"), {"observed_at": observed_at, "message": message}, 7 * 24 * 3600)
        return {"source": source, "status": "unavailable", "message": message}


def collect_all(store: TrendStore | None = None) -> list[dict[str, Any]]:
    store = store or TrendStore()
    return [collect_source(source, store) for source in SOURCES]


def get_trends(store: TrendStore | None = None) -> dict[str, Any]:
    """Read a public feed; errors return explicit unavailable source states."""
    now = _now()
    try:
        store = store or TrendStore()
    except ValueError:
        store = None
    sources = []
    for source, label in SOURCES.items():
        entry: dict[str, Any] = {"source": source, "label": label, "observed_at": None,
                                 "stale": False, "status": "unavailable", "items": []}
        if store is None:
            entry["message"] = "Trend storage is not configured"
            sources.append(entry)
            continue
        try:
            latest = store.get_json(_key(source, "latest"))
            error = store.get_json(_key(source, "error"))
            if latest:
                entry.update({key: latest[key] for key in ("observed_at", "status", "items") if key in latest})
                age_limit = WIKIPEDIA_MAX_AGE if source == "wikipedia" else SOCIAL_MAX_AGE
                observed = _parse(entry["observed_at"])
                # A successful collection deletes the error key. If it exists,
                # the latest attempt failed even when clock resolution makes its
                # timestamp equal to the previous snapshot.
                stale = observed is None or now - observed > age_limit or bool(error)
                entry["stale"] = stale
                if stale:
                    entry["status"] = "stale"
            elif error:
                entry["message"] = error.get("message", "Collection failed")
            else:
                entry["message"] = "Awaiting first collection"
        except (urllib.error.URLError, ValueError, RuntimeError, OSError):
            entry["message"] = "Trend storage is unavailable"
        sources.append(entry)
    return {"generated_at": _iso(now), "sources": sources}
