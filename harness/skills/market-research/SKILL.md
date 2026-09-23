---
name: market-research
description: Cited market and topic research — market size, segments, trends, players, and risks, each finding grounded in a real source with a retrieval date and a finder≠validator check. Specializes research-spine for the "how big / who / where's it going" question.
when-to-use: When asked to "research a market", size a market (TAM/SAM/SOM), map segments or trends, list the players in a space, or assess demand/risk for a topic before a business or product decision. For head-to-head rival teardown use `competitive-intel`; for drafting copy use `content-studio`.
user-invocable: true
allowed-tools: [WebSearch, WebFetch, Bash, Read, Write]
---

# Market Research — a harness, not a web search

You are running a **harness**: a deliberate loop that turns a fuzzy market
question into a **cited artifact** where every claim carries a source and a
retrieval date, and where the agent that *found* a fact is never the only one
that *confirmed* it. The output is trustworthy because it is grounded and
validated — not because it sounds confident.

Follow the method in order. Do not skip GATHER to synthesize from memory, and do
not skip VALIDATE to ship faster. An unverified number is a **hypothesis**, and
it ships in the "Needs validation" section, never as a headline figure.

> This skill specializes `research-spine`. If `research-spine` is available,
> read it first for the shared Claim/Provenance discipline; this file adds the
> market-specific scope, source map, and output shape.

---

## The method: SCOPE → GATHER → SYNTHESIZE → VALIDATE → DELIVER

### 1. SCOPE

Turn the request into an explicit brief before touching a tool. Write it down
(a short block at the top of your working notes) and confirm it with the user if
anything is ambiguous:

- **Market definition** — the exact product/service category, in one sentence.
  "Meal-kit delivery in the US" is scopeable; "food tech" is not.
- **Geography & time** — which country/region, and which year(s). A 2021 figure
  is not a 2026 figure; say which you need.
- **Questions to answer** — pick from: size (TAM/SAM/SOM), growth rate (CAGR),
  segments, key players & shares, trends/drivers, risks/headwinds, regulation.
- **Decision it feeds** — enter/skip, price point, positioning, build/buy. This
  sets how precise the numbers must be.
- **Risk tier per question.** Tag each question `routine` or `high`. A number
  that drives spend or a go/no-go is **high-risk** and needs ≥2 independent
  sources to be "confirmed" (see VALIDATE).

Produce a numbered question list `Q1..Qn`. Everything downstream maps to these.

### 2. GATHER — evidence with provenance

For each question, collect evidence using the real tools available. **Every
retrieved fact gets a provenance record** — capture it as you go, not at the end.

**Source map (prefer authoritative, dated, primary):**

| Need | Go-to sources |
|------|---------------|
| Market size / CAGR | Analyst/industry reports, trade associations, company filings (10-K/S-1 give TAM claims), gov statistics (Census, BLS, Eurostat) |
| Segments & demand | Gov economic stats, industry surveys, category reports |
| Players & shares | Company filings, press releases, reputable trade press, product directories |
| Trends & drivers | Recent news (last 12–18 mo), analyst commentary, gov/regulatory notices |
| Risks & regulation | Regulator sites, filings' risk-factor sections, reputable news |

**How to gather:**

1. `WebSearch` to find candidate sources. Prefer primary and dated results;
   distrust undated, SEO-farm, and "top 10" listicle pages for numbers.
2. `WebFetch` the actual page to read the figure **in context** — never cite a
   number you only saw in a search snippet. Confirm the page states it, for the
   geography and year in scope.
3. For each fact you will use, record a provenance stub (see schema below).
4. Prefer **two different origins** for any figure you expect to headline. If a
   number appears only on aggregators that all cite one analyst, that is **one**
   origin, not many.

**Provenance record** (align to `conduit/core/schema.py` `Provenance`) — capture
per fact:

```json
{
  "id": "<sha256 of the exact quoted content>",
  "source": "US Census Bureau — 2025 Annual Retail Trade Survey",
  "provider": "web",
  "retrieved_at": "2026-09-23T00:00:00Z",
  "url": "https://www.census.gov/...",
  "confidence": 0.9,
  "origin_key": "census.gov",
  "content_hash": "<sha256 of the exact quoted content>",
  "pii_redacted": false
}
```

`origin_key` is the publisher/domain identity — two URLs on the same site, or two
resellers of the same analyst report, share an `origin_key` and do **not** count
as independent. Compute a hash for `id`/`content_hash` over the exact sentence(s)
you are relying on:

```bash
printf '%s' "the exact quoted claim text" | shasum -a 256 | cut -d' ' -f1
```

If a question yields no usable source, record that — it goes to "Needs
validation", it does not get answered from prior knowledge.

### 3. SYNTHESIZE — turn evidence into claims

Convert findings into **Claims**, each tied to the provenance that supports it.
Align to the `Claim` contract:

