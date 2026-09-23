# Example — Competitor research, cited and validated

This is a runnable, key-free example of the craftharness method in Claude Code.
It needs **no account and no API keys** — just the built-in `WebSearch`,
`WebFetch`, and `Bash` tools. (An optional `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD`
unlocks keyword volume via the conduit adapter, but is not required here.)

## 1. Install

```bash
git clone https://github.com/alinaqi/craftharness
cd craftharness
./install.sh
```

Restart Claude Code (or run `/skills`) so it picks up the harness.

## 2. Ask

In any Claude Code session, type exactly:

```
do competitor research on Notion vs Coda
```

You do not need to name the skill — the `research-spine` + `competitive-intel`
skills auto-invoke on a request like this.

## 3. What the harness does

It runs the five-step method, and you will see it work through them:

1. **SCOPE** — restates the question and the decision it serves (e.g. "which tool
   for a 20-person team's docs + lightweight databases?"), and lists the axes it
   will compare (pricing, collaboration, databases, offline, API).
2. **GATHER** — pulls evidence with real tools. Each fetch is recorded with
   *provenance*: the source, the URL, and a retrieval date. It prefers primary
   sources (each vendor's own pricing/docs pages) over secondary summaries.
3. **SYNTHESIZE** — turns the evidence into a comparison and a set of discrete
   **claims**, each tagged `routine` or `high` risk.
4. **VALIDATE** — a *separate* check (the finder is not the validator) re-opens
   each claim's cited source and confirms the statement is actually supported.
   A **high-risk** claim (e.g. a specific price or a "market leader" assertion)
   is only marked `confirmed` when **≥ 2 independent sources** — distinct
   `origin_key` *and* distinct `content_hash` — back it. Anything that fails is
   moved to a **Needs validation** section, never dropped silently.
5. **DELIVER** — a cited artifact: the comparison, a recommendation, a source
   list, and an honest "what we could not verify" section.

## 4. Sample output (abridged)

```markdown
# Notion vs Coda — competitor research
_Scope: docs + lightweight databases for a ~20-person team. Retrieved 2026-09-23._

## Verdict
Coda leans toward teams that live in interconnected tables and automations;
Notion toward teams that want a fast docs/wiki with databases attached. [C-001, C-004]

## Comparison
| Axis            | Notion                          | Coda                              |
|-----------------|---------------------------------|-----------------------------------|
| Free tier       | Unlimited blocks, solo/small    | Unlimited docs, limits on doc size|
| Paid entry      | Plus $10/user/mo (annual)       | Pro $10/maker/mo (annual)         |
| Databases       | Databases + linked views        | Tables + cross-doc + Packs        |
| Offline         | Partial (mobile/desktop)        | Limited                           |

## Claims (validated)
- **C-001** *(routine, confirmed)* — "Notion Plus is $10/user/month billed annually."
  Supported by: [P-001 notion.so/pricing]. found_by: gather · validated_by: validator.
- **C-004** *(high, confirmed)* — "Coda bills per Doc Maker, not per viewer."
  Supported by: [P-007 coda.io/pricing], [P-009 coda.io/docs/... ] — 2 independent origins.
  found_by: gather · validated_by: validator.

## Needs validation
- "Coda has more third-party integrations than Notion." — Only one secondary
  source found; vendor counts differ. Marked `needs_validation`, not shipped as fact.

## Sources
- P-001 https://www.notion.so/pricing — retrieved 2026-09-23
- P-007 https://coda.io/pricing — retrieved 2026-09-23
- P-009 https://coda.io/docs/... — retrieved 2026-09-23
```

## 5. The rule that makes it trustworthy

Every claim carries a **source and a retrieval date**. Nothing ships as
"confirmed" without a citation, high-risk claims need **two independent
sources**, and the component that validates a claim is never the one that found
it. When something can't be verified, the harness says so instead of guessing.

Try your own: `do competitor research on <your product> vs <a rival>`.
