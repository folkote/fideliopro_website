"""Probe the FidelioPro/DaData address suggestion endpoint.

Usage:
    Minimal initialization::

        python tools/probe_fideliopro_address_suggest.py

    Minimal happy-path call against the local/internal endpoint::

        python tools/probe_fideliopro_address_suggest.py --url http://127.0.0.1:7080/api/suggest/address

    Common error-handling case: a network timeout or non-JSON response exits with a
    non-zero status and prints a concise error without request secrets. No API key is
    required or sent by this utility.
"""

from __future__ import print_function

import argparse
import json
import sys
import time

import requests


DEFAULT_URL = "https://fidelio.pro/api/suggest/address"
DEFAULT_QUERY = "127282, г. Москва, ул. Ленина, дом 8, корп. 1, кв. 77"
DEFAULT_COUNT = 10
MAX_DADATA_COUNT = 20
DEFAULT_TIMEOUT_SECONDS = 10.0


def validate_count(value):
    """Return a DaData-compatible positive count, clamped to the documented max."""
    try:
        count = int(value)
    except (TypeError, ValueError):
        raise ValueError("count must be an integer")
    if count < 1:
        raise ValueError("count must be greater than zero")
    return min(count, MAX_DADATA_COUNT)


def build_request_body(query, count):
    """Build the deterministic default request body with only query and count."""
    if query is None or not str(query).strip():
        raise ValueError("query must not be empty")
    return {"query": str(query), "count": validate_count(count)}


def extract_summary(payload):
    """Extract a safe concise summary from a DaData-like suggestions payload."""
    suggestions = payload.get("suggestions") if isinstance(payload, dict) else None
    if not isinstance(suggestions, list):
        suggestions = []

    first = suggestions[0] if suggestions and isinstance(suggestions[0], dict) else {}
    first_value = first.get("value") or ""
    first_data = first.get("data") if isinstance(first.get("data"), dict) else {}
    first_fias_id = first_data.get("fias_id") or ""

    return {
        "suggestions_count": len(suggestions),
        "first_value": first_value,
        "first_fias_id": first_fias_id,
    }


def format_summary(status_code, elapsed_ms, payload, output_path=None):
    """Format the probe result summary without secrets or full PII payload dumps."""
    summary = extract_summary(payload)
    lines = [
        "HTTP status: {0}".format(status_code),
        "Elapsed ms: {0}".format(int(round(elapsed_ms))),
        "Suggestions count: {0}".format(summary["suggestions_count"]),
        "First value: {0}".format(summary["first_value"] or "<none>"),
        "First data.fias_id: {0}".format(summary["first_fias_id"] or "<none>"),
    ]
    if output_path:
        lines.append("Output saved: {0}".format(output_path))
    return "\n".join(lines)


def save_json_response(payload, output_path):
    """Save the full JSON response to a user-requested local file."""
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def post_address_suggest(url, body, timeout):
    """POST the suggestion request and return response, JSON payload, and elapsed ms."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    started = time.monotonic()
    response = requests.post(url, data=data, headers=headers, timeout=timeout)
    elapsed_ms = (time.monotonic() - started) * 1000.0
    payload = response.json()
    return response, payload, elapsed_ms


def _positive_float(value):
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("timeout must be a number")
    if timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be greater than zero")
    return timeout


def _count_arg(value):
    try:
        return validate_count(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Standalone probe for FidelioPro/DaData address suggestions."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Suggestion endpoint URL.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Address query text.")
    parser.add_argument(
        "--count",
        type=_count_arg,
        default=DEFAULT_COUNT,
        help="Suggestion count, clamped to DaData max {0}.".format(MAX_DADATA_COUNT),
    )
    parser.add_argument(
        "--timeout",
        type=_positive_float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional local file path for saving the full JSON response.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        body = build_request_body(args.query, args.count)
        response, payload, elapsed_ms = post_address_suggest(args.url, body, args.timeout)
        if args.output:
            save_json_response(payload, args.output)
        print(format_summary(response.status_code, elapsed_ms, payload, args.output))
        return 0 if 200 <= response.status_code < 300 else 1
    except requests.exceptions.RequestException as exc:
        print("Request failed: {0}".format(exc), file=sys.stderr)
        return 2
    except ValueError as exc:
        print("Invalid response or input: {0}".format(exc), file=sys.stderr)
        return 2
    except OSError as exc:
        print("Output file error: {0}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
