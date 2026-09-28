from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Settings
import quota


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(upstash_url="https://example.upstash.io", upstash_token="token", session_secret="secret")

    def test_signature_and_expiry_are_checked(self):
        token = quota.create_session(self.settings)
        self.assertTrue(quota.verify_session(self.settings, token))
        with self.assertRaises(quota.InvalidSession):
            quota.verify_session(self.settings, token + "x")
        identity, _, signature = token.split(".")
        with self.assertRaises(quota.InvalidSession):
            quota.verify_session(self.settings, f"{identity}.1.{signature}")


class QuotaTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.settings = Settings(upstash_url="https://example.upstash.io", upstash_token="token", session_secret="secret")

    async def test_remaining_reflects_all_three_limits(self):
        with patch.object(quota, "_command", new_callable=AsyncMock, return_value=["1", "19", "10"]):
            result = await quota.remaining_quota(self.settings, "installation", "127.0.0.1")
        self.assertEqual(result["remaining"], 1)

    async def test_reservation_exhaustion_reports_scope(self):
        with patch.object(quota, "_command", new_callable=AsyncMock, return_value=[0, 3, 2]) as command:
            with self.assertRaises(quota.QuotaExceeded) as caught:
                await quota.reserve_call(self.settings, "installation", "127.0.0.1")
        self.assertEqual(caught.exception.scope, "service")
        self.assertEqual(command.await_args.args[1][0], "EVAL")
        self.assertEqual(command.await_args.args[1][2], 3)

    async def test_storage_outage_fails_closed(self):
        with patch.object(quota, "_command", new_callable=AsyncMock, side_effect=quota.QuotaUnavailable):
            with self.assertRaises(quota.QuotaUnavailable):
                await quota.reserve_call(self.settings, "installation", "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
