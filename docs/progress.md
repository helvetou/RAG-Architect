# RAG-Architect for GMAO v3.0 — Progress & Next Steps

- **Repository:** `/media/malek/DONNEES/pydev/RAG-Architect`
- **Branch:** `main` @ `104dd83` (5 commits)
- **Status date:** 2026-11-18

## 1. Goal (restated)

Deliver **RAG-Architect for GMAO v3.0**, a CMMI-DEV Level 3 ("Defined"),
strict-TDD, 4-tier system for pharmaceutical GMP maintenance:

1. Audit Portal & Edge BFF — SvelteKit + Tailwind (Cloudflare Pages)
2. Sizing Engine — Python 3.12 / uv / Docker (Fly)
3. Knowledge Base — Cloudflare D1 (SQLite) via Drizzle ORM
4. Telemetry Pipeline — Cloudflare Worker + R2 (connected) and air-gapped JSONL batch mode

Success = all six milestones (M1–M6) closed, all six CM baselines
(BL-01…BL-06) signed off, 100% RTM traceability, ≥95% branch coverage on
`services/sizing-engine/core/`, and a clean GMP qualification (Projet 04)
with FCA/PCA and BL-06-REL-1.0 release.

## 2. The Plan (M1–M6 roadmap)

| Milestone | Deliverable | Baseline |
|---|---|---|
| M1 | Tailoring, RTM, FMEA, monorepo + CI | BL-01-INIT |
| M2 | D1 schema + catalog seed (Drizzle) | BL-02-DATA |
| M3 | Python sizing engine + zero-hallucination gate | BL-03-CORE |
| M4 | Telemetry worker + 3-loop auto-calibration | BL-04-TELEM |
| M5 | SvelteKit portal + 4-tier integration | BL-05-INTEG |
| M6 | GMP qualification, FCA/PCA, release 1.0 | BL-06-REL-1.0 |

Critical path: M1 → M2 → {M3 ∥ M4 ingestion} → M5 → M6.

## 3. Done so far

### M1 — BL-01-INIT (complete)
- Monorepo skeleton: `apps/portal`, `apps/telemetry-worker`,
  `services/sizing-engine`, `packages/db`, `pnpm` + `uv` workspaces.
- Bidirectional RTM frozen: `docs/cmmi/rtm-v3.md` — 9 `REQ-*` mapped 1:1 to 9 `TEST-*`.
- FMEA risk register: `docs/cmmi/fmea-risk-register.md` (RSK-001…004).
- Governance docs: `codewhaleSpecIntepretation.md`, `milestones.md`,
  `.codewhale/instructions.md`.
- CI quality gate: `.github/workflows/ci-cmmi-gate.yml`
  (ruff/mypy/pytest, eslint/tsc, RTM presence, coverage ≥95%).

### M2 — BL-02-DATA (complete)
- `packages/db/src/schema.ts` — 4 Drizzle tables
  (`hardwareCatalog`, `modelRegistry`, `auditSubmissions`,
  `telemetryCalibration`) with GQA params + FKs.
- `packages/db/src/seed.ts` — deterministic catalog seeds.
- `packages/db/migrations/0000_calm_wallflower.sql` — generated DDL.
- Tests: `packages/db/tests/schema.test.ts` — `TEST-DB-001` (columns) and
  `TEST-DB-002` (seed + FK enforcement) pass.

### M3 — BL-03-CORE (complete)
- `core/calculator.py`, `core/gate.py`, `api/routes.py` (RED → GREEN → REFACTOR).
- `tests/test_calculator.py`, `test_gate.py`, `test_api.py` — `TEST-MATH-001/002/003`,
  `TEST-FIN-001`, `TEST-SAFE-001`, `TEST-API-001`.
- Canonical `aud-gmao-2026-001` vector: chunks 901 313, KV 4.66, vectorDB 1.15,
  VRAM 10.96, CAPEX 26 458.24 vs OPEX 54 531.94.
- pytest 8 passed @ 99.39% branch coverage; ruff + mypy --strict clean.

