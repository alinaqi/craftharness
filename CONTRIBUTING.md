# Contributing to craftharness

Thanks for helping build a harness for knowledge work. This guide covers the two
things most contributions are — a **skill** or a **data adapter** — and the one
rule that everything here is built around: **cite everything, and the finder is
never the validator.**

## The non-negotiable rule

Every factual claim a harness ships carries a **source and a retrieval date**.
Nothing is presented as `confirmed` without a citation. Two parts enforce this:

1. **Provenance on every piece of evidence.** When a skill or adapter gathers a
   fact, it records where it came from (see the `Provenance` contract in
   `conduit/core/schema.py`): source, provider, URL, retrieval timestamp, and a
   content hash.
2. **finder ≠ validator.** The component that *found* a claim may not be the one
   that *confirms* it. A separate validation pass re-checks each claim against
   its cited source. In a `Claim`, `validated_by` must differ from `found_by`.
   A **high-risk** claim is only `confirmed` with **≥ 2 supporting sources that
   have distinct `origin_key` AND distinct `content_hash`** (genuinely
   independent origins, not the same page fetched twice). Everything else is
   `needs_validation` and ships in an honest "could not verify" section.

`harness/lib/validate_claims.py` is the machine check for these rules. It is
**stdlib-only** (zero external dependencies) — keep it that way so it runs
anywhere, including as a Claude Code hook.

## Project layout

```
harness/     # the OSS harness you install
  skills/    #   SKILL.md folders — the method (research-spine + deliverables)
  lib/       #   validate_claims.py + shared helpers (stdlib only)
  hooks/     #   quality-control hooks (Stop/PreToolUse enforcement)
conduit/     # uDAPI — the data plane
  core/      #   schema.py: Query / Provenance / Record / Claim / SourceAdapter
  adapters/  #   provider adapters normalized to the Record schema
examples/    # runnable, key-free examples
docs/        # contract + authoring guides
```

Do not edit `README.md` or `SPEC.md` in a routine PR — open an issue first if the
product framing needs to change.

## Contributing a skill

Skills use the **Agent Skills** format: a folder under `harness/skills/<name>/`
containing a `SKILL.md`.

1. **Frontmatter (YAML):**
   ```yaml
   ---
   name: competitive-intel
   description: <what it does — appears in every context, drives auto-invocation>
   when-to-use: <the trigger conditions, plainly>
   allowed-tools: [WebSearch, WebFetch, Bash]
   ---
   ```
   Keep `description` + `when-to-use` tight (they are always in context). Only
   list tools the skill actually uses.
2. **Body:** Markdown, **under ~450 lines**. Push long detail into a sibling
   `reference.md` or `scripts/`.
3. **Follow the method:** SCOPE → GATHER (with provenance) → SYNTHESIZE →
   VALIDATE (finder ≠ validator) → DELIVER a cited artifact. Deliverable skills
   specialize the shared `research-spine`; they define output *shape*, not a new
   quality bar.
4. **Usable TODAY:** a skill must work in Claude Code with its real tools
   (`WebSearch`, `WebFetch`, `Bash`) and, when a key is present, the conduit
   `dataforseo` adapter. **BYO-keys** — never require a hosted service to start.
5. **Test it** by installing (`./install.sh --dest /tmp/ch`) and running the
   trigger phrase; confirm claims come out cited and that unverifiable ones land
   in a "needs validation" section.

## Contributing an adapter

An adapter fetches from one provider and normalizes to the shared `Record`
schema. Subclass `SourceAdapter` (`conduit/core/schema.py`):

```python
class SourceAdapter:
    capability: str          # e.g. "keywords", "search", "news"
    provider: str            # e.g. "dataforseo"
    async def fetch(self, req: Query) -> list[Record]: ...
    def health(self) -> bool: ...
```

Rules for a good adapter:

- **Fill provenance completely.** Every `Record` you return gets a `Provenance`
  with a real `source`, `url`, `retrieved_at` (ISO), and `content_hash`. Set a
  meaningful `origin_key` so the validator can tell your source apart from
  others — that is what makes the "≥ 2 independent origins" check real.
- **Keys via env, never hardcoded.** Read credentials from environment variables
  (e.g. `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD`) and degrade gracefully —
  `health()` returns `False` when creds are absent, so the harness can route
  around you instead of crashing.
- **Respect the `Query` budget.** Honor `timeout_ms`, `cost_budget`, and `fresh`.
- **No secrets in code, logs, or fixtures.**

## Conventions

- **Python 3.12**, 4-space indent, type hints on all signatures, small functions.
- **`validate_claims.py` stays stdlib-only.** Adapters may use `httpx` (behind
  the `conduit` extra); the core harness stays dependency-free.
- Lint and type-check before you push:
  ```bash
  ruff check .
  mypy conduit/
  pytest        # coverage >= 80%
  ```
- **Tests first.** New behavior ships with a test that failed before your change.

## Submitting

1. Branch, make one logical change, and add/update tests and docs.
2. Run the checks above; make sure a fresh `./install.sh --dest /tmp/ch` works.
3. Open a PR describing **what / why / how**, and call out anything your change
   could *not* verify — the same honesty the harness itself is held to.

By contributing you agree your work is licensed under **Apache-2.0** (see
[LICENSE](LICENSE)).
