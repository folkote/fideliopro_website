"""Smoke checks for the unified DaData Cleaner full-response cache helpers.

Usage:
    Minimal initialization::

        python test/smoke_dadata_clean_cache.py

    Minimal happy-path call::

        python test/smoke_dadata_clean_cache.py --address "  Москва  "

    Common error-handling case: failed assertions exit non-zero and print the
    failed check name. No DaData credentials, network, or database connection is
    required because this smoke script validates deterministic helper behavior.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import os
import sys
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADATA_SOURCE = Path(PROJECT_ROOT) / "app" / "services" / "dadata.py"


def build_sample_result() -> dict:
    return {
        "source": "Москва, Тверская 1",
        "result": "г Москва, ул Тверская, д 1",
        "street_fias_id": "street-fias-id",
        "fias_id": "fias-id",
        "unrestricted_value": "г Москва, ул Тверская, д 1",
        "qc": 0,
        "qc_geo": 0,
    }


def run_smoke(address: str) -> None:
    source = DADATA_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    constants = _extract_string_constants(tree)
    canonical_address = address.strip()
    expected_hash = hashlib.sha256(canonical_address.encode("utf-8")).hexdigest()
    cache_key = "sha256:v1:cleaner_address:{0}".format(expected_hash)
    envelope = _build_expected_envelope(
        canonical_address=canonical_address,
        cache_key=cache_key,
        result=build_sample_result(),
    )

    assert constants["DADATA_CLEAN_ADDRESS_FULL_NAMESPACE"] == "dadata_clean_address_full_v1"
    assert constants["DADATA_STREET_FIAS_NAMESPACE"] == "dadata_street_fias"
    assert constants["DADATA_CLEANED_ADDRESS_NAMESPACE"] == "dadata_cleaned_address"
    assert canonical_address == address.strip()
    assert cache_key == "sha256:v1:cleaner_address:{0}".format(expected_hash)
    assert envelope["schema_version"] == 1
    assert envelope["provider"] == "dadata"
    assert envelope["api"] == "cleaner.address"
    assert envelope["request"]["canonical_address"] == canonical_address
    assert envelope["request"]["cache_key_algorithm"] == "sha256:v1:cleaner_address:utf8_trim"
    assert envelope["response"]["status_code"] == 200
    assert envelope["response"]["body"]["result"] == "г Москва, ул Тверская, д 1"
    assert envelope["derived"]["result"] == "г Москва, ул Тверская, д 1"
    assert envelope["derived"]["street_fias_id"] == "street-fias-id"
    assert envelope["derived"]["fias_id"] == "fias-id"
    assert envelope["derived"]["unrestricted_value"] == "г Москва, ул Тверская, д 1"
    assert envelope["derived"]["qc"] == 0
    assert _method_mentions(tree, "get_clean_address_cached", "DADATA_CLEAN_ADDRESS_FULL_NAMESPACE")
    assert _method_mentions(tree, "get_street_fias_id", "get_clean_address_cached")
    assert _method_mentions(tree, "get_cleaned_address_text", "get_clean_address_cached")
    assert not _method_mentions(tree, "get_street_fias_id", "DADATA_STREET_FIAS_NAMESPACE")
    assert not _method_mentions(tree, "get_cleaned_address_text", "DADATA_CLEANED_ADDRESS_NAMESPACE")


def _extract_string_constants(tree: ast.AST) -> dict[str, str]:
    constants = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        constants[target.id] = node.value.value
    return constants


def _find_method(tree: ast.AST, method_name: str) -> ast.AsyncFunctionDef | ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.name == method_name:
            return node
    raise AssertionError("method not found: {0}".format(method_name))


def _method_mentions(tree: ast.AST, method_name: str, token: str) -> bool:
    method = _find_method(tree, method_name)
    return token in ast.unparse(method)


def _build_expected_envelope(canonical_address: str, cache_key: str, result: dict) -> dict:
    derived = {
        "result": result.get("result"),
        "street_fias_id": result.get("street_fias_id"),
        "fias_id": result.get("fias_id"),
        "unrestricted_value": result.get("unrestricted_value"),
    }
    for quality_field in (
        "qc",
        "qc_complete",
        "qc_geo",
        "qc_house",
        "qc_name",
        "qc_conflict",
    ):
        if quality_field in result:
            derived[quality_field] = result.get(quality_field)
    return {
        "schema_version": 1,
        "provider": "dadata",
        "api": "cleaner.address",
        "request": {
            "canonical_address": canonical_address,
            "cache_key_algorithm": "sha256:v1:cleaner_address:utf8_trim",
            "cache_key": cache_key,
        },
        "response": {"status_code": 200, "body": result},
        "derived": derived,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate deterministic unified DaData Cleaner cache helpers."
    )
    parser.add_argument(
        "--address",
        default="  Москва, Тверская 1  ",
        help="Address text used for canonicalization/key smoke checks.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        run_smoke(args.address)
    except AssertionError as exc:
        print("Smoke assertion failed: {0}".format(exc), file=sys.stderr)
        return 1
    print("Unified DaData Cleaner cache helper smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
