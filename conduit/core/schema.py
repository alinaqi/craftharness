"""Founding data contracts for craftharness / conduit (the uDAPI data gateway).

These types are the shared vocabulary every harness speaks: a ``Query`` asks a
capability for evidence, a ``SourceAdapter`` returns ``Record`` objects each
carrying immutable ``Provenance``, and a ``Claim`` ties a statement to the
provenance that supports it under the finder != validator discipline.

Design rules honoured here:
  * Every fetched fact carries a source + retrieval date (``Provenance``).
  * A provenance id is the sha256 content hash of its canonical payload, so the
    same fact from the same origin always hashes to the same id (dedupe-friendly)
    while a different origin produces a different ``origin_key``.
  * Independence for a high-risk confirmed claim requires >= 2 supporting
    provenances with DISTINCT ``origin_key`` AND ``content_hash``, and the
    ``validated_by`` agent must differ from ``found_by``.

Pure stdlib. Fully typed. Importable with no side effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal, Union
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

__all__ = [
    "RiskTier",
    "Verdict",
    "Query",
    "Provenance",
    "Record",
    "Claim",
    "canonical_json",
    "compute_content_hash",
    "compute_provenance_id",
    "normalize_origin_key",
    "make_provenance",
    "independent_support",
]

# --- literal enumerations -------------------------------------------------

RiskTier = Literal["routine", "high"]
Verdict = Literal["confirmed", "needs_validation", "rejected"]

# Query params / record content are free-form JSON-ish payloads.
JSONValue = Union[str, int, float, bool, None, dict, list]

# Tracking / analytics query params stripped when computing an origin_key so
# that two links to the same resource collapse to one origin.
_TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "utm_id",
        "utm_name",
        "utm_reader",
        "utm_referrer",
        "gclid",
        "gclsrc",
        "dclid",
        "fbclid",
        "msclkid",
        "mc_cid",
        "mc_eid",
        "igshid",
        "ref",
        "ref_src",
        "ref_url",
        "spm",
        "yclid",
        "_hsenc",
        "_hsmi",
        "vero_id",
        "wickedid",
        "oly_anon_id",
        "oly_enc_id",
    }
)


# --- canonicalisation + hashing helpers -----------------------------------

def canonical_json(payload: Any) -> str:
    """Deterministic JSON string used as the pre-image for every hash.

    Keys are sorted and whitespace is collapsed so equal payloads always
    produce byte-identical output regardless of construction order.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def compute_content_hash(payload: Any) -> str:
    """sha256 of just the record content — the independence fingerprint.

    Two provenances sharing a content_hash carry the same underlying text and
    therefore do NOT count as independent corroboration.
    """
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def compute_provenance_id(
    source: str,
    provider: str,
    retrieved_at: str,
    payload: Any,
) -> str:
    """sha256 over the canonical json of source+provider+retrieved_at+payload.

    This is the stable identity of a fetched fact. Including the provider and
    retrieval time means the same content re-fetched later, or via a different
    provider, is a distinct provenance record with its own id.
    """
    preimage = {
        "source": source,
        "provider": provider,
        "retrieved_at": retrieved_at,
        "payload": payload,
    }
    return hashlib.sha256(canonical_json(preimage).encode("utf-8")).hexdigest()


def normalize_origin_key(url: str | None) -> str:
    """Normalise a web URL into a stable origin key.

    Lowercases scheme + host, strips tracking query params, drops the fragment,
    removes a trailing slash from the path, and sorts remaining query params so
    cosmetic differences collapse. Non-URL / empty inputs are lowercased and
    stripped as a best-effort fallback so a caller always gets a usable key.
    """
    if not url:
        return ""
    parts = urlsplit(url.strip())
    if not parts.scheme and not parts.netloc:
        # Not a real URL (e.g. an API id or bare host) — normalise loosely.
        return url.strip().lower()

    scheme = parts.scheme.lower()
    host = parts.hostname.lower() if parts.hostname else ""
    if parts.port:
        host = f"{host}:{parts.port}"

    path = parts.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    kept = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _TRACKING_PARAMS
    ]
    kept.sort()
    query = urlencode(kept)

    return urlunsplit((scheme, host, path, query, ""))


# --- core dataclasses -----------------------------------------------------

@dataclass(slots=True)
class Query:
    """A request to a capability for evidence.

    ``fresh`` forces a live fetch (bypass any cache). ``cost_budget`` is the
    ceiling in USD a single fetch may spend; ``timeout_ms`` bounds latency.
    """

    capability: str
    params: dict[str, JSONValue] = field(default_factory=dict)
    fresh: bool = False
    timeout_ms: int = 15000
    cost_budget: float = 0.10


@dataclass(slots=True, frozen=True)
class Provenance:
    """Immutable record of where a fact came from.

    ``id`` is the sha256 content hash (see ``compute_provenance_id``).
    ``origin_key`` identifies the source independently of the exact content;
    ``content_hash`` fingerprints the content independently of the source.
    Both must differ across supporting provenances for a high-risk confirmation.
    """

    id: str
    source: str
    provider: str
    retrieved_at: str  # ISO-8601 timestamp
    confidence: float
    origin_key: str
    content_hash: str
    url: str | None = None
    pii_redacted: bool = False


@dataclass(slots=True)
class Record:
    """A single unit of evidence returned by an adapter."""

    id: str
    capability: str
    content: str | dict[str, JSONValue]
    provenance: Provenance
    title: str | None = None
    entities: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Claim:
    """A statement under validation, bound to its supporting provenance.

    ``supported_by`` holds ``Provenance.id`` strings. A claim is only
    ``confirmed`` once a validator (``validated_by`` != ``found_by``) checks the
    statement against those sources; high-risk claims additionally need >= 2
    independent supports (see ``independent_support``).
    """

    id: str  # e.g. "C-001"
    statement: str
    risk_tier: RiskTier
    found_by: str
    validated_by: str = ""
    supported_by: list[str] = field(default_factory=list)
    verdict: Verdict = "needs_validation"
    validation: dict[str, JSONValue] = field(default_factory=dict)


# --- convenience constructors + independence check ------------------------

def make_provenance(
    source: str,
    provider: str,
    retrieved_at: str,
    payload: Any,
    *,
    confidence: float = 0.5,
    url: str | None = None,
    pii_redacted: bool = False,
    origin_key: str | None = None,
) -> Provenance:
    """Build a ``Provenance`` with id, content_hash and origin_key derived.

    ``origin_key`` defaults to the normalised ``url`` (or ``source`` when no URL
    is given). Pass an explicit ``origin_key`` for non-web providers.
    """
    key = origin_key if origin_key is not None else normalize_origin_key(url or source)
    return Provenance(
        id=compute_provenance_id(source, provider, retrieved_at, payload),
        source=source,
        provider=provider,
        retrieved_at=retrieved_at,
        confidence=confidence,
        origin_key=key,
        content_hash=compute_content_hash(payload),
        url=url,
        pii_redacted=pii_redacted,
    )


def independent_support(provenances: list[Provenance]) -> int:
    """Count independent supports: distinct (origin_key, content_hash) pairs.

    A high-risk claim needs the return value to be >= 2 to be confirmable.
    """
    seen: set[tuple[str, str]] = set()
    for p in provenances:
        seen.add((p.origin_key, p.content_hash))
    return len(seen)
