---
name: content-studio
description: Content generation with harness discipline — gather real supporting facts WITH sources first, draft to a brief (blog post, X/LinkedIn thread, or landing-page copy), then a quality pass that checks every factual claim is cited and the brief is actually met. Persuasive copy that isn't quietly making things up.
when-to-use: When asked to write a blog post, article, social thread, newsletter, or landing/marketing copy that should be accurate and on-brief. For pure market analysis use `market-research`; for rival teardowns use `competitive-intel`. Use this when the deliverable is publishable prose that still must not fabricate facts.
user-invocable: true
allowed-tools: [WebSearch, WebFetch, Bash, Read, Write]
---

# Content Studio — a content harness, not a prompt

Most "write me a blog post" flows hallucinate stats, invent quotes, and drift
off-brief. This harness doesn't. It applies the same discipline as research:
**gather real supporting facts with sources, draft against an explicit brief,
then run a separate quality pass** where the checker is not the drafter. Copy
ships persuasive *and* honest — every factual claim is traceable to a source, and
anything unverifiable is either cut or softened to opinion.

Follow the method in order. The draft is step 3 of 5, not step 1. Do not write
the piece before you have gathered the facts it will rest on.

> This skill uses the `research-spine` method for its evidence and validation
> legs. If `research-spine` is available, read it for the shared
> Claim/Provenance discipline; this file adds the content brief and the
> claims-are-cited quality pass.

---

## The method: SCOPE → GATHER → SYNTHESIZE(draft) → VALIDATE → DELIVER

### 1. SCOPE — write the brief

Never draft without an explicit brief. Capture it (and confirm with the user if
anything is missing) before gathering:

- **Format & length** — blog post (word target), X/LinkedIn thread (post count),
  landing-page copy (sections: hero, subhead, value props, CTA), newsletter.
- **Audience** — who reads it and what they already know. Sets vocabulary and
  depth.
- **Goal / CTA** — the one action or belief change the piece drives.
- **Key message** — the single sentence the reader must walk away with.
- **Voice & constraints** — tone, brand rules, must-include or must-avoid terms,
  reading level, any claims legal/brand forbids.
- **Factual load** — list the claims the piece *needs* to be credible (stats,
  dates, capabilities, comparisons). Each becomes a gather target. Tag any claim
  that is risky if wrong (a specific stat, a competitor comparison, a compliance
  or safety statement) as **high-risk**.

Write the brief as a short block at the top of your working notes. The VALIDATE
step checks the draft against it, so it must be concrete.

### 2. GATHER — real supporting facts, with sources

