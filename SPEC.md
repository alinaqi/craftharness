# craftharness — Product & Build Spec

**Date:** 2026-09-23 · **Owner:** Ali Naqi Shaheen · **Repo:** `~/Documents/ai-playground/craftharness`

## What craftharness is

An open-source **harness for knowledge work** — maggy's sibling for everything that
isn't code. A harness is the deliberate design of three things around any serious task
(research, business planning, content, ads, CV↔job matching, relocation planning):

1. **Workflow** — steps, branching, parallel work, retries, I/O chaining.
2. **Context & tools** — sources, instructions, memory, prior results, tools per step.
3. **Quality controls** — how results are checked and what happens on failure (retry,
   gather more evidence, human review). Grounded + validated (finder ≠ validator), with
   provenance on every claim.

Open-core: the **harness is free OSS** (works BYO-keys); a hosted data plane, **uDAPI**,
gives it superpowers out of the box. Runs on **Claude Code, claude.ai, ChatGPT, and Codex**.

## What a harness is, concretely (a harness is NOT just a skill)

A **skill** is one *component* of a harness — the instructions/method leg. A **harness** is
the assembled apparatus. Each leg of the definition needs a different mechanism:

| Harness leg | Delivered by |
|-------------|--------------|
| **1. Workflow** — steps, branching, retries | **Skill(s)** — `research-spine` + a deliverable skill; for complex/autonomous harnesses, also **orchestration code** (plugin / CLI) that runs steps deterministically |
| **2. Context & tools** | **uDAPI (an MCP server) + adapters**, plus local tools (Bash, files). The skill *declares* what to use; the fetching is the MCP server, not skill text |
| **3. Quality controls** | **Hooks** (the only real *enforcement* — a skill can only suggest) **+ `validate_claims.py`** (validator) **+ finder ≠ validator orchestration** |

```
harness  =  skill(s)        # the brain / method (workflow + context declaration)
          + tools/data      # uDAPI MCP server + adapters
          + quality hooks   # enforcement (PreToolUse/Stop) + validator
          + [plugin / CLI]  # orchestration, for multi-step or scheduled/autonomous ones
          + [memory/state]  # for recurring or long-running harnesses
```

