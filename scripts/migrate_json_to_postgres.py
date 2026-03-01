"""
One-time migration script: JSON file cache → PostgreSQL.

Run from project root:
    python scripts/migrate_json_to_postgres.py

Reads DATABASE_URL, CACHE_DB_SCHEMA, CACHE_DB_TABLE from .env
Migrates:
    - address_cache.json         → dadata:street_fias_id:{address}
    - fulladdress_cache.json     → dadata:cleaned_text:{address}
    - cache/dadata_address_*.json → dadata:street_fias_id:{source} + dadata:cleaned_text:{source}
    - cache/geolocation_*.json   → geolocation_{ip}

All inserts use ON CONFLICT DO NOTHING (safe to re-run).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from dotenv import dotenv_values

# ── Config ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
ENV = dotenv_values(ROOT / ".env")

DATABASE_URL: str = ENV.get("DATABASE_URL", "")
SCHEMA: str = ENV.get("CACHE_DB_SCHEMA", "fideliopro")
TABLE: str = ENV.get("CACHE_DB_TABLE", "cache_entries")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in .env", file=sys.stderr)
    sys.exit(1)

# psycopg3 uses postgresql:// (without +psycopg suffix)
CONN_STR = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")


# ── Helpers ───────────────────────────────────────────────────────────────────

def table_ref() -> str:
    return f'"{SCHEMA}"."{TABLE}"'


def ensure_schema(conn: psycopg.Connection) -> None:
    conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"')
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_ref()} (
            cache_key   TEXT PRIMARY KEY,
            cache_value JSONB NOT NULL,
            expires_at  TIMESTAMPTZ NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    conn.execute(f"""
        CREATE INDEX IF NOT EXISTS "{TABLE}_expires_at_idx"
        ON {table_ref()} (expires_at)
    """)
    conn.commit()
    print(f"Schema '{SCHEMA}' and table '{TABLE}' ready.")


def insert_batch(
    conn: psycopg.Connection,
    rows: list[tuple],
) -> tuple[int, int]:
    """Insert rows, return (inserted, skipped)."""
    inserted = 0
    skipped = 0
    for cache_key, cache_value_json, expires_at in rows:
        cur = conn.execute(
            f"""
            INSERT INTO {table_ref()} (cache_key, cache_value, expires_at, created_at, updated_at)
            VALUES (%s, %s::jsonb, %s, NOW(), NOW())
            ON CONFLICT (cache_key) DO NOTHING
            """,
            (cache_key, cache_value_json, expires_at),
        )
        if cur.rowcount > 0:
            inserted += 1
        else:
            skipped += 1
    conn.commit()
    return inserted, skipped


def is_expired(expires_at_str: str | None) -> bool:
    if not expires_at_str:
        return False
    try:
        expires_at = datetime.fromisoformat(expires_at_str)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires_at
    except ValueError:
        return False


# ── Migration sources ─────────────────────────────────────────────────────────

def migrate_address_cache(conn: psycopg.Connection) -> None:
    """address_cache.json: {address: fias_id} → dadata:street_fias_id:{address}"""
    path = ROOT / "address_cache.json"
    if not path.exists():
        print("[address_cache.json] File not found, skipping.")
        return

    data: dict = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for address, fias_id in data.items():
        if not address or not fias_id:
            continue
        key = f"dadata:street_fias_id:{address}"
        value_json = json.dumps(fias_id, ensure_ascii=False)
        rows.append((key, value_json, None))

    inserted, skipped = insert_batch(conn, rows)
    print(f"[address_cache.json]      processed={len(rows):>6}  inserted={inserted:>6}  skipped={skipped:>6}")


def migrate_fulladdress_cache(conn: psycopg.Connection) -> None:
    """fulladdress_cache.json: {address: cleaned_text} → dadata:cleaned_text:{address}"""
    path = ROOT / "fulladdress_cache.json"
    if not path.exists():
        print("[fulladdress_cache.json] File not found, skipping.")
        return

    data: dict = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for address, cleaned_text in data.items():
        if not address or not cleaned_text:
            continue
        key = f"dadata:cleaned_text:{address}"
        value_json = json.dumps(cleaned_text, ensure_ascii=False)
        rows.append((key, value_json, None))

    inserted, skipped = insert_batch(conn, rows)
    print(f"[fulladdress_cache.json]  processed={len(rows):>6}  inserted={inserted:>6}  skipped={skipped:>6}")


def migrate_dadata_file_cache(conn: psycopg.Connection) -> None:
    """cache/dadata_address_*.json: full DaData API responses."""
    cache_dir = ROOT / "cache"
    if not cache_dir.exists():
        print("[cache/dadata_address_*] Directory not found, skipping.")
        return

    files = list(cache_dir.glob("dadata_address_*.json"))
    if not files:
        print("[cache/dadata_address_*] No files found, skipping.")
        return

    rows = []
    skipped_no_source = 0
    for f in files:
        try:
            entry = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        value = entry.get("value", {})
        source = value.get("source", "").strip()
        if not source:
            skipped_no_source += 1
            continue

        # street_fias_id key (no TTL — address data is stable)
        street_fias_id = value.get("street_fias_id")
        if street_fias_id:
            rows.append((
                f"dadata:street_fias_id:{source}",
                json.dumps(street_fias_id, ensure_ascii=False),
                None,
            ))

        # cleaned_text key
        result = value.get("result", "").strip()
        if result:
            rows.append((
                f"dadata:cleaned_text:{source}",
                json.dumps(result, ensure_ascii=False),
                None,
            ))

    inserted, skipped = insert_batch(conn, rows)
    print(
        f"[cache/dadata_address_*]  files={len(files):>6}  "
        f"rows={len(rows):>6}  inserted={inserted:>6}  skipped_dup={skipped:>6}  "
        f"skipped_no_src={skipped_no_source}"
    )


def migrate_geolocation_file_cache(conn: psycopg.Connection) -> None:
    """cache/geolocation_*.json: IP geolocation data."""
    cache_dir = ROOT / "cache"
    if not cache_dir.exists():
        print("[cache/geolocation_*] Directory not found, skipping.")
        return

    files = list(cache_dir.glob("geolocation_*.json"))
    if not files:
        print("[cache/geolocation_*] No files found, skipping.")
        return

    rows = []
    for f in files:
        # Extract IP from filename: geolocation_1.2.3.4.json → 1.2.3.4
        ip = f.stem[len("geolocation_"):]
        if not ip:
            continue

        try:
            entry = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        # IP→location mapping is stable — ignore expires_at
        value = entry.get("value", {})
        if not isinstance(value, dict):
            continue

        rows.append((
            f"geolocation_{ip}",
            json.dumps(value, ensure_ascii=False),
            None,
        ))

    inserted, skipped = insert_batch(conn, rows)
    print(
        f"[cache/geolocation_*]     files={len(files):>6}  "
        f"rows={len(rows):>6}  inserted={inserted:>6}  skipped_dup={skipped:>6}"
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Connecting to PostgreSQL...")
    print(f"Schema: {SCHEMA}, Table: {TABLE}\n")

    with psycopg.connect(CONN_STR) as conn:
        ensure_schema(conn)
        print()

        migrate_address_cache(conn)
        migrate_fulladdress_cache(conn)
        migrate_dadata_file_cache(conn)
        migrate_geolocation_file_cache(conn)

        # Final count
        row = conn.execute(f"SELECT COUNT(*) FROM {table_ref()}").fetchone()
        total = row[0] if row else 0
        print(f"\nTotal rows in {table_ref()}: {total}")

    print("\nMigration complete.")


if __name__ == "__main__":
    main()
