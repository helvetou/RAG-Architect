# RAG-Architect for GMAO v3.0 — Audit Summary through M4 (BL-04-TELEM)

- **Document purpose:** consolidated evidence for an external audit of work completed through Milestone 4.
- **Date:** 2026-11-19
- **Governing spec:** `SPEC-GMAO-RAG-ARCH-003` (v3.0.0)
- **Methodology:** CMMI-DEV Level 3 ("Defined") + strict TDD (Red-Green-Refactor)
- **Target deployment:** `smartmaintenance.helveticore.com`

---

## 1. Project overview

RAG-Architect for GMAO v3.0 is a four-tier platform that sizes a
Retrieval-Augmented Generation stack for regulated industrial GMP maintenance
and screens generated answers through a deterministic zero-hallucination gate.

### 1.1 Architecture (4 tiers)

| Tier | Component | Stack |
| :--- | :--- | :--- |
| 1 | Audit Portal & Edge BFF | SvelteKit + Tailwind (Cloudflare Pages) |
| 2 | Sizing Engine | Python 3.12, `uv`, Docker (Fly) |
| 3 | Knowledge Base | Cloudflare D1 (SQLite) via Drizzle ORM |
| 4 | Telemetry Pipeline | Cloudflare Worker + R2 (connected) + air-gapped JSONL batch |

### 1.2 Configuration Management baselines

| Baseline | Milestone | Commit | State |
| :--- | :--- | :--- | :--- |
| `BL-01-INIT` | M1 — Tailoring, RTM, FMEA, monorepo, CI | `f91dc09` | ✅ |
| `BL-02-DATA` | M2 — D1 schema + catalog seed | `104dd83` | ✅ |
| `BL-03-CORE` | M3 — Sizing engine + zero-hallucination gate | `6fc95b6` | ✅ |
| `BL-04-TELEM` | M4 — Telemetry worker + auto-calibration | `489e52e` | ✅ |

Full history (oldest → newest, through Phase A):
`f91dc09` (BL-01-INIT) → `97b661e` (uv.lock) → `ac21693` (pnpm-lock) →
`6ecb9f2` (eslint gate) → `104dd83` (BL-02-DATA) → `6fc95b6` (BL-03-CORE) →
`489e52e` (BL-04-TELEM) → `80ca7d7` (verify scripts) → `ac650bd` (audit package)
→ `5cfdb99` (AUD-01 worker) → `a22906f` (AUD-03 gate) → `11a3dc8` (AUD-07 CI)
→ `c9d3c94` (CR-001/CM) → `8d2706a` (AUD-10) → `fe95f6f` (migration meta) →
HEAD (Phase A exit report). Annotated tags: `BL-01-INIT`, `BL-02-DATA`,
`BL-03-CORE`, `BL-04-TELEM`.

---

## 2. Requirements traceability (RTM)

`docs/cmmi/rtm-v3.md` (Document ID `RTM-GMAO-RAG-ARCH-003`, v3.0.0, baseline
`BL-01-INIT`) freezes 9 requirements, each mapped 1:1 to a test case.

