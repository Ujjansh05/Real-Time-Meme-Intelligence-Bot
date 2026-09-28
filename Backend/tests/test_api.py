import asyncio
from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as api
from config import Settings
import quota


TEST_SETTINGS = Settings(
    cloudflare_account_id="example-account",
    cloudflare_api_token="example-token",
    upstash_url="https://example.upstash.io",
    upstash_token="example-redis-token",
    session_secret="test-signing-key",
)


class APITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.settings_patch = patch.object(api, "settings", TEST_SETTINGS)
        self.settings_patch.start()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app), base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose()
        self.settings_patch.stop()

    async def test_session_and_explain_contract(self):
        with patch.object(api.quota, "remaining_quota", new_callable=AsyncMock, return_value={"remaining": 5, "reset_at": "tomorrow"}):
            response = await self.client.post("/api/v1/session")
        self.assertEqual(response.status_code, 200)
        token = response.json()["token"]
        self.assertTrue(quota.verify_session(TEST_SETTINGS, token))
        with patch.object(api.quota, "reserve_call", new_callable=AsyncMock, return_value={"remaining": 4, "reset_at": "tomorrow"}) as reserve, patch.object(api.ai, "explain", new_callable=AsyncMock, return_value="A joke about exams.") as explain:
            response = await self.client.post("/api/v1/explain", headers={"Authorization": f"Bearer {token}"}, json={"text": "exam meme", "language": "hi"})
        self.assertEqual(response.json(), {"explanation": "A joke about exams.", "quota": {"remaining": 4, "reset_at": "tomorrow"}})
        self.assertEqual(reserve.await_count, 1)
        self.assertEqual(explain.await_args.args[2], "hindi")

    async def test_invalid_input_does_not_use_quota(self):
        token = quota.create_session(TEST_SETTINGS)
        with patch.object(api.quota, "reserve_call", new_callable=AsyncMock) as reserve:
            response = await self.client.post("/api/v1/explain", headers={"Authorization": f"Bearer {token}"}, json={"text": "x" * 4001})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_input")
        reserve.assert_not_awaited()

    async def test_large_json_body_is_rejected_before_quota(self):
        token = quota.create_session(TEST_SETTINGS)
        with patch.object(api.quota, "reserve_call", new_callable=AsyncMock) as reserve:
            response = await self.client.post(
                "/api/v1/explain",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                content=b'{"text":"' + b"a" * (16 * 1024) + b'"}',
            )
        self.assertEqual(response.status_code, 400)
        reserve.assert_not_awaited()

    async def test_bad_multipart_is_structured_error(self):
        response = await self.client.post(
            "/api/v1/explain",
            headers={"Content-Type": "multipart/form-data; boundary=broken"},
            content=b"garbage",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_input")

    async def test_image_upload_is_normalized(self):
        source = BytesIO()
        Image.new("RGB", (32, 16), (255, 0, 0)).save(source, format="PNG")
        token = quota.create_session(TEST_SETTINGS)
        with patch.object(api.quota, "reserve_call", new_callable=AsyncMock, return_value={"remaining": 4, "reset_at": "tomorrow"}), patch.object(api.ai, "explain", new_callable=AsyncMock, return_value="red") as explain:
            response = await self.client.post("/api/v1/explain", headers={"Authorization": f"Bearer {token}"}, files={"file": ("meme.png", source.getvalue(), "image/png")})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(explain.await_args.args[3].startswith(b"\xff\xd8"))

    async def test_missing_session_and_quota_outage(self):
        response = await self.client.post("/api/v1/explain", json={"text": "hi"})
        self.assertEqual(response.status_code, 401)
        token = quota.create_session(TEST_SETTINGS)
        with patch.object(api.quota, "reserve_call", new_callable=AsyncMock, side_effect=quota.QuotaUnavailable):
            response = await self.client.post("/api/v1/explain", headers={"Authorization": f"Bearer {token}"}, json={"text": "hi"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "quota_unavailable")

    async def test_legacy_remix_preserves_old_field_and_uses_quota(self):
        with patch.object(api.quota, "reserve_call", new_callable=AsyncMock, return_value={"remaining": 3, "reset_at": "tomorrow"}) as reserve, patch.object(api.ai, "remix", new_callable=AsyncMock, return_value=["one", "two", "three"]):
            response = await self.client.get("/remix", params={"meme": "old meme"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["remix"], "one\ntwo\nthree")
        self.assertEqual(len(response.json()["variations"]), 3)
        self.assertEqual(reserve.await_count, 1)

    async def test_trends_route_delegates_to_collector(self):
        response = await self.client.get("/api/v1/trends")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["sources"]), 3)


if __name__ == "__main__":
    unittest.main()
