import unittest
from ipaddress import ip_address, ip_network
from pathlib import Path
from unittest.mock import AsyncMock, patch

from starlette.requests import Request

from app import rate_limit
from app.routers import api
from app.rate_limit import limiter
from app.config import settings
from app.services.dadata import DaDataService
from app.services.geolocation import GeolocationService


class _OpenSession:
    closed = False


class CostSafeHealthChecksTest(unittest.IsolatedAsyncioTestCase):
    async def test_dadata_health_check_never_calls_paid_cleaner(self) -> None:
        service = DaDataService()
        service.session = _OpenSession()
        service.clean_address = AsyncMock(side_effect=AssertionError("paid Cleaner call"))

        with (
            patch.object(settings, "dadata_token", "test-token"),
            patch.object(settings, "dadata_secret", "test-secret"),
        ):
            self.assertTrue(await service.health_check())
        service.clean_address.assert_not_awaited()

    async def test_dadata_health_check_requires_credentials_and_open_session(self) -> None:
        service = DaDataService()
        with (
            patch.object(settings, "dadata_token", ""),
            patch.object(settings, "dadata_secret", ""),
        ):
            self.assertFalse(await service.health_check())

        with (
            patch.object(settings, "dadata_token", "test-token"),
            patch.object(settings, "dadata_secret", "test-secret"),
        ):
            self.assertFalse(await service.health_check())
            service.session = type("ClosedSession", (), {"closed": True})()
            self.assertFalse(await service.health_check())

    async def test_geolocation_health_check_never_calls_external_lookup(self) -> None:
        service = GeolocationService()
        service.session = _OpenSession()
        service.get_location = AsyncMock(side_effect=AssertionError("external lookup"))

        self.assertTrue(await service.health_check())
        service.get_location.assert_not_awaited()


class PaidEndpointRateLimitTest(unittest.TestCase):
    @staticmethod
    def _request(peer: str, forwarded_for: str | list[str] | None = None) -> Request:
        headers = []
        if forwarded_for is not None:
            values = [forwarded_for] if isinstance(forwarded_for, str) else forwarded_for
            headers.extend((b"x-forwarded-for", value.encode("ascii")) for value in values)
        return Request(
            {
                "type": "http",
                "method": "GET",
                "scheme": "http",
                "path": "/apiaddress/api",
                "raw_path": b"/apiaddress/api",
                "query_string": b"",
                "headers": headers,
                "client": (peer, 12345),
                "server": ("testserver", 80),
            }
        )

    def test_paid_dadata_endpoints_have_rate_limit_rules(self) -> None:
        for endpoint in (api.api_address, api.api_full_address, api.suggest_address):
            with self.subTest(endpoint=endpoint.__name__):
                route_name = f"{endpoint.__module__}.{endpoint.__name__}"
                self.assertTrue(
                    limiter._route_limits.get(route_name),
                    f"{endpoint.__name__} is missing a SlowAPI rate limit",
                )

    def test_trusted_proxy_uses_distinct_forwarded_client_ips(self) -> None:
        trusted = (ip_network("10.0.0.25/32"),)
        first = rate_limit.rate_limit_client_ip(
            self._request("10.0.0.25", "198.51.100.10"), trusted
        )
        second = rate_limit.rate_limit_client_ip(
            self._request("10.0.0.25", "198.51.100.11"), trusted
        )

        self.assertEqual(first, "198.51.100.10")
        self.assertEqual(second, "198.51.100.11")
        self.assertNotEqual(first, second)

    def test_untrusted_peer_cannot_spoof_forwarded_client_ip(self) -> None:
        trusted = (ip_network("10.0.0.25/32"),)
        key = rate_limit.rate_limit_client_ip(
            self._request("203.0.113.20", "198.51.100.99"), trusted
        )

        self.assertEqual(key, "203.0.113.20")

    def test_forwarded_chain_ignores_spoofed_leftmost_value(self) -> None:
        trusted = (ip_network("10.0.0.25/32"),)
        key = rate_limit.rate_limit_client_ip(
            self._request("10.0.0.25", "192.0.2.66, 198.51.100.15"), trusted
        )

        self.assertEqual(key, "198.51.100.15")

    def test_docker_gateway_is_not_a_trusted_proxy(self) -> None:
        gateway = ip_address("172.19.0.1")
        self.assertFalse(
            any(gateway in network for network in rate_limit.TRUSTED_PROXY_NETWORKS)
        )

        first = rate_limit.rate_limit_client_ip(
            self._request("172.19.0.1", "198.51.100.10")
        )
        second = rate_limit.rate_limit_client_ip(
            self._request("172.19.0.1", "198.51.100.11")
        )
        self.assertEqual(first, "172.19.0.1")
        self.assertEqual(second, "172.19.0.1")

    def test_duplicate_forwarded_for_headers_fail_closed_to_peer(self) -> None:
        trusted = (ip_network("10.0.0.25/32"),)
        key = rate_limit.rate_limit_client_ip(
            self._request(
                "10.0.0.25",
                ["198.51.100.10", "198.51.100.11"],
            ),
            trusted,
        )

        self.assertEqual(key, "10.0.0.25")


class ExampleEnvironmentSafetyTest(unittest.TestCase):
    def test_example_environment_contains_no_credential_shaped_values(self) -> None:
        values = {}
        for line in Path(".env.example").read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key] = value

        self.assertEqual(values.get("DADATA_TOKEN"), "replace_with_dadata_token")
        self.assertEqual(values.get("DADATA_SECRET"), "replace_with_dadata_secret")
        self.assertIn("user:password@", values.get("DATABASE_URL", ""))

    def test_docker_build_context_excludes_environment_files(self) -> None:
        dockerignore = Path(".dockerignore")
        self.assertTrue(dockerignore.is_file(), ".dockerignore is required")
        ignored = {
            line.strip()
            for line in dockerignore.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertIn(".env", ignored)
        self.assertIn(".env.*", ignored)
        self.assertIn("!.env.example", ignored)


if __name__ == "__main__":
    unittest.main()
