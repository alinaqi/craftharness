# craftharness

> **Author your agent harness once — run it in Claude Code, claude.ai, ChatGPT, and Codex.**
> maggy's sibling for knowledge work: research, business planning, content, ads, and more.

A **harness** is the deliberate design of three things around any serious task:
**workflow** (steps, branching, retries), **context & tools** (sources, memory, tools per
step), and **quality controls** (how results are checked — grounded, validated
finder ≠ validator, provenance on every claim). craftharness makes that structure reusable.

**Open-core:** the harness is free and works with your own API keys. **uDAPI** — a hosted
data plane behind one MCP server — gives it superpowers out of the box (managed keys +
provenance + caching), so you don't wire a dozen data providers yourself.

## Status

Early. The build is specified in **[SPEC.md](SPEC.md)**; architecture, security, and
validation contracts in the planning docs. License: **Apache-2.0**.

## How it reaches every surface (the design in one line)

Two open standards cover all four tools:
- **Agent Skills** (`SKILL.md`) — the workflow/context/quality layer, read by Claude Code,
  claude.ai, Codex, Cursor, and more.
- **One remote MCP server (uDAPI)** — the data/tools layer, reaching Claude Code, claude.ai
  Connectors, ChatGPT Apps/Plugins, and Codex from a single deployment.

A `craftharness init` / `sync` compiler authors these once and emits `.claude/`, `AGENTS.md`,
`.codex/`, and a claude.ai `.zip` from one source.

## Repo layout

```
harness/     # the OSS harness — skills (research-spine + deliverables), quality hooks
conduit/     # uDAPI — the data plane (FastAPI gateway, adapters, contracts)
docs/        # contracts, skill/adapter authoring guides
examples/    # runnable, key-free examples
SPEC.md      # what we're building
```

## License

Apache-2.0 — see [LICENSE](LICENSE).
