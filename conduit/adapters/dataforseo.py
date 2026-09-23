#!/usr/bin/env python3
"""DataForSEO keyword adapter for conduit (uDAPI).

Ports the standalone DataForSEO helper into the conduit ``SourceAdapter``
shape. Capability ``keywords``, provider ``dataforseo``. Auth is HTTP Basic
(base64 ``login:password``) read from the environment:

    DATAFORSEO_LOGIN + DATAFORSEO_PASSWORD
    (or a combined DATAFORSEO_API_KEY, either "login:password" or its base64)

Never hardcode the key; never commit it. Requests go only to api.dataforseo.com.

Zero-cost fallback: with no credentials, ``fetch`` returns ``[]`` and
``health()`` returns ``False`` — so a keyless run degrades gracefully.

CLI (mirrors a simple client):
    dataforseo.py whoami                         # auth check + balance
    dataforseo.py volume "kw one" "kw two" ...   # Google Ads search volume
Options: --location <code, default 2840=US> --language <code, default en>
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

BASE = "https://api.dataforseo.com/v3"

try:  # align to the canonical contracts when conduit.core.schema is present
    from conduit.core.schema import Provenance, Query, Record
    from conduit.adapters.base import SourceAdapter
except Exception:  # pragma: no cover - fallback until conduit.core.schema lands
    from dataclasses import dataclass, field

    @dataclass
    class Query:  # type: ignore[no-redef]
        capability: str
        params: dict = field(default_factory=dict)
        fresh: bool = False
        timeout_ms: int = 15000
        cost_budget: float = 0.10

    @dataclass
    class Provenance:  # type: ignore[no-redef]
        id: str
        source: str
        provider: str
        retrieved_at: str
        url: str | None
        confidence: float
        origin_key: str
        content_hash: str
        pii_redacted: bool = False

    @dataclass
    class Record:  # type: ignore[no-redef]
        id: str
        capability: str
        title: str | None
        content: object
        entities: list
        provenance: Provenance

    class SourceAdapter:  # type: ignore[no-redef]
        capability: str = ""
        provider: str = ""

        async def fetch(self, req: Query) -> list:
            raise NotImplementedError

        def health(self) -> bool:
            return False


# --- credentials + transport ------------------------------------------------

def _creds_token() -> str | None:
    """Return the base64 Basic-auth token, or None when unconfigured."""
    login = os.environ.get("DATAFORSEO_LOGIN")
    pw = os.environ.get("DATAFORSEO_PASSWORD")
    if login and pw:
        return base64.b64encode(f"{login}:{pw}".encode()).decode()
    combined = os.environ.get("DATAFORSEO_API_KEY", "")
    if not combined:
        return None
    if ":" in combined:
        return base64.b64encode(combined.encode()).decode()
    return combined


def _post(path: str, payload: list) -> dict:
    """POST a JSON task array to DataForSEO and parse the response."""
    token = _creds_token()
    if not token:
        raise RuntimeError("DataForSEO credentials not set")
    req = urllib.request.Request(
        f"{BASE}{path}", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.load(resp)


def _get(path: str) -> dict:
    """GET a DataForSEO endpoint (used for the user_data auth check)."""
    token = _creds_token()
    if not token:
        raise RuntimeError("DataForSEO credentials not set")
    req = urllib.request.Request(f"{BASE}{path}", headers={"Authorization": f"Basic {token}"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.load(resp)


# --- record building --------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _content_hash(content: dict) -> str:
    blob = json.dumps(content, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def _confidence(row: dict) -> float:
    """Confidence in the datum, informed by the API competition where sensible.

    A concrete search_volume is measured/authoritative (base 0.85); the
    competition_index (0-100), when present, nudges it within 0.75-0.95. A
    null search_volume means DataForSEO has no measurement -> low confidence.
    """
    if row.get("search_volume") is None:
        return 0.4
    idx = row.get("competition_index")
    if isinstance(idx, (int, float)):
        return round(min(0.95, 0.75 + (idx / 100.0) * 0.2), 3)
    return 0.85


def _row_content(row: dict, location: int) -> dict:
    return {
        "keyword": row.get("keyword"),
        "search_volume": row.get("search_volume"),
        "cpc": row.get("cpc"),
        "competition": row.get("competition"),
        "competition_index": row.get("competition_index"),
        "location_code": location,
        "monthly_searches": row.get("monthly_searches"),
    }


def _make_provenance(content_hash: str, row: dict, keyword: str) -> Provenance:
    return Provenance(
        id=content_hash,
        source="dataforseo:google_ads",
        provider="dataforseo",
        retrieved_at=_now_iso(),
        url=None,
        confidence=_confidence(row),
        origin_key=f"keyword:{keyword}",
        content_hash=content_hash,
        pii_redacted=False,
    )


def _build_record(row: dict, location: int) -> Record:
    keyword = row["keyword"]
    content = _row_content(row, location)
    chash = _content_hash(content)
    prov = _make_provenance(chash, row, keyword)
    return Record(
        id=chash,
        capability="keywords",
        title=keyword,
        content=content,
        entities=[keyword],
        provenance=prov,
    )


# --- the adapter ------------------------------------------------------------

class DataForSeoAdapter(SourceAdapter):
    """Fetch Google Ads search-volume Records for a set of seed keywords."""

    capability = "keywords"
    provider = "dataforseo"

    def health(self) -> bool:
        return _creds_token() is not None

    async def fetch(self, req: Query) -> list[Record]:
        if not self.health():
            return []
        params = getattr(req, "params", None) or {}
        seeds = list(params.get("seed_keywords") or [])
        if not seeds:
            return []
        loc = int(params.get("location_code", 2840))
        lang = params.get("language_code", "en")
        payload = [{"keywords": seeds, "location_code": loc,
                    "language_code": lang, "search_partners": False}]
        data = await asyncio.to_thread(
            _post, "/keywords_data/google_ads/search_volume/live", payload)
        rows = (data.get("tasks") or [{}])[0].get("result") or []
        return [_build_record(r, loc) for r in rows if r.get("keyword")]


# --- CLI (whoami / volume) --------------------------------------------------

def _cli_opts(args: list[str]) -> tuple[list[str], int, str]:
    loc, lang, rest = 2840, "en", []
    it = iter(args)
    for a in it:
        if a == "--location":
            loc = int(next(it))
        elif a == "--language":
            lang = next(it)
        else:
            rest.append(a)
    return rest, loc, lang


def _print_volume(data: dict, loc: int, lang: str) -> None:
    task = (data.get("tasks") or [{}])[0]
    rows = task.get("result") or []
    ranked = sorted(
        ((x.get("keyword"), x.get("search_volume"),
          str(x.get("competition") or "-"), round(x.get("cpc") or 0, 2)) for x in rows),
        key=lambda x: (x[1] or -1), reverse=True)
    print(f"# cost ${task.get('cost')}  loc={loc} lang={lang}")
    print(f"{'keyword':<30}{'vol/mo':>9}  {'comp':<8}{'cpc$':>7}")
    for kw, vol, comp, cpc in ranked:
        print(f"{kw:<30}{(vol if vol is not None else 'n/a'):>9}  {comp:<8}{cpc:>7}")


def cli_whoami(_args: list[str]) -> int:
    data = _get("/appendix/user_data")
    t = data["tasks"][0]["result"][0]
    money = t.get("money") or {}
    print("login:", t.get("login"), "| balance $:", money.get("balance"))
    return 0


def cli_volume(args: list[str]) -> int:
    kws, loc, lang = _cli_opts(args)
    if not kws:
        return _cli_usage()
    payload = [{"keywords": kws, "location_code": loc,
                "language_code": lang, "search_partners": False}]
    _print_volume(_post("/keywords_data/google_ads/search_volume/live", payload), loc, lang)
    return 0


def _cli_usage() -> int:
    print(__doc__)
    return 1


def main() -> int:
    if len(sys.argv) < 2:
        return _cli_usage()
    cmd, rest = sys.argv[1], sys.argv[2:]
    handler = {"whoami": cli_whoami, "volume": cli_volume}.get(cmd, lambda _a: _cli_usage())
    try:
        return handler(rest)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
