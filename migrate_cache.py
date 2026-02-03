#!/usr/bin/env python3
"""
Migration script to convert individual geolocation cache files to JSONL format.
This consolidates all geolocation_*.json files into a single geolocation_cache.jsonl file.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def migrate_geolocation_cache(cache_dir: str = "cache"):
    """Migrate individual geolocation JSON files to JSONL format."""
    cache_path = Path(cache_dir)
    
    if not cache_path.exists():
        print(f"Cache directory '{cache_dir}' not found")
        return False
    
    # Find all geolocation_*.json files
    geolocation_files = list(cache_path.glob("geolocation_*.json"))
    
    if not geolocation_files:
        print("No geolocation cache files found to migrate")
        return True
    
    print(f"Found {len(geolocation_files)} geolocation cache files to migrate")
    
    jsonl_file = cache_path / "geolocation_cache.jsonl"
    migrated_count = 0
    error_count = 0
    
    # Open JSONL file for writing
    with open(jsonl_file, "w", encoding="utf-8") as jsonl_f:
        for json_file in sorted(geolocation_files):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Extract the IP from filename (geolocation_<ip>.json)
                ip = json_file.stem.replace("geolocation_", "")
                key = f"geolocation_{ip}"
                
                # Create JSONL entry
                entry = {
                    "key": key,
                    "value": data.get("value", data),  # Handle both wrapped and unwrapped formats
                    "created_at": data.get("created_at", datetime.now().isoformat()),
                }
                
                if "expires_at" in data:
                    entry["expires_at"] = data["expires_at"]
                
                # Write to JSONL
                jsonl_f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                migrated_count += 1
                
            except Exception as e:
                print(f"Error migrating {json_file.name}: {e}")
                error_count += 1
    
    print(f"\nMigration complete:")
    print(f"  ✓ Migrated: {migrated_count} entries")
    print(f"  ✗ Errors: {error_count}")
    print(f"  → Output: {jsonl_file}")
    
    # Optional: backup old files
    backup_dir = cache_path / "geolocation_backup"
    backup_dir.mkdir(exist_ok=True)
    
    for json_file in geolocation_files:
        try:
            json_file.rename(backup_dir / json_file.name)
        except Exception as e:
            print(f"Warning: Could not backup {json_file.name}: {e}")
    
    print(f"  → Backup: {backup_dir}")
    return error_count == 0

if __name__ == "__main__":
    cache_dir = sys.argv[1] if len(sys.argv) > 1 else "cache"
    success = migrate_geolocation_cache(cache_dir)
    sys.exit(0 if success else 1)
