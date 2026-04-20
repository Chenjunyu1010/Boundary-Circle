from __future__ import annotations

import argparse
import json
from typing import Any

import requests


def trigger_admin_seed(
    *,
    base_url: str,
    admin_key: str,
    dataset: str,
    reset: bool,
) -> dict[str, Any]:
    normalized_base_url = base_url.rstrip("/")
    endpoint = "/admin/seed/reset" if reset else "/admin/seed"
    response = requests.post(
        f"{normalized_base_url}{endpoint}?dataset={dataset}",
        headers={"X-Admin-Key": admin_key},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trigger remote seed import/reset through the admin API.")
    parser.add_argument("dataset", choices=["demo", "stress", "stress2"], help="Seed dataset to manage remotely.")
    parser.add_argument("--base-url", required=True, help="Backend base URL, for example https://example.up.railway.app")
    parser.add_argument("--admin-key", required=True, help="Value for the X-Admin-Key header.")
    parser.add_argument("--reset", action="store_true", help="Reset the selected dataset instead of importing it.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = trigger_admin_seed(
        base_url=args.base_url,
        admin_key=args.admin_key,
        dataset=args.dataset,
        reset=args.reset,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
