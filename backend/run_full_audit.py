"""CLI entrypoint for one-shot local full SEO audits.

Usage:
  python run_full_audit.py https://example.com
  python run_full_audit.py https://example.com --max-internal-urls 40 --keyword seo --keyword audit
"""

import argparse
import asyncio
import json

from tools.full_audit import run_full_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a one-shot local-first SEO full audit")
    parser.add_argument("url", help="Website URL to audit")
    parser.add_argument("--max-internal-urls", type=int, default=25, help="How many internal URLs to probe")
    parser.add_argument("--keyword", dest="keywords", action="append", default=[], help="Target keyword (repeatable)")
    return parser.parse_args()


async def _main() -> None:
    args = parse_args()
    result = await run_full_audit(args.url, args.max_internal_urls, args.keywords)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(_main())