### M4 — BL-04-TELEM (complete)
- `core/calibration.py` — 3-loop auto-calibration (Loop 1/2/3).
- `apps/telemetry-worker/src/index.ts` — event + batch-upload endpoints with
  Bearer auth + R2 `ctx.waitUntil()` writes.
- `tests/test_calibration.py` — `TEST-CAL-001`, `TEST-CAL-002`.
- `apps/telemetry-worker/src/index.test.ts` — `TEST-TEL-001`, `TEST-TEL-002`.
- pytest 13 passed @ 99.50% branch coverage; vitest 2 passed; tsc + ruff + mypy clean.

## 4. Next up — M5 (BL-05-INTEG)

**Entry criteria:** BL-02-DATA, BL-03-CORE, and BL-04-TELEM signed off.

TDD sequence:

1. **RED** — `apps/portal` Vitest component + Playwright E2E tests
   (`TEST-UI-001`, `TEST-INT-001`) asserting form validation, air-gapped
   constraint toggles, and CAPEX-vs-OPEX chart rendering.
2. **GREEN** — `+page.svelte` multi-step qualification UI, server-side proxy
   actions to D1 (packages/db) and the sizing engine, TCO/VRAM breakdown views.
3. **REFACTOR** — WCAG AA contrast for factory tablets, Panasonic Toughbook G2
   responsive layout.

**Exit criteria (BL-05-INTEG):** zero contract mismatch between Zod/Drizzle and
Pydantic schemas; Playwright suite green across AIR_GAPPED_EDGE /
HYBRID_CONNECTED / FULL_CLOUD.

## 5. Open items / decisions

- **REQM/CM defect resolution — RESOLVED (2026-11-18):** the `aud-gmao-2026-001`
  reference vector carried three arithmetic defects vs the exact §5.1/§5.2/§5.3
  formulas — chunks `550 563 → 901 313`, KV cache `4.55 → 4.66 GB`
  (`2×14×5800×28×8×128 = 4.6563e9`), and TCO (`energy_and_maint 10 040.83 →
  10 038.24`, cloud OPEX `54 120.00 → 54 531.94`). Per Option B (full
  formula-exact), the canonical vector is now: chunks `901 313`, weights `1.85`,
  KV `4.66`, vectorDB `1.15`, VRAM total `10.96`, CAPEX `26 458.24` vs OPEX
  `54 531.94` → `CAPEX_ON_PREM_EDGE`. Applied in `.codewhale/instructions.md`
  §7, spec §6.1 (+audit trace + §8.2.1), and the RED tests.
- **Test-ID taxonomy mismatch — RESOLVED (2026-11-16):** `milestones.md` M3/M4
  now reference the RTM test IDs (`TEST-MATH-001…003`, `TEST-FIN-001`,
  `TEST-SAFE-001`, `TEST-API-001`, `TEST-CAL-001/002`). Remaining `TEST-TEL-*`,
  `TEST-UI-*`, `TEST-INT-*`, `TEST-GMP-*` are milestone-level tests beyond the
  frozen 9 requirements (no `REQ-*` conflict) and are retained.
- **5 untracked files** in the working tree — inspect and decide commit vs ignore.
- **M4 note — RESOLVED (2026-11-18):** `REQ-CAL-002` dual-mode ingestion is
  implemented and verified in `core/calibration.py` (TEST-CAL-001/002) and the
  telemetry worker (TEST-TEL-001/002). The RTM's portal-route mapping for the
  batch-upload endpoint remains for the M5 portal proxy.


## 6. Immediate next actions (checklist)

- [x] M3 (BL-03-CORE): RED → GREEN → REFACTOR — pytest 8/8, ruff, mypy clean.
- [x] M4 (BL-04-TELEM): RED → GREEN — calibration.py + telemetry worker,
      pytest 13/13 @ 99.50%, vitest 2/2, tsc/ruff/mypy clean.
- [ ] Commit M4 work.
- [ ] Review the 5 untracked `.codewhale/verify-*.sh` files.
- [ ] Start M5 (BL-05-INTEG): portal UI + 4-tier integration (`TEST-UI-001`, `TEST-INT-001`).
