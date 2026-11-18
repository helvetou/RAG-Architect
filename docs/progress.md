# RAG-Architect for GMAO v3.0 — Progress & Next Steps

- **Repository:** `/media/malek/DONNEES/pydev/RAG-Architect`
- **Branch:** `main` @ `104dd83` (5 commits)
- **Status date:** 2026-11-16

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

## 4. Next up — M3 (BL-03-CORE)

**Entry criterion:** BL-02-DATA signed off (schema committed; formal PPQA
sign-off to be recorded).

TDD sequence (no production code before failing tests):

1. **RED** — commit failing suite referencing `REQ-*`/`TEST-*`:
   - `services/sizing-engine/tests/test_calculator.py`
     → `TEST-MATH-001/002/003`, `TEST-FIN-001`
   - `services/sizing-engine/tests/test_gate.py`
     → `TEST-SAFE-001`
   - `services/sizing-engine/tests/test_api.py`
     → `TEST-API-001`
   - Run `uv run pytest` and record the failure log (ImportError/AssertionError).
2. **GREEN** — implement the minimal deterministic code:
   - `core/calculator.py` — B_active = ceil(35 × 0.40) = 14; KV 4.66 GB;
     weights 1.85 GB; vectorDB 1.15 GB; reranker 2.00 GB; VRAM total 10.96 GB;
     chunks 901 313; 3-yr TCO CAPEX 26 458.24 USD vs OPEX cloud 54 531.94 USD
     → decision `CAPEX_ON_PREM_EDGE`.
   - `core/gate.py` — block any response lacking `[Manual ID, Section, Page]`
     or containing an unverified physical quantity (Nm, bar, psi, V, A, °C);
     message: `"SAFETY GATE BLOCK: Unverified numerical specification or
     missing citation detected. Consult physical manual directly."`
   - `api/routes.py` — `POST /api/v1/size-architecture` with Pydantic v2.
3. **REFACTOR** — NumPy vectorization, `mypy --strict`, ruff clean.

**Exit criteria (BL-03-CORE):** 100% pass on `TEST-MATH-*`, `TEST-FIN-*`,
`TEST-SAFE-*`, `TEST-API-*`; ≥95% branch coverage; exact match with the
reference vector `aud-gmao-2026-001`.

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
- **M4 note:** `REQ-CAL-002` is traced to a portal route
  (`apps/portal/src/routes/api/batch-upload/+server.ts`) but tested in
  `services/sizing-engine/tests/test_calibration.py` — verify that cross-tier
  mapping is intended when M4 starts.


## 6. Immediate next actions (checklist)

- [x] Reconcile the M3 reference-vector numbers (single source of truth).
- [x] Write M3 RED test suite (`test_calculator.py`, `test_gate.py`,
      `test_api.py`) and record the failing run.
- [ ] Review the 5 untracked files.
- [x] Then GREEN → REFACTOR → `uv run pytest --cov=core --cov=api
      --cov-fail-under=95 --cov-branch`, `ruff check`, `mypy --strict`.
