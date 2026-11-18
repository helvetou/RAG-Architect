# M4 (BL-04-TELEM) — Phase RED Failure Log

- **Date:** 2026-11-18
- **Milestone:** M4 — Telemetry Ingestion Pipeline & Closed-Loop Auto-Calibration
- **Baseline target:** BL-04-TELEM
- **Methodology:** Strict TDD — tests written first, run, and confirmed failing before any production code.

## Result: RED confirmed

| Test module | Expected symbol | Failure |
|---|---|---|
| `services/sizing-engine/tests/test_calibration.py` | `core.calibration` | `ModuleNotFoundError: No module named 'core.calibration'` |
| `apps/telemetry-worker/src/index.test.ts` | default export `worker` | `TypeError: Cannot read properties of undefined (reading 'fetch')` |

## Test IDs written (RED)

| Test ID | Requirement | File |
|---|---|---|
| `TEST-CAL-001` | `REQ-CAL-001` | `services/sizing-engine/tests/test_calibration.py` |
| `TEST-CAL-002` | `REQ-CAL-002` | `services/sizing-engine/tests/test_calibration.py` |
| `TEST-TEL-001` | worker event ingestion | `apps/telemetry-worker/src/index.test.ts` |
| `TEST-TEL-002` | worker auth + batch upload | `apps/telemetry-worker/src/index.test.ts` |