| Requirement | Priority | Test case | Test file | Status |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-DB-001` | P0 | `TEST-DB-001` | `packages/db/tests/schema.test.ts` | ✅ |
| `REQ-MATH-001` | P0 | `TEST-MATH-001` | `services/sizing-engine/tests/test_calculator.py` | ✅ |
| `REQ-MATH-002` | P0 | `TEST-MATH-002` | `services/sizing-engine/tests/test_calculator.py` | ✅ |
| `REQ-MATH-003` | P0 | `TEST-MATH-003` | `services/sizing-engine/tests/test_calculator.py` | ✅ |
| `REQ-FIN-001` | P0 | `TEST-FIN-001` | `services/sizing-engine/tests/test_calculator.py` | ✅ |
| `REQ-API-001` | P0 | `TEST-API-001` | `services/sizing-engine/tests/test_api.py` | ✅ |
| `REQ-SAFE-001` | P0 | `TEST-SAFE-001` | `services/sizing-engine/tests/test_gate.py` | ✅ |
| `REQ-CAL-001` | P1 | `TEST-CAL-001` | `services/sizing-engine/tests/test_calibration.py` | ✅ |
| `REQ-CAL-002` | P1 | `TEST-CAL-002` | `services/sizing-engine/tests/test_calibration.py` | ✅ |

Traceability completeness: **9 / 9 (100%)**. No `REQ-*` exists without a mapped `TEST-*`.

Additional milestone-level tests (beyond the frozen 9 requirements):
`TEST-DB-002`, `TEST-TEL-001`, `TEST-TEL-002` (see §8).

---

## 3. Risk register (FMEA)

`docs/cmmi/fmea-risk-register.md` (Document ID `FMEA-GMAO-RAG-ARCH-003`, v3.0.0,
baseline `BL-01-INIT`).

| Risk | Failure mode | Severity | Mitigation / verification control |
| :--- | :--- | :--- | :--- |
| `RSK-001` | Hallucinated torque/pressure/lockout value | Critical (5) | Zero-hallucination gate (`REQ-SAFE-001`, `gate.py`, `TEST-SAFE-001a/b/c`) |
| `RSK-002` | Edge GPU Out-Of-Memory | High (4) | GQA KV sizing + 20% headroom + Loop-1 scaling (`REQ-MATH-001/003`, `REQ-CAL-001`) |
| `RSK-003` | Air-gapped telemetry loss | Medium (3) | Dual-mode ingestion + `.jsonl.gz` batch upload (`REQ-CAL-002`, `TEST-CAL-002`) |
| `RSK-004` | Python → D1 direct connection failure | High (4) | Edge BFF pattern (catalog snapshot in REST payload; `TEST-API-001`, `TEST-INT-001` at M5) |

---

## 4. M2 — Edge relational persistence & catalog baseline

`packages/db` (Drizzle ORM + Cloudflare D1/SQLite):

- `src/schema.ts` — 4 tables: `hardwareCatalog`, `modelRegistry`,
  `auditSubmissions`, `telemetryCalibration` with GQA attention parameters
  (`qHeadCount`, `kvHeadCount`, `headDim`, `kvCacheBits`) and foreign keys.
- `src/seed.ts` — deterministic catalog seeds.
- `migrations/0000_calm_wallflower.sql` — generated DDL.
- Tests: `tests/schema.test.ts` — `TEST-DB-001` (columns) and `TEST-DB-002`
  (seed + FK enforcement).

---

## 5. M3 — Core sizing engine & zero-hallucination gate

`services/sizing-engine` — Python 3.12, `uv`, FastAPI, Pydantic v2, NumPy.

### 5.1 Canonical reference vector `aud-gmao-2026-001` (formula-exact)

Implemented as the exact §5.1/§5.2/§5.3 formulas (no magic numbers):

| Field | Value | Derivation |
| :--- | :--- | :--- |
| Active streams `B_active` | 14 | `ceil(35 × 0.40)` |
| `weights_vram_gb` | 1.85 | `3.21 × 0.5 × 1.15 = 1.84575` |
| `kv_cache_allocated_gb` | 4.66 | `2 × 14 × 5800 × 28 × 8 × 128 / 1e9 = 4.65633` |
| `estimated_total_child_chunks` | 901 313 | `ceil((85×2500×420 + 450000×150) / 200 × 1.15)` |
| `vector_db_vram_gb` | 1.15 | `901313 × 1024 × 1 × 1.25 / 1e9 = 1.15368` |
| reranker (fixed) | 2.00 | `bge-m3` + `bge-reranker-base` |
| headroom (20%) | 1.30 | `0.20 × (1.84575 + 4.65633)` |
| `total_vram_required_gb` | 10.96 | `1.84575 + 4.65633 + 1.15368 + 2.0 + 1.30042` |
| hardware quantity Q | 2 | `max(2, ceil(10.96 / 24))` (HA, safety-critical) |
| `hardware_capex_usd` | 16 420.00 | `8210 × 2` |
| `energy_and_maint_3yr_usd` | 10 038.24 | `(300×2×730×0.18/1000 + 100×2) × 36` |
| `capex_edge_total_usd` | 26 458.24 | `16420 + 10038.24` |
| `opex_cloud_total_usd` | 54 531.94 | `((5400×3 + 400×15)/1e6 × 35×3×15×30.4 + 451.84) × 36` |
| `net_savings_usd` | 28 073.70 | `54531.94 − 26458.24` |
| `recommended_decision` | `CAPEX_ON_PREM_EDGE` | CAPEX < OPEX |

### 5.2 Modules

- `core/calculator.py` — `compute_active_streams`, `compute_kv_cache_gb`,
  `compute_total_child_chunks`, `compute_vram_allocation`, `compute_3year_tco`.
- `core/gate.py` — `verify_response_safety` with citation regex
  `\[Manual [A-Z0-9-]+,\s*Section [0-9.]+\s*,\s*Page [0-9]+\]` and numeric
  grounding for units `Nm, N·m, bar, psi, kPa, MPa, V, kV, A, mA, Hz, °C, mm`.
  Block message: `"SAFETY GATE BLOCK: Unverified numerical specification or missing citation detected. Consult physical manual directly."`
- `api/routes.py` — `POST /api/v1/size-architecture` (Pydantic v2 request models,
  deterministic response vector).

---

## 6. Reference-vector defect resolution (REQM/CM)

During M3 GREEN verification, three arithmetic defects were found between the
frozen reference vector and the exact §5.1/§5.2/§5.3 formulas, and were resolved
by adopting the **full formula-exact** values (user decision, Option B):

| Value | Before | After (formula-exact) |
| :--- | :--- | :--- |
| Chunks | 550 563 | 901 313 |
| KV cache | 4.55 GB | 4.66 GB |
| VectorDB | 0.70 GB | 1.15 GB |
| VRAM total | 10.38 GB | 10.96 GB |
| TCO CAPEX | 26 460.83 | 26 458.24 |
| TCO OPEX | 54 120.00 | 54 531.94 |

The correction was propagated to `.codewhale/instructions.md` §7, spec §6.1
(+ audit trace + §8.2.1 + §5.3), `milestones.md`, and the RED tests. The
reconciliation is logged in `docs/progress.md`.

---

## 7. M4 — Telemetry ingestion & closed-loop calibration

### 7.1 Auto-calibration engine (`core/calibration.py`)

`evaluate_calibration_loops(RollingTelemetryMetrics) -> CalibrationDecision`
implements the three feedback loops from spec §7.4:

| Loop | Trigger | Action |
| :--- | :--- | :--- |
| Loop 1 | P95 TTFT > 1500 ms **or** peak VRAM > 90% of hardware | `M_calib += 0.20` |
| Loop 2 | context recall < 0.75 **or** P50 reranker < 0.60 | child chunks `−20%` |
| Loop 3 | cloud token spend > baseline +15% | enable `SEMANTIC_ROUTER_SLM_3B` |

### 7.2 Telemetry worker (`apps/telemetry-worker/src/index.ts`)

Cloudflare Worker with Bearer-token authorization and non-blocking
`ctx.waitUntil()` R2 writes:

- `POST /api/v1/telemetry/event` — real-time JSON event (schema validation:
  `client_id`, `timestamp`, `execution_metrics`; 401 unauthorized, 400 invalid,
  202 accepted).
- `POST /api/v1/telemetry/batch-upload` — air-gapped `.jsonl.gz` archive
  (multipart/form-data; 401 unauthorized, 202 accepted).

---

## 8. Test inventory & verification evidence

### 8.1 Test inventory

| Test ID | Requirement | File | Result |
| :--- | :--- | :--- | :--- |
| `TEST-DB-001` | `REQ-DB-001` | `packages/db/tests/schema.test.ts` | ✅ (M2) |
| `TEST-DB-002` | (seed/FK) | `packages/db/tests/schema.test.ts` | ✅ (M2) |
| `TEST-MATH-001` | `REQ-MATH-001` | `tests/test_calculator.py` | ✅ |
| `TEST-MATH-002` | `REQ-MATH-002` | `tests/test_calculator.py` | ✅ |
| `TEST-MATH-003` | `REQ-MATH-003` | `tests/test_calculator.py` | ✅ |
| `TEST-FIN-001` | `REQ-FIN-001` | `tests/test_calculator.py` | ✅ |
| `TEST-SAFE-001a/b/c` | `REQ-SAFE-001` | `tests/test_gate.py` | ✅ |
| `TEST-API-001` | `REQ-API-001` | `tests/test_api.py` | ✅ |
| `TEST-CAL-001` | `REQ-CAL-001` | `tests/test_calibration.py` | ✅ |
| `TEST-CAL-002` | `REQ-CAL-002` | `tests/test_calibration.py` | ✅ |
| `TEST-TEL-001` | worker event | `apps/telemetry-worker/src/index.test.ts` | ✅ |
| `TEST-TEL-002` | worker auth/batch | `apps/telemetry-worker/src/index.test.ts` | ✅ |

### 8.2 Verification results (2026-11-19, Phase A exit gate)

Python sizing engine (`services/sizing-engine`):

- `pytest --cov=core --cov=api --cov-branch --cov-fail-under=95 --junitxml=reports/junit.xml` → **19 passed, 99.14% branch coverage** (≥95% required).
- `ruff check .` → **clean**.
- `mypy --strict core api tests` → **Success (11 files)**.

Telemetry worker (`apps/telemetry-worker`):

- `vitest run` → **5 passed** (4 functional + 1 p99 benchmark).
- `tsc --noEmit` → **clean**.
- Ingestion p99 benchmark → **1.146 ms < 15 ms**.

Database (`packages/db`):

- `vitest run` → **7 passed**.
- `tsc --noEmit` → **clean**.
- `drizzle-kit check` → **zero drift**.

---

## 9. Open items & next steps

- **M5 (BL-05-INTEG)** — SvelteKit audit portal + 4-tier integration
  (`TEST-UI-001`, `TEST-INT-001`). *Not started; awaiting authorization.*
- **M6 (BL-06-REL-1.0)** — GMP qualification (Projet 04), FCA/PCA, release 1.0.
- Internal `.codewhale/verify-*.sh` gate helpers are now tracked (commit `80ca7d7`).
