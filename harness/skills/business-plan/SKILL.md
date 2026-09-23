---
name: business-plan
description: Draft a grounded business plan — problem, market/TAM, competition, model, GTM, financials — where every external claim is cited and every number is labelled fact, assumption, or projection.
when-to-use: >-
  When asked to write or draft a business plan, investment memo, or go-to-market
  plan for a company or product. Specializes research-spine for planning work.
user-invocable: true
allowed-tools: [WebSearch, WebFetch, Bash, Read, Write]
---

# Business Plan

A business plan mixes **cited facts** (market size, competitors, prices you can
verify) with **assumptions** and **projections** (revenue, costs, adoption) that
cannot be looked up. The whole point of the harness here is to **never let an
assumption masquerade as a fact.** Follow the `research-spine` method; the rules
below are what make a plan honest instead of confident fiction.

## The one discipline that matters

Every quantitative statement is tagged, explicitly, as one of:

- **[FACT]** — verifiable and **cited** (source + retrieval date). Market sizes,
  competitor pricing, published funding, headcounts, adoption stats.
- **[ASSUMPTION]** — an input you are choosing; state it and its basis.
- **[PROJECTION]** — an output derived from assumptions; show the formula/driver.

A number with no tag is a bug. A projection presented as a fact is the failure
mode this skill exists to prevent.

## Method (specializes research-spine)

### 1. SCOPE
Pin: the company/product, the audience for the plan (investor / internal / partner),
the stage (idea / launched / scaling), and the geography. Ask **one** sharp
clarifying question only if the entity is ambiguous; otherwise proceed on the most
likely reading and note it.

### 2. GATHER (cite everything external)
For the sections that CAN be grounded, gather with provenance:
- **Market / TAM-SAM-SOM** — sizing reports, `econ-stats` where relevant; cite each figure.
- **Competition** — real competitors, their positioning and pricing (WebSearch/WebFetch;
  for search-demand, the DataForSEO adapter: `python3 -m conduit.adapters.dataforseo volume "<term>" "<term>"`).
- **Demand signal** — search volume / trends for the category.
- **Regulatory / context** — anything that constrains the model.
For a **private company you know internally** (e.g. your own), treat internal
knowledge as an **[ASSUMPTION]** unless it is publicly verifiable — the plan must
stand on cited or clearly-flagged inputs, not unverifiable private claims.

### 3. SYNTHESIZE — the plan
Standard sections, each carrying its tags:
1. **Summary** — the thesis in 3–4 lines.
2. **Problem** — who hurts, how much (cite where possible).
3. **Solution / product**.
4. **Market** — TAM/SAM/SOM, each figure `[FACT]`-cited or `[ASSUMPTION]`-stated.
5. **Competition** — a matrix of real, cited competitors + the wedge.
6. **Business model** — pricing, unit economics; inputs `[ASSUMPTION]`, outputs `[PROJECTION]`.
7. **Go-to-market** — channels, motion, first 3 milestones.
8. **Financials** — a simple 3-year sketch; **every line a `[PROJECTION]` with its
   driver assumptions listed**. No invented "current revenue" for a private company.
9. **Risks & unknowns** — explicit, including what you could not verify.

### 4. VALIDATE (finder ≠ validator)
Record each external `[FACT]` as a Claim with its source, then run the gate:
```bash
python3 harness/lib/validate_claims.py claims.json
```
A separate pass checks: is every `[FACT]` cited and does the source support it?
is any `[PROJECTION]` secretly stated as fact? are competitor claims real? Downgrade
anything unverifiable to `[ASSUMPTION]` or the "Unknowns" section — never delete the
uncertainty to look more confident.

### 5. DELIVER
The plan, followed by:
- **Sources** — every `[FACT]`'s citation with retrieval date.
- **Key assumptions** — the inputs the whole plan rests on (so a reader can challenge them).
- **What I could not verify** — the honest gap list.

## Anti-patterns
- Inventing a private company's revenue, margins, or headcount as fact.
- A TAM number with no source ("the market is $50B").
- Financial projections with no visible driver assumptions.
- A competitor comparison built from memory instead of cited current positioning.
- Hiding uncertainty to make the plan read as finished.
