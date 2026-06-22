"""Import legacy file cache entries into the PostgreSQL cache backend.

Usage:
    Minimal initialization::

        DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db python scripts/import_file_cache_to_postgres.py --dry-run

    Minimal happy-path call::

        python scripts/import_file_cache_to_postgres.py

    Common error-handling case::

        if DATABASE_URL is missing, the script exits with a clear error before importing.

The database access pattern follows SQLAlchemy 2.0 async examples from Context7:
`create_async_engine`, `engine.begin()`, `conn.execute(text(...))`,
`async_sessionmaker.begin()`, and PostgreSQL `insert(...).on_conflict_do_update(...)`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

# Allow running this file directly from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings  # noqa: E402
from app.services.cache import cache_service  # noqa: E402


@dataclass(frozen=True)
class CacheEntry:
    namespace: str
    cache_key: str
    value: Any
    source: str


class ImportStats:
    def __init__(self) -> None:
        self.counts = Counter(
            {
                "read": 0,
                "inserted": 0,
                "updated": 0,
                "skipped": 0,
                "errors": 0,
            }
        )

    def inc(self, key: str, amount: int = 1) -> None:
        self.counts[key] += amount

    def print_summary(self) -> None:
        print("Import summary:")
        for key in ("read", "inserted", "updated", "skipped", "errors"):
            print(f"  {key}: {self.counts[key]}")


def load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def unwrap_legacy_value(data: Any) -> Any:
    if isinstance(data, dict) and "value" in data:
        return data["value"]
    return data


def normalize_geolocation_key(key: str) -> str:
    return key.removeprefix("geolocation_")


def iter_mapping_cache(path: Path, namespace: str) -> Iterable[CacheEntry]:
    data = load_json_file(path)
    if not isinstance(data, dict):
        yield CacheEntry(namespace, path.stem, unwrap_legacy_value(data), str(path))
        return

    for key, value in data.items():
        yield CacheEntry(namespace, str(key), unwrap_legacy_value(value), str(path))


def iter_geolocation_jsonl(path: Path) -> Iterable[CacheEntry]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            data = json.loads(line)
            if not isinstance(data, dict) or "key" not in data:
                raise ValueError(f"{path}:{line_number} is missing key")
            yield CacheEntry(
                "geolocation",
                normalize_geolocation_key(str(data["key"])),
                unwrap_legacy_value(data),
                f"{path}:{line_number}",
            )


def iter_geolocation_json(path: Path) -> Iterable[CacheEntry]:
    data = load_json_file(path)
    cache_key = normalize_geolocation_key(path.stem)
    yield CacheEntry("geolocation", cache_key, unwrap_legacy_value(data), str(path))


def discover_entries(paths: list[Path], stats: ImportStats) -> list[CacheEntry]:
    entries: list[CacheEntry] = []
    seen_files: set[Path] = set()

    for cache_dir in paths:
        if not cache_dir.exists():
            continue
        for filename, namespace in (
            ("address_cache.json", "dadata_street_fias"),
            ("fulladdress_cache.json", "dadata_cleaned_address"),
        ):
            path = cache_dir / filename
            if path.exists() and path not in seen_files:
                seen_files.add(path)
                try:
                    file_entries = list(iter_mapping_cache(path, namespace))
                    entries.extend(file_entries)
                    stats.inc("read", len(file_entries))
                except Exception as exc:  # noqa: BLE001
                    stats.inc("errors")
                    print(f"ERROR reading {path}: {exc}")

        jsonl_path = cache_dir / "geolocation_cache.jsonl"
        if jsonl_path.exists() and jsonl_path not in seen_files:
            seen_files.add(jsonl_path)
            try:
                file_entries = list(iter_geolocation_jsonl(jsonl_path))
                entries.extend(file_entries)
                stats.inc("read", len(file_entries))
            except Exception as exc:  # noqa: BLE001
                stats.inc("errors")
                print(f"ERROR reading {jsonl_path}: {exc}")

        for path in sorted(cache_dir.glob("geolocation_*.json")):
            if path in seen_files:
                continue
            seen_files.add(path)
            try:
                file_entries = list(iter_geolocation_json(path))
                entries.extend(file_entries)
                stats.inc("read", len(file_entries))
            except Exception as exc:  # noqa: BLE001
                stats.inc("errors")
                print(f"ERROR reading {path}: {exc}")

    return entries


async def import_entries(entries: list[CacheEntry], dry_run: bool, stats: ImportStats) -> None:
    if dry_run:
        stats.inc("skipped", len(entries))
        return

    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required to import cache into PostgreSQL")

    await cache_service.initialize()
    try:
        for entry in entries:
            existing = await cache_service.get(entry.cache_key, namespace=entry.namespace)
            ok = await cache_service.set(
                entry.cache_key,
                entry.value,
                namespace=entry.namespace,
                source=entry.source,
            )
            if ok:
                stats.inc("updated" if existing is not None else "inserted")
            else:
                stats.inc("errors")
    finally:
        await cache_service.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read legacy cache files and print a summary without writing to PostgreSQL.",
    )
    parser.add_argument(
        "--cache-dir",
        action="append",
        type=Path,
        default=None,
        help="Legacy cache directory to read. Can be repeated. Defaults to cache/ and data/cache/.",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    stats = ImportStats()
    cache_dirs = args.cache_dir or [Path("cache"), Path("data/cache")]
    entries = discover_entries(cache_dirs, stats)

    try:
        await import_entries(entries, args.dry_run, stats)
    except Exception as exc:  # noqa: BLE001
        stats.inc("errors")
        print(f"ERROR importing entries: {exc}")
        stats.print_summary()
        return 1

    stats.print_summary()
    return 0 if stats.counts["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
