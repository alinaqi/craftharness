#!/usr/bin/env python3
"""Validate a craftharness claims.json against the honest-harness rules.

A harness only ships a claim as `confirmed` when it is grounded and
independently checked. This validator is the machine gate for that discipline.
Zero dependencies (stdlib only) so it runs on any surface with a bare Python.

Enforced rules
--------------
* ids unique and shaped `C-<digits>` (e.g. C-001).
* `risk_tier` and `verdict` are valid enums.
* a `confirmed` claim:
    - cites >= 1 provenance id in `supported_by`,
    - carries a non-empty structured `validation` object,
    - names both `found_by` and `validated_by`, and they differ
      (finder != validator).
* a `confirmed` claim whose `risk_tier` is `high` needs >= 2 supporting
  provenance with DISTINCT `origin_key` AND DISTINCT `content_hash` — i.e.
  two genuinely independent origins, not one source cited twice. Proving
  this requires the provenance records, so a high-risk confirmed claim whose
  supports cannot all be resolved against a top-level `provenance` array is a
  violation (independence is unproven, therefore rejected).

Input shape
-----------
    {
      "claims": [ Claim, ... ],
      "provenance": [ Provenance, ... ]   # optional, but required to prove
                                          # high-risk independence
    }

Exit 0 = clean; exit 1 = violations (printed to stderr); exit 2 = bad usage.

Usage: validate_claims.py claims.json
"""
from __future__ import annotations

import json
import re
import sys

_CLAIM_ID_RE = re.compile(r"^C-[0-9]{3,}$")

RISK_TIERS = {"routine", "high"}
VERDICTS = {"confirmed", "needs_validation", "rejected"}
REQUIRED = ("id", "statement", "risk_tier", "verdict")
PROV_REQUIRED = ("id", "source", "provider", "retrieved_at",
                 "origin_key", "content_hash")


def _enum(errs: list, cid: str, field: str, val, allowed: set) -> None:
    if val not in allowed:
        errs.append(f"{cid}: {field}={val!r} not in {sorted(allowed)}")


def _index_provenance(errs: list, doc: dict) -> dict:
    """Build id -> Provenance map, validating each record's shape and the
    uniqueness of provenance ids. A malformed provenance list is reported but
    never crashes claim checking."""
    provs = doc.get("provenance")
    index: dict = {}
    if provs is None:
        return index
    if not isinstance(provs, list):
        errs.append("provenance must be a list when present")
        return index
    for p in provs:
        if not isinstance(p, dict):
            errs.append("provenance entries must be objects")
            continue
        pid = p.get("id")
        if not pid:
            errs.append("provenance entry missing id")
            continue
        if pid in index:
            errs.append(f"provenance {pid}: duplicate id")
        for k in PROV_REQUIRED:
            if not p.get(k):
                errs.append(f"provenance {pid}: missing required field {k!r}")
        index[pid] = p
    return index


def _check_independence(errs: list, cid: str, supports: list, provs: dict) -> None:
    """A high-risk confirmed claim must resolve to >= 2 provenance records with
    distinct origin_key AND distinct content_hash."""
    resolved = [provs[s] for s in supports if s in provs]
    missing = [s for s in supports if s not in provs]
    if missing:
        errs.append(f"{cid}: high-risk support(s) not resolvable to provenance "
                    f"records: {missing} (independence unproven)")
    origins = {p.get("origin_key") for p in resolved}
    hashes = {p.get("content_hash") for p in resolved}
    if len(origins) < 2 or len(hashes) < 2:
        errs.append(f"{cid}: high-risk confirmed needs >=2 independent supports "
                    f"(distinct origin_key AND content_hash); "
                    f"got {len(origins)} origin(s), {len(hashes)} hash(es)")


def _check_confirmed(errs: list, cid: str, c: dict, provs: dict) -> None:
    """Grounding + finder!=validator + high-risk independence for a confirmed
    claim. An absent found_by/validated_by must not let the distinctness check
    pass silently."""
    supports = c.get("supported_by")
    if not isinstance(supports, list) or not supports:
        errs.append(f"{cid}: confirmed but supported_by is empty "
                    "(a confirmed claim must cite provenance)")
        supports = supports if isinstance(supports, list) else []
    validation = c.get("validation")
    if not isinstance(validation, dict) or not validation:
        errs.append(f"{cid}: confirmed but validation is not a non-empty object")
    found, val = c.get("found_by"), c.get("validated_by")
    if not found:
        errs.append(f"{cid}: confirmed but no found_by (finder must be named)")
    if not val:
        errs.append(f"{cid}: confirmed but no validated_by (validator must be named)")
    if found and val and val == found:
        errs.append(f"{cid}: validated_by must differ from found_by ({found})")
    if c.get("risk_tier") == "high":
        _check_independence(errs, cid, supports, provs)


def _check_schema(errs: list, cid: str, c: dict) -> None:
    """Shape constraints beyond the enums: id pattern and a real statement."""
    if not _CLAIM_ID_RE.match(str(c.get("id", ""))):
        errs.append(f"{cid}: id must match C-<digits> (e.g. C-001)")
    statement = c.get("statement")
    if not isinstance(statement, str) or len(statement.strip()) < 8:
        errs.append(f"{cid}: statement must be a string of >= 8 chars")
    supports = c.get("supported_by")
    if supports is not None and not isinstance(supports, list):
        errs.append(f"{cid}: supported_by must be a list of provenance ids")


def _check_claim(errs: list, seen: set, c: dict, provs: dict) -> None:
    cid = c.get("id", "<no-id>")
    for k in REQUIRED:
        if not c.get(k):
            errs.append(f"{cid}: missing required field {k!r}")
    if cid in seen:
        errs.append(f"{cid}: duplicate id")
    seen.add(cid)
    _check_schema(errs, cid, c)
    _enum(errs, cid, "risk_tier", c.get("risk_tier"), RISK_TIERS)
    _enum(errs, cid, "verdict", c.get("verdict"), VERDICTS)
    if c.get("verdict") == "confirmed":
        _check_confirmed(errs, cid, c, provs)


def validate(doc: dict) -> list[str]:
    errs: list[str] = []
    if not isinstance(doc, dict):
        return ["top level must be an object with a 'claims' list"]
    claims = doc.get("claims")
    if not isinstance(claims, list):
        return errs + ["claims must be a list"]
    provs = _index_provenance(errs, doc)
    seen: set = set()
    for c in claims:
        if not isinstance(c, dict):
            errs.append("claim entries must be objects")
            continue
        _check_claim(errs, seen, c, provs)
    return errs


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read {argv[1]}: {exc}", file=sys.stderr)
        return 2
    errs = validate(doc)
    if errs:
        print(f"INVALID — {len(errs)} problem(s):", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    claims = doc.get("claims", [])
    conf = sum(1 for c in claims if c.get("verdict") == "confirmed")
    print(f"OK — {len(claims)} claim(s) ({conf} confirmed), integrity checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