If a harness were *only* a skill it couldn't fetch data, couldn't enforce quality (skills
can't block — only hooks can), and couldn't run unattended. **Packaging per surface:** on
Claude Code / Codex a harness ships as a **plugin** bundling skills + hooks + the uDAPI MCP
config; on claude.ai / ChatGPT (no hooks) it's **skill(s) + the uDAPI connector**, with the
quality checks running as an in-harness validator step instead of a hook.

## The two artifacts that span every surface (the key research finding)

All four target surfaces converged on the **same two open standards**, so craftharness is
built around exactly two shipping artifacts:

- **Agent Skills** (open standard, Dec 2025 — `SKILL.md` folders / `.zip` bundles) read by
  Claude Code, claude.ai (upload), Codex, Cursor, Gemini CLI, Copilot, Cline. → the harness's
  workflow/context/quality layer.
- **One remote MCP server = uDAPI** (OAuth 2.1 + DCR/CIMD). Reaches Claude Code, claude.ai
  Connectors, ChatGPT Apps/Plugins, and Codex from a single deployment. → the data/tools layer.

Corollary: **don't build for the GPT Store** (retiring into the MCP Apps SDK by Dec 2026) and
treat GPT **Actions** as legacy — bet on **MCP + an OpenAPI 3.1 spec**, not Actions.

---

## The spec list — what we will create

### A. `harness/` — the OSS harness (skills)
1. **`research-spine`** skill — the shared method: scope → gather (via uDAPI/tools) →
   synthesize → validate (finder ≠ validator) → report. Owns the Claim/provenance discipline.
2. **Deliverable skills** (specialize the spine, define output shape) — ship 2 flagships first,
   then expand down the 12 meta-harnesses by cross-industry reach:
   - `competitive-intel`, `market-research` (flagships)
   - `business-plan`, `content-studio`, `ad-generation`, `regulatory-monitor`, `cv-match`,
     `relocation-planner`, …
3. **`validate_claims.py`** — zero-dep validator enforcing the honest-harness rules (unique ids,
   immutable provenance, structured independent-validation proof, finder ≠ validator, ≥2
   independent origins for high-risk claims). Ported/adapted from the security-audit skill.
4. **Skill frontmatter** to the portable spec: `name`, `description`, `when_to_use`,
   `allowed-tools`, `license`, `compatibility` — so one skill runs on every surface. Build
   constraints (Claude Code, current): `description`+`when_to_use` share a **~1,536-char** cap
   (always in context, drives auto-invocation); invoked bodies share a **~25k-token** budget;
   keep `SKILL.md` **< 500 lines** with detail in `reference.md` / `scripts/`.
4b. **Quality-control hooks** — the "quality controls" leg delivered as **enforcement**, not just
   skill text. Skills are *context* and can only suggest; a Claude Code **`PreToolUse`/`Stop`
   hook** (exit code 2 blocks) is the only real gate — so craftharness ships the validation/
   provenance checks (e.g. "no unproven claim ships", `validate_claims.py`) as **hooks**, the way
   maggy enforces TDD via stop-hooks. Hooks are bundled in the **plugin** (`hooks/hooks.json`) and
   degrade gracefully on surfaces without hook support (claude.ai/ChatGPT), where the same checks
   run as an in-harness validator step.

### B. `conduit/` — uDAPI, the hosted data plane
5. **FastAPI gateway** (mirror srooter) — typed capabilities, provider adapters normalized to
   one `Record` schema, routing + fallback, cache, budget/metering, audit ledger, deterministic
   keyless stub.
6. **Capabilities** (from the JTBD data research):
   - Horizontal: `search`, `crawl` (Apify), `keywords` (DataForSEO), `news`, `entity`.
   - Free-gov (the differentiator, zero per-call cost): `gov-registries` (EDGAR/USPTO/FDA/EPA),
     `econ-stats` (BLS/Census/FRED/EIA), `geo-weather` (NOAA/USGS), `health` (CMS/openFDA).
   - `markets` (paid). Everything else via the adapter SDK.
7. **Contracts** (from PLAN.md §4c): `Query`/params per capability, `SourceAdapter`, `Record`,
   immutable `Provenance` (content-addressed id, `origin_key` + `content_hash` lineage,
   `snapshot_ref`), `Claim` (structured `validation` proof).
8. **Security/governance** (PLAN.md §5b): source allow/deny, fail-closed PII redaction + automated
   drift eval, cost/latency budgets, tenant isolation, retention, untrusted-content boundary.

### C. uDAPI exposure artifacts (one source → three shapes)
9. **OpenAPI 3.1 spec** — the source of truth; the REST API is authored first.
10. **Remote streamable-HTTP MCP server** (PRIMARY) — generated from the OpenAPI; OAuth 2.1 with
    **DCR + CIMD** so clients self-register (near-zero per-user setup). Capabilities as MCP tools
    carrying provenance in metadata. This one server is what installs into all four surfaces.
11. **Python + TypeScript SDKs** — thin, generated from the OpenAPI, for builders embedding uDAPI
    directly.

### D. `craftharness` CLI — author-once, compile-to-every-target (the differentiator)
12. **`craftharness init`** — detects which tools are present in a repo/machine and wires them:
    writes `.claude/skills/` + `.claude-plugin/marketplace.json` (Claude Code), `AGENTS.md`
    (Codex/Cursor/Copilot — the Linux-Foundation neutral standard, and **read natively by Claude
    Code v2.1.277+** too), `.codex/config.toml`, and a `.zip` for claude.ai upload — all from the
    single `harness/` source.
13. **`craftharness sync`** — regenerate all targets from source (the maggy `/sync-agents`
    pattern, generalized). Derived dirs gitignored; `AGENTS.md` committed.
14. **`craftharness self update`** — bundled self-updater (don't rely on the package manager).
15. **Keyless `--demo` mode** — the harness runs a deterministic sample end-to-end with no
    account, no uDAPI key, no provider creds (first-success without gating — the top conversion
    lever). Also supports a local-model path.

### E. Per-surface delivery (what a user actually installs)
16. **Claude Code / Codex:** `git clone` + `curl … | sh` installer → skills into `~/.claude`,
    `~/.codex`; a **plugin** (`.claude-plugin/plugin.json`) bundling skills + commands + the uDAPI
    MCP server; listed on a `craftharness` **marketplace.json**.
17. **claude.ai:** downloadable **skill `.zip`s** (Customize → Skills → upload) + the uDAPI
    **Connector** (remote MCP URL) submitted to the **Connectors Directory**; an **Owner install
    link** for Team/Enterprise.
18. **ChatGPT:** a **ChatGPT App/Plugin** = the uDAPI MCP server (+ optional inline UI components),
    submitted to the **Plugin Directory**; harness instructions delivered as **plugin "skills."**
    Builder path: **Responses API + hosted MCP tool**.

### F. Distribution & install
19. **Install:** `curl -LsSf https://craftharness.dev/install.sh | sh` (uv-based, no prereq);
    secondary `uv tool install craftharness` / `pipx` / `npx craftharness init`.
20. **Channels (priority):** GitHub repo → PyPI (uv) → official **MCP Registry** (pypi + oci) for
    uDAPI → Claude plugin marketplace → `awesome-*` PRs → HN + Product Hunt launch with a **demo
    GIF of cross-tool sync**.
21. **Repo assets:** README (logo → badges → one-liner → demo GIF → 1-command quickstart → why),
    runnable key-free examples, `docs/` (capability contract, skill authoring, adapter authoring).

### G. Open-core / commercial (uDAPI)
22. **Free:** full harness, BYO-keys, keyless demo.
23. **uDAPI free tier:** generous on free-gov capabilities (zero cost to us); paid capabilities
    (crawl/keywords/markets) capped.
24. **uDAPI paid:** OAuth once → managed pre-provisioned provider keys + metering (out-of-box);
    BYO-keys opt-in (pass-through). Tiers: solo / pro / team (SSO, SLA, shared config sync).
    Upgrade prompt lives **at the data boundary** and the **team/compliance boundary** — never in
    the core loop.

---

## Build sequencing

- **Phase 0 — Spec + contracts.** Ratify the capability/Record/Provenance/Claim contracts and the
  Agent-Skills frontmatter profile. Port `dataforseo.py` as the first adapter.
- **Phase 1 — Harness OSS MVP.** `research-spine` + `competitive-intel` + `validate_claims.py`;
  the `craftharness init/sync` cross-tool compiler; `--demo` keyless mode; BYO-keys. Ship on
  GitHub + PyPI. Skills run on Claude Code, Codex, and claude.ai (zip).
- **Phase 2 — uDAPI MVP.** OpenAPI-first REST + MCP server (OAuth/DCR/CIMD) with `crawl`, `search`,
  `keywords`, `gov-registries` (EDGAR), `econ-stats` (BLS); managed keys + metering; publish to
  MCP Registry. Wire the harness's out-of-box path.
- **Phase 3 — Reach + second flagship.** Connectors Directory + ChatGPT Plugin Directory listings;
  `regulatory-monitor`; sibling gov adapters; adapter SDK.
- **Phase 4 — Hosted/commercial.** Tenants, billing, team features (gated on the PLAN.md §5b
  controls + §11 decisions).

## Open decisions (carry from PLAN.md §11)
- **License: RESOLVED → Apache-2.0** (permissive + patent grant + trademark clause for the
  commercial/brand angle; MIT is a trivial swap if preferred). Phase 1 publication unblocked.
- Still open: first flagship (competitive-intel vs regulatory-monitor), tenant/hosting model,
  and the `craftharness.dev` domain/trademark.

## 2026 uncertainty flags (verify before building)
MCP Registry is pre-GA (build on `server.json`, expect churn); ChatGPT Apps SDK is early and some
docs are gated; GPT Actions/Store retirement dates are "subject to change"; CLAUDE.md ↔ AGENTS.md
interop is convention-only — **our sync tool owns the mapping**; star counts cited in research are
volatile.

---
*Synthesized from four parallel research streams (Claude Code/Codex packaging, claude.ai + ChatGPT
delivery, MCP/uDAPI exposure, packaging/distribution/install) — 2026-09-23. Source URLs in the
research transcripts.*