For every factual claim the brief needs, find a real source. **Do not fabricate
statistics, quotes, dates, or study results.** Placeholder numbers ("studies show
73%…") are banned.

1. `WebSearch` for authoritative, dated sources for each claim in the factual
   load. Prefer primary sources (the study, the filing, the vendor's own docs)
   over aggregators.
2. `WebFetch` the page and read the claim **in context** before relying on it —
   confirm the number, the date, and that the source actually says what you want
   to write. Never cite from a search snippet alone.
3. Record a provenance stub per fact (align to `conduit/core/schema.py`
   `Provenance`):

```json
{
  "id": "<sha256 of the exact quoted content>",
  "source": "Publisher / study name",
  "provider": "web",
  "retrieved_at": "2026-09-23T00:00:00Z",
  "url": "https://...",
  "confidence": 0.85,
  "origin_key": "example.com",
  "content_hash": "<sha256 of the exact quoted content>",
  "pii_redacted": false
}
```

4. If a needed fact has **no** credible source, you have three honest options —
   pick one, never invent: (a) cut the claim, (b) rewrite it as clearly-marked
   opinion/framing ("we believe…"), or (c) flag it to the user as a gap. Note the
   choice; it surfaces in DELIVER.

Facts you gather for brand/voice (from a provided style guide or existing pages
via `Read`) are also captured here so the draft can match them.

### 3. SYNTHESIZE — draft against the brief

Now write. Map each factual sentence to the provenance that backs it as you go —
keep a running claim list so VALIDATE has something to check:

```json
{
  "id": "C-001",
  "statement": "Teams using X cut onboarding time by ~40%.",
  "risk_tier": "high",
  "supported_by": ["<provenance id>"],
  "verdict": "needs_validation",
  "found_by": "content-studio/draft",
  "validated_by": "",
  "validation": {}
}
```

Drafting rules:

- **Every factual sentence traces to a gathered source.** If you find yourself
  writing a claim you didn't gather, stop — gather it (back to step 2) or turn it
  into explicit opinion.
- **Opinion is allowed and labeled.** Persuasive framing, analogies, and points
  of view are the craft — they just aren't dressed up as facts. Keep the line
  between "this is true and sourced" and "this is our take" visible.
- **Hit the brief's shape.** Word/post count, section list, CTA, key message,
  and must-include terms — build them in now, don't hope to bolt them on.
- **No fake specifics.** No invented quotes, fake customer names, made-up study
  citations, or precise numbers you can't source. Round honestly or omit.
- All claims leave the draft as `needs_validation`; VALIDATE promotes them.

Produce the draft **plus** an inline citation map (which sentence → which source)
so the quality pass is mechanical, not guesswork.

### 4. VALIDATE — the quality pass (checker ≠ drafter)

Re-approach the draft as a skeptical editor who did not write it. Two checks,
both required:

**A. Claims-are-cited check.** Walk every sentence:

1. Is it a factual assertion? If yes, does it have a `supported_by` source?
   - No source → cut it, soften it to labeled opinion, or send it back to gather.
2. Re-open each cited source (`WebFetch`) and confirm it still supports the exact
   wording — no drift, no exaggeration ("linked to" ≠ "causes"; "up to 40%" ≠
   "40%"). Set `validated_by` to a label **distinct from** `found_by` (e.g.
   `content-studio/quality`).
3. For **high-risk** claims, require **≥2 supporting provenance with distinct
   `origin_key` AND distinct `content_hash`** to mark `confirmed`; otherwise soften
   the wording or attribute it explicitly to the single source ("according to
   [source]…") and leave it `needs_validation`.
4. Set each verdict: `confirmed` / `needs_validation` / `rejected`, and record the
   check in `validation`. Rewrite or remove anything `rejected`.

**B. Brief-conformance check.** Score the draft against the SCOPE brief:

- Format and length within target? Section list complete?
- Audience/voice/tone honored? Must-include terms present, must-avoid absent?
- Key message unmistakable? CTA present and clear?
- Any forbidden claim slipped in?

If a machine validator is present, run it as a gate on the claim list:

```bash
python3 harness/lib/validate_claims.py claims.json
```

Iterate: fix cited-claim failures and brief misses, then re-check. Do not proceed
to DELIVER with an open A-failure (an uncited factual claim) or a brief miss.

### 5. DELIVER — the piece plus a transparency note

Write the final artifact (`Write`). Deliver:

1. **The content itself**, publish-ready, in the requested format — clean prose
   without inline `[n]` clutter unless the format wants visible citations (e.g. a
   researched blog post often should show them; a landing hero should not).
2. **Sources** — a numbered list backing every factual claim: source name, url,
   `retrieved_at`. For formats where inline markers would hurt readability, keep
   the citations in this appendix and the claim→source map alongside.
3. **Brief-conformance summary** — a short line confirming length, format,
   audience, key message, and CTA were met (or noting any deliberate deviation).
4. **Needs validation / editorial notes** — the honest section: any claim that
   could not be confirmed and how it was handled (cut / softened / single-source
   attributed), plus anything the user should verify before publishing (legal,
   brand, a stat you'd want a second source on). **Never omit this** — if
   everything checked out, say so explicitly.

---

## Guardrails

- **Never fabricate facts.** No invented stats, quotes, studies, dates, or
  customer names. Unsourced specifics get cut or turned into labeled opinion.
- **Draft is step 3, not step 1.** Gather the facts the piece rests on first.
- **Checker ≠ drafter.** The quality pass re-verifies against sources with fresh
  eyes; `validated_by` differs from `found_by`.
- **Match the wording to the source.** No strengthening "associated with" into
  "causes", no dropping a "up to".
- **Opinion is fine, disguising it as fact is not.** Keep the line visible.
- **Meet the brief.** Persuasive but off-brief (wrong length, missing CTA, wrong
  audience) is a fail — the conformance check catches it.
- **Be transparent.** The transparency note tells the user exactly what is
  sourced and what still needs a human check.

## Minimal example (shape only)

> **Brief:** 900-word blog post, audience = eng leaders, goal = book a demo,
> key message = "cited AI content beats fast AI content", must-include = "harness".
>
> **Draft claim C-003 (high-risk):** "Hallucinated stats appear in ~X% of
> unedited AI drafts." → gather found one source → VALIDATE: single origin, so
> soften to "One [study] found roughly X%…" and mark `needs_validation`.
>
> **Deliver → Needs validation:** "The X% figure rests on a single study [2];
> recommend a second source or attribute it in-line before publishing."
