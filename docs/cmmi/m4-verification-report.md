# M4 (BL-04-TELEM) — Verification Report

- **Date:** 2026-11-19
- **Milestone:** M4 — Telemetry Ingestion Pipeline & Closed-Loop Auto-Calibration
- **Baseline:** BL-04-TELEM
- **Scope:** M4 exit gate + Phase A audit remediation (AUD-01, AUD-02, AUD-03, AUD-07, AUD-10)

## 1. Worker ingestion benchmark (p99 < 15 ms requirement)

Automated Vitest benchmark (`apps/telemetry-worker/src/benchmark.test.ts`), 1000 samples
against `POST /api/v1/telemetry/event` with mocked R2:

```
p99 ingestion latency (1000 samples): 1.146 ms
```

✅ Requirement met: **p99 = 1.146 ms < 15 ms**.

## 2. Worker functional tests (Vitest)

- `TEST-TEL-001` — event ingestion with valid Bearer token → 202 + R2 write.
- `TEST-TEL-002` — unauthorized → 401; signed batch upload → 202.
- `TEST-TEL-003` — SHA-256 batch signature (missing → 400, invalid → 401, valid → 202).
- `TEST-TEL-004` — `scheduled()` calibration handler persists `M_calib` to D1.
- benchmark — p99 < 15 ms.

Result: **5 passed** (4 functional + 1 benchmark). `tsc --noEmit` → clean.

## 3. Calibration engine (Python)

- `TEST-CAL-001` — Loop 1 (+0.20 M_calib on TTFT > 1500 ms).
- `TEST-CAL-002` — Loop 2 (−20% chunks) + Loop 3 (Semantic Router).
- Sampling: deterministic 5% RAGAS `should_sample_for_eval` (boundaries + determinism).
- Air-gapped parsing: `.jsonl.gz` → telemetry records (`parse_jsonl_gz`).

## 4. Safety gate hardening (AUD-03)

- `TEST-SAFE-001a/b/c` — original grounded/hallucination/missing-citation cases.
- `TEST-SAFE-001d` — citation anti-spoofing (metadata mismatch blocked).
- `TEST-SAFE-001e` — comma decimals + optional spaces.
- `TEST-SAFE-001f` — ranges + extended GMP units.

## 5. Full Python verification

```
pytest --cov=core --cov=api --cov-branch --cov-fail-under=95
  → 19 passed, 99.14% branch coverage (≥95% required)
ruff check .  → All checks passed
mypy --strict core api tests  → Success (11 files)
```

## 6. Database verification

```
vitest run (packages/db)  → 7 passed
tsc --noEmit              → clean
drizzle-kit check         → Everything's fine (zero drift)
```

## 7. Audit remediation traceability

| Audit ID | Change |
| :--- | :--- |
| `AUD-01` | Worker SHA-256 batch signature + `scheduled()` calibration handler (TEST-TEL-003/004) |
| `AUD-02` | CR-001 (reference vector) + RTM/milestones/uptoM4/progress alignment |
| `AUD-03` | Safety gate anti-spoofing + GMP unit/number normalization (TEST-SAFE-001d/e/f) |
| `AUD-07` | Dockerfile + CI JUnit/coverage artifacts + db/worker gates |
| `AUD-10` | OpenAPI contract export + auditSubmissions 21 CFR Part 11 |

## 8. Containerization note

`services/sizing-engine/Dockerfile` written (multi-stage uv image). `docker build`
could not be executed in this environment (no Docker daemon; network blocked), so
the Dockerfile is syntactically validated only. The runtime entrypoint uses
`uvicorn`; `uvicorn` must be added to `pyproject.toml` dependencies + `uv.lock`
regenerated (requires network) before the image serves traffic.
