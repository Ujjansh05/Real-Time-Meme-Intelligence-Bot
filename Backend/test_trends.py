import copy
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trends


class MemoryStore:
    def __init__(self):
        self.values = {}

    def get_json(self, key):
        return copy.deepcopy(self.values.get(key))

    def set_json(self, key, value, ttl_seconds):
        self.values[key] = copy.deepcopy(value)

    def command(self, *parts):
        if parts[0] == "DEL":
            self.values.pop(parts[1], None)


class TrendTests(unittest.TestCase):
    def test_social_needs_two_observations_and_removes_missing_posts(self):
        store = MemoryStore()
        first = [{"id": "one", "title": "A meme", "url": "https://example.org/one", "engagement": 5},
                 {"id": "deleted", "title": "Gone", "url": "https://example.org/gone", "engagement": 4}]
        second = [{"id": "one", "title": "A meme", "url": "https://example.org/one", "engagement": 12},
                  {"id": "new", "title": "New", "url": "https://example.org/new", "engagement": 100}]
        with patch.object(trends, "collect_reddit", side_effect=[first, second]):
            self.assertEqual(trends.collect_source("reddit", store)["status"], "insufficient_data")
            result = trends.collect_source("reddit", store)
        self.assertEqual(result["status"], "ok")
        self.assertEqual([item["title"] for item in result["items"]], ["A meme"])
        self.assertEqual(result["items"][0]["score"], 7)

    def test_error_preserves_feed_and_marks_it_stale(self):
        store = MemoryStore()
        with patch.object(trends, "collect_bluesky", return_value=[]):
            trends.collect_source("bluesky", store)
        with patch.object(trends, "collect_bluesky", side_effect=ValueError("secret details")):
            trends.collect_source("bluesky", store)
        feed = trends.get_trends(store)
        bluesky = next(source for source in feed["sources"] if source["source"] == "bluesky")
        self.assertTrue(bluesky["stale"])
        self.assertEqual(bluesky["status"], "stale")
        self.assertNotIn("secret details", str(feed))

    def test_social_with_no_growth_is_comparable_and_empty(self):
        store = MemoryStore()
        sample = [{"id": "one", "title": "A meme", "url": "https://example.org/one", "engagement": 5}]
        with patch.object(trends, "collect_bluesky", return_value=sample):
            trends.collect_source("bluesky", store)
            result = trends.collect_source("bluesky", store)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["items"], [])

    def test_old_snapshot_is_stale(self):
        store = MemoryStore()
        yesterday = datetime.now(timezone.utc) - timedelta(hours=49)
        store.set_json(trends._key("reddit", "latest"), {
            "source": "reddit", "status": "ok", "items": [], "observed_at": trends._iso(yesterday)
        }, 500000)
        reddit = next(source for source in trends.get_trends(store)["sources"] if source["source"] == "reddit")
        self.assertEqual(reddit["status"], "stale")

    def test_wikipedia_ranks_observed_readership_growth(self):
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)

        def fake_request(url):
            article = url.split("/daily/")[0].split("/")[-1]
            latest = 30 if article == "Internet_meme" else 10
            return {"items": [{"timestamp": (yesterday - timedelta(days=offset)).strftime("%Y%m%d00"),
                               "views": latest if offset == 0 else 10} for offset in range(8)]}

        with patch.object(trends, "_json_request", side_effect=fake_request):
            items, _ = trends.collect_wikipedia()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Internet meme")
        self.assertEqual(items[0]["score"], 2.0)


if __name__ == "__main__":
    unittest.main()
