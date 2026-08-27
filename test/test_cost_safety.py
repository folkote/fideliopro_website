import re
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

from app.routers import api
from app.rate_limit import limiter
from app.services.dadata import DaDataService
from app.services.geolocation import GeolocationService


class _OpenSession:
    closed = False


class CostSafeHealthChecksTest(unittest.IsolatedAsyncioTestCase):
    async def test_dadata_health_check_never_calls_paid_cleaner(self) -> None:
        service = DaDataService()
        service.session = _OpenSession()
        service.clean_address = AsyncMock(side_effect=AssertionError("paid Cleaner call"))

        self.assertTrue(await service.health_check())
        service.clean_address.assert_not_awaited()

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

        for key in ("DADATA_TOKEN", "DADATA_SECRET"):
            with self.subTest(key=key):
                self.assertNotRegex(values.get(key, ""), re.compile(r"^[0-9a-f]{32,}$"))
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
