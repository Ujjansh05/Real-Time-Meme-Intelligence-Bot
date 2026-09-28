"""Scheduled command: python Backend/trend_collect.py --source wikipedia|social|all."""

import argparse
import json

from trends import TrendStore, collect_source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("wikipedia", "social", "all"), default="all")
    args = parser.parse_args()
    choices = {"wikipedia": ("wikipedia",), "social": ("reddit", "bluesky"),
               "all": ("wikipedia", "reddit", "bluesky")}[args.source]
    store = TrendStore()
    results = [collect_source(source, store) for source in choices]
    print(json.dumps([{"source": result["source"], "status": result["status"],
                       "count": len(result.get("items", []))} for result in results]))
    return 0 if any(result["status"] in ("ok", "insufficient_data") for result in results) or all(
        result.get("message") == "Source access is not configured" for result in results
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
