#!/usr/bin/env python3
"""Apify crawl adapter — the ``crawl`` capability for conduit.

Runs an Apify actor (default: ``apify/website-content-crawler``) and normalizes each
crawled page into a conduit ``Record`` with provenance (the page URL as origin, a content
hash, retrieval time). Credentials come from ``APIFY_TOKEN`` / ``APIFY_API_TOKEN`` in the
env — nothing is hardcoded. Zero external deps (urllib).

CLI:
    python3 -m conduit.adapters.apify crawl "https://example.com" [max_pages]
    python3 -m conduit.adapters.apify whoami
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

try:
    from conduit.core.schema import Query, Record, make_provenance
    from conduit.adapters.base import SourceAdapter
except Exception:  # pragma: no cover - allow standalone execution
    Query = Record = make_provenance = object  # type: ignore
    class SourceAdapter:  # type: ignore
        capability = ""
        provider = ""

_API = "https://api.apify.com/v2"
DEFAULT_ACTOR = os.environ.get("APIFY_CRAWL_ACTOR", "apify/website-content-crawler")
DEFAULT_CRAWLER = os.environ.get("APIFY_CRAWLER_TYPE", "cheerio")  # cheap + fast for text


def _token() -> str:
    tok = os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN") or ""
    if not tok:
        raise RuntimeError("Apify needs APIFY_TOKEN (or APIFY_API_TOKEN) in the env")
    return tok


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post(actor: str, payload: dict, timeout: float) -> list[dict]:
    """Run an actor synchronously and return its dataset items."""
    aid = actor.replace("/", "~")
    url = f"{_API}/acts/{aid}/run-sync-get-dataset-items?token={_token()}"
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


class ApifyAdapter(SourceAdapter):
    capability = "crawl"
    provider = "apify"

    async def fetch(self, req: "Query") -> list["Record"]:  # type: ignore[override]
        params = getattr(req, "params", {}) or {}
        urls = params.get("urls") or ([params["url"]] if params.get("url") else [])
        if not urls:
            return []
        max_pages = int(params.get("max_pages", 3))
        actor = params.get("actor", DEFAULT_ACTOR)
        payload = {
            "startUrls": [{"url": u} for u in urls],
            "maxCrawlPages": max_pages,
            "crawlerType": params.get("crawler_type", DEFAULT_CRAWLER),
            "saveMarkdown": True,
        }
        timeout = max(30.0, getattr(req, "timeout_ms", 60000) / 1000.0)
        items = await asyncio.to_thread(_post, actor, payload, timeout)
        return [self._record(it) for it in items if it.get("url")]

    def _record(self, it: dict) -> "Record":
        page_url = it["url"]
        text = it.get("text") or it.get("markdown") or ""
        title = (it.get("metadata") or {}).get("title") or it.get("title")
        prov = make_provenance(
            source=page_url, provider="apify", retrieved_at=_now(),
            payload={"url": page_url, "text": text}, url=page_url, confidence=0.6,
        )
        return Record(
            id=prov.id, capability="crawl", title=title,
            content=text, provenance=prov,
        )

    def health(self) -> bool:
        try:
            _token()
            return True
        except RuntimeError:
            return False


# --- CLI --------------------------------------------------------------------

def _cli_whoami() -> int:
    r = json.load(urllib.request.urlopen(f"{_API}/users/me?token={_token()}", timeout=20))
    d = r.get("data", {})
    print("apify user:", d.get("username"), "| plan:", (d.get("plan") or {}).get("id", "?"))
    return 0


def _cli_crawl(args: list[str]) -> int:
    if not args:
        print("usage: crawl <url> [max_pages]", file=sys.stderr)
        return 1
    url, max_pages = args[0], int(args[1]) if len(args) > 1 else 1
    q = Query(capability="crawl", params={"url": url, "max_pages": max_pages})
    recs = asyncio.run(ApifyAdapter().fetch(q))
    print(f"crawled {len(recs)} page(s) from {url}")
    for rec in recs:
        body = rec.content if isinstance(rec.content, str) else json.dumps(rec.content)
        print(f"\n# {rec.title or rec.provenance.url}\n  {rec.provenance.url}"
              f"\n  {len(body)} chars | prov {rec.provenance.id[:12]}…\n  {body[:200].strip()}…")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1
    cmd, rest = sys.argv[1], sys.argv[2:]
    try:
        return {"whoami": lambda a: _cli_whoami(), "crawl": _cli_crawl}.get(
            cmd, lambda a: (print(__doc__, file=sys.stderr) or 1))(rest)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
