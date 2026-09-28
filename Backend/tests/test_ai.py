import asyncio
import base64
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ai
from config import Settings


SETTINGS = Settings(cloudflare_account_id="account", cloudflare_api_token="server-only-token")


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_vision_request_uses_documented_image_shape(self):
        captured = {}

        def handler(request):
            captured["url"] = str(request.url)
            captured["authorization"] = request.headers["Authorization"]
            captured["payload"] = json.loads(request.content)
            return httpx.Response(200, json={"success": True, "result": {"response": "A joke about contrast."}})

        real_client = httpx.AsyncClient
        transport = httpx.MockTransport(handler)
        with patch.object(ai.httpx, "AsyncClient", side_effect=lambda **kwargs: real_client(transport=transport)):
            output = await ai.explain(SETTINGS, "", "english", b"jpeg-bytes")
        self.assertEqual(output, "A joke about contrast.")
        self.assertIn("/@cf/meta/llama-3.2-11b-vision-instruct", captured["url"])
        self.assertEqual(captured["authorization"], "Bearer server-only-token")
        self.assertEqual(captured["payload"]["image"], "data:image/jpeg;base64," + base64.b64encode(b"jpeg-bytes").decode())
        self.assertEqual(captured["payload"]["messages"][0]["role"], "system")

    async def test_provider_error_has_no_upstream_body(self):
        real_client = httpx.AsyncClient
        transport = httpx.MockTransport(lambda _: httpx.Response(429, json={"error": "provider details"}))
        with patch.object(ai.httpx, "AsyncClient", side_effect=lambda **kwargs: real_client(transport=transport)):
            with self.assertRaises(ai.AIProviderError):
                await ai.explain(SETTINGS, "hello", "english", None)

    async def test_remix_parses_three_captions(self):
        with patch.object(ai, "_run", return_value='```json\n["one", "two", "three"]\n```'):
            self.assertEqual(await ai.remix(SETTINGS, "source", "hindi", "work", "office", None), ["one", "two", "three"])


if __name__ == "__main__":
    unittest.main()
