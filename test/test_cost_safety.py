import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

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
    def test_paid_dadata_endpoints_have_rate_limit_rules(self) -> None:
        for endpoint in (api.api_address, api.api_full_address, api.suggest_address):
            with self.subTest(endpoint=endpoint.__name__):
                route_name = f"{endpoint.__module__}.{endpoint.__name__}"
                self.assertTrue(
                    limiter._route_limits.get(route_name),
                    f"{endpoint.__name__} is missing a SlowAPI rate limit",
                )


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