```json
{
  "id": "C-001",
  "statement": "The US meal-kit delivery market was ~$X.XB in 2025.",
  "risk_tier": "high",
  "supported_by": ["<provenance id>", "<provenance id>"],
  "verdict": "needs_validation",
  "found_by": "market-research/gather",
  "validated_by": "",
  "validation": {}
}
```

Rules while synthesizing:

- One statement per claim; keep it atomic and checkable. Split "the market is $X
  and growing at Y%" into two claims — they may have different sources and
  verdicts.
- Attach `supported_by` provenance ids. A claim with no support cannot leave
  synthesis as anything but a flagged gap.
- Reconcile conflicts openly. If two credible sources disagree on size, state the
  range and both sources; do not silently pick one.
- Distinguish **fact** (cited) from **estimate** (your derivation, e.g. SOM from
  a share assumption). Label estimates and show the arithmetic and its inputs'
  sources.
- All claims leave this step as `needs_validation`. VALIDATE promotes them.

### 4. VALIDATE — finder ≠ validator

This is the step that makes the harness honest. **Re-check each claim against its
cited source with fresh eyes** — do not trust the synthesis pass.

For each claim:

1. **Independent re-read.** Open each `supported_by` source again (`WebFetch`)
   and confirm the source actually states the claim, for the scoped geography and
   year. Set `validated_by` to a label distinct from `found_by` (e.g.
   `market-research/validate`). `validated_by` **must differ from** `found_by`.
2. **Independence test for high-risk claims.** A `high` claim may become
   `confirmed` only with **≥2 supporting provenance records that have distinct
   `origin_key` AND distinct `content_hash`**. Two quotes of the same report, or
   two pages of one site, fail this — such a claim stays `needs_validation`.
3. **Set the verdict:**
   - `confirmed` — source(s) verified, independence met (for high-risk).
   - `needs_validation` — supported but not independently corroborated, or the
     source is weak/undated, or it's an unverified estimate.
   - `rejected` — the source does not actually support the statement, or is
     unreliable. Remove it from headline findings.
4. Record the check in `validation`, e.g.
   `{"method": "re-fetch + independence", "origins": ["census.gov", "bls.gov"], "notes": "both state 2025 figure"}`.

If a machine validator is present, run it and treat its exit code as the gate:

```bash
# zero-dep validator; enforces unique ids, immutable provenance,
# finder≠validator, and ≥2 independent origins for high-risk confirmed claims
python3 harness/lib/validate_claims.py claims.json
```

Do not upgrade a verdict the validator rejects.

### 5. DELIVER — a cited artifact

Write the report to a file (`Write`). Structure:

1. **Title & brief** — market definition, geography, time window, date of
   research (`retrieved_at`), and the decision it feeds.
2. **Executive summary** — 3–6 bullets, each ending with a citation marker.
   Only `confirmed` claims appear here as facts; estimates are labeled.
3. **Market size** — TAM/SAM/SOM with figures, year, method, and sources. Show a
   range when sources conflict.
4. **Segments** — the meaningful cuts, with any per-segment figures cited.
5. **Trends & drivers** — dated, sourced, most recent first.
6. **Key players** — names, positioning, and shares where cited; no invented
   shares.
7. **Risks & headwinds** — regulatory, demand, competitive; sourced.
8. **Sources** — numbered list; each entry: source name, url, `retrieved_at`.
   Every citation marker in the body resolves here.
9. **Needs validation** — the honest section. Every `needs_validation` and
   `rejected` claim, why it could not be confirmed, and what source would close
   the gap. **Never empty by omission** — if everything was confirmed, say so
   explicitly.

**Citation style:** append `[n]` after each factual sentence, resolving to
Sources. A sentence in the body with no `[n]` must be clearly your own
analysis/estimate, not a claimed fact.

---

## Guardrails

- **No citation, no fact.** A number without a live, dated source is a hypothesis
  and lives only under "Needs validation".
- **Snapshot in context, not snippet.** Cite the fetched page, not the search
  result blurb.
- **Recency matters for markets.** Prefer sources ≤18 months old for size/trend
  claims; always state the figure's year.
- **Estimates are labeled and shown.** Any derived number (e.g. SOM) shows its
  formula and the sources of its inputs.
- **Independence is by origin, not by URL count.** Ten pages citing one analyst
  are one origin.
- **Be honest about gaps.** A short, correct report with a full "Needs
  validation" section beats a comprehensive-looking one built on unsourced
  numbers.

## Minimal example (shape only)

> **Executive summary**
> - The US meal-kit delivery market was ~$XB in 2025 [1][2]. *(confirmed — two
>   independent origins)*
> - Projected CAGR ~Y% through 2030 [3]. *(needs validation — single analyst
>   source)*
>
> **Needs validation**
> - CAGR ~Y% rests on one analyst press release [3]; no independent corroboration
>   found. Close by locating a second, methodologically distinct forecast.
