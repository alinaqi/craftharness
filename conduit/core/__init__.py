"""conduit.core — the founding data contracts for craftharness.

Public types and helpers every harness and adapter shares. Import from here
(``from conduit.core import Query, Record, Provenance, Claim``) rather than
reaching into ``schema`` directly.
"""

from __future__ import annotations

from conduit.core.schema import (
    Claim,
    Provenance,
    Query,
    Record,
    RiskTier,
    Verdict,
    canonical_json,
    compute_content_hash,
    compute_provenance_id,
    independent_support,
    make_provenance,
    normalize_origin_key,
)

__all__ = [
    "Query",
    "Provenance",
    "Record",
    "Claim",
    "RiskTier",
    "Verdict",
    "canonical_json",
    "compute_content_hash",
    "compute_provenance_id",
    "normalize_origin_key",
    "make_provenance",
    "independent_support",
]
