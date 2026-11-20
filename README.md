# RAG-Architect for GMAO v3.0

A **CMMI-DEV Level 3 ("Defined")** platform that sizes a Retrieval-Augmented
Generation (RAG) stack for industrial GMP maintenance and gates generated
answers with a deterministic zero-hallucination check. Development follows
strict **Test-Driven Development (Red-Green-Refactor)**.

## Architecture (4 tiers)

| Tier | Component | Stack |
| :--- | :--- | :--- |
| 1 | Audit Portal & Edge BFF | SvelteKit + Tailwind (Cloudflare Pages) |
| 2 | Sizing Engine | Python 3.12, `uv`, Docker (Fly) |
| 3 | Knowledge Base | Cloudflare D1 (SQLite) via Drizzle ORM |
| 4 | Telemetry Pipeline | Cloudflare Worker + R2; air-gapped JSONL batch |

## Milestone status

| Milestone | Baseline | State |
| :--- | :--- | :--- |
| M1 — Tailoring, RTM, monorepo, CI | `BL-01-INIT` | ✅ Complete |
| M2 — D1 schema + catalog seed | `BL-02-DATA` | ✅ Complete |
| M3 — Sizing engine + safety gate | `BL-03-CORE` | ✅ Complete |
| M4 — Telemetry worker + calibration | `BL-04-TELEM` | ✅ Complete |
| M5 — Portal + 4-tier integration | `BL-05-INTEG` | ✅ Complete |
| M6 — GMP qualification, FCA/PCA | `BL-06-REL-1.0` | ✅ Complete |

## Repository layout

- `apps/portal/` — SvelteKit audit portal (M5)
- `apps/telemetry-worker/` — Cloudflare Worker telemetry ingestion (M4)
- `services/sizing-engine/` — Python sizing + calibration engine (M3/M4)
- `packages/db/` — Drizzle ORM + D1 schema/seed/migrations (M2)
- `docs/cmmi/` — RTM, FMEA, RED failure logs
- `uptoM4.md` — external audit summary through M4

## Verification

Python sizing engine (`services/sizing-engine`):

```bash
uv run pytest --cov=core --cov=api --cov-fail-under=95 --cov-branch
uv run ruff check .
uv run mypy --strict core api tests
```

Telemetry worker (`apps/telemetry-worker`):

```bash
pnpm --filter @rag-architect/telemetry-worker test
pnpm --filter @rag-architect/telemetry-worker run check
```

Database (`packages/db`):

```bash
pnpm --filter @rag-architect/db test
pnpm --filter @rag-architect/db run check
```

## Deployment (Cloudflare Pages → Fly + D1)

Target domain: `rag-architect.helveticore.com` (independent, isolated deployment).

| Service | Target |
| :--- | :--- |
| Portal (`rag-architect-portal`) | Cloudflare Pages — config in `apps/portal/wrangler.toml` |
| Sizing Engine (`rag-architect-sizing`) | Fly.io — `https://rag-architect-sizing.fly.dev` |
| Telemetry Worker | Cloudflare Workers — `https://telemetry-worker.haroudm.workers.dev` |
| D1 (`rag-architect-db`) | binding `DB`, id `ba6b952e-1d76-4201-a650-aba9df3d0307` |

### Environment variables / bindings

- `DB` (D1 binding) — `rag-architect-db`, configured for **production and preview**.
- `SIZING_ENGINE_URL` — `https://rag-architect-sizing.fly.dev` (normalized by `apps/portal/src/lib/config.ts`).
- `TELEMETRY_WORKER_URL` — `https://telemetry-worker.haroudm.workers.dev`.
- `AUTH_TOKEN` — **secret** shared (identical value) between `telemetry-worker` and
  `rag-architect-portal`, in **production and preview**; set via Cloudflare
  secrets / `.dev.vars`, never committed to `wrangler.toml`.

### Ops notes

- **`502 Sizing engine unavailable` fix:** an environment value carrying a Markdown
  link (`[url](url)`) was previously passed verbatim as the fetch URL.
  `normalizeUrl()` in `config.ts` strips Markdown wrappers, angle brackets and
  trailing slashes, and falls back to the default on malformed values
  (unit-tested in `config.test.ts`).
- **21 CFR Part 11:** `POST /api/audit` inserts into `audit_submissions` (append-only).
  `UPDATE`/`DELETE` are rejected by D1 triggers (`SQLITE_CONSTRAINT_TRIGGER`,
  `audit_submissions is append-only`) — covered locally by `packages/db/tests/gmp.test.ts`
  and validated end-to-end against D1.

## Governance documents

- `technical_specification_rag_architect_for_gmao_v3_0_cmmi_l3_tdd.md` — governing spec (v3.0)
- `docs/cmmi/rtm-v3.md` — bidirectional RTM (9 `REQ-*` → 9 `TEST-*`)
- `docs/cmmi/fmea-risk-register.md` — FMEA (`RSK-001…004`)
- `milestones.md` — M1–M6 plan with entry/exit criteria
- `uptoM4.md` — audit summary through M4
