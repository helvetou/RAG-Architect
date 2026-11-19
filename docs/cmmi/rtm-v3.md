# Bidirectional Requirements Traceability Matrix (RTM) — v3

| Attribute | Value |
| :--- | :--- |
| **Document ID** | `RTM-GMAO-RAG-ARCH-003` |
| **Version** | `v3.0.0` |
| **Baseline** | `BL-01-INIT` |
| **Governing Spec** | `SPEC-GMAO-RAG-ARCH-003` (v3.0.0) |
| **Process Areas** | RD (Requirements Development), REQM (Requirements Management) |
| **Traceability Guarantee** | 100 % — every `REQ-*` SHALL be mapped to exactly one `TEST-*` |

This matrix locks the bidirectional traceability between formal requirements (`REQ-*`), their design sections, the source-code modules that will implement them, and the mandatory TDD test cases (`TEST-*`). Under CMMI-DEV Level 3 `VER`, no production code may be written before its corresponding failing test is committed.

## Traceability Matrix

| Requirement ID | Category | Priority | Design Section | Source Code Module | TDD Test Case ID | Test Suite File |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `REQ-DB-001` | Data Schema | P0 | Section 4.1 | `packages/db/src/schema.ts` | `TEST-DB-001` | `packages/db/tests/schema.test.ts` |
| `REQ-MATH-001` | Sizing Math | P0 | Section 5.1 | `services/sizing-engine/core/calculator.py` | `TEST-MATH-001` | `services/sizing-engine/tests/test_calculator.py` |
| `REQ-MATH-002` | Sizing Math | P0 | Section 5.2 | `services/sizing-engine/core/calculator.py` | `TEST-MATH-002` | `services/sizing-engine/tests/test_calculator.py` |
| `REQ-MATH-003` | Sizing Math | P0 | Section 5.2 | `services/sizing-engine/core/calculator.py` | `TEST-MATH-003` | `services/sizing-engine/tests/test_calculator.py` |
| `REQ-FIN-001` | Financial TCO | P0 | Section 5.3 | `services/sizing-engine/core/calculator.py` | `TEST-FIN-001` | `services/sizing-engine/tests/test_calculator.py` |
| `REQ-API-001` | Interface | P0 | Section 6.1 | `services/sizing-engine/api/routes.py` | `TEST-API-001` | `services/sizing-engine/tests/test_api.py` |
| `REQ-SAFE-001` | Safety Gate | P0 | Section 7.3 | `services/sizing-engine/core/gate.py` | `TEST-SAFE-001` | `services/sizing-engine/tests/test_gate.py` |
| `REQ-CAL-001` | Calibration | P1 | Section 7.4 | `services/sizing-engine/core/calibration.py` | `TEST-CAL-001` | `services/sizing-engine/tests/test_calibration.py` |
| `REQ-CAL-002` | Calibration | P1 | Section 6.2 | `apps/portal/src/routes/api/batch-upload/+server.ts` | `TEST-CAL-002` | `services/sizing-engine/tests/test_calibration.py` |

## Requirements Catalog (frozen in M1)

| Requirement ID | Requirement Specification |
| :--- | :--- |
| `REQ-DB-001` | The relational schema (`packages/db/src/schema.ts`) SHALL define `hardwareCatalog`, `modelRegistry`, `auditSubmissions`, and `telemetryCalibration` with explicit GQA attention head parameters (`qHeadCount`, `kvHeadCount`, `headDim`, `kvCacheBits`). |
| `REQ-MATH-001` | The sizing engine SHALL compute active concurrent streams as `B_active = ceil(N_techs × R_peak)` and KV Cache memory in bytes using exact GQA dimensions and bit-width precision. |
| `REQ-MATH-002` | The sizing engine SHALL convert PDF manual volume (GB) and historical work orders into total indexed child chunks (`N_chunks`) accounting for a 15 % sliding-window overlap (1.15). |
| `REQ-MATH-003` | The sizing engine SHALL calculate total required GPU VRAM as the sum of Model Weights, KV Cache, VectorDB Index, Resident Reranker (2.0 GB), and a 20 % Safety Headroom on Weights + KV Cache, scaled by `M_calib`. |
| `REQ-FIN-001` | The sizing engine SHALL compute a 36-month CAPEX TCO (hardware acquisition + TDP electricity + monthly maintenance) versus 36-month Cloud OPEX TCO (token volume pricing + managed vector hosting). |
| `REQ-API-001` | The `POST /api/v1/size-architecture` endpoint SHALL validate inputs via Pydantic v2 and return deterministic sizing, RAG configuration, and TCO projections matching the baseline verification vector within ±0.01 precision. |
| `REQ-SAFE-001` | The Zero-Hallucination Gate (`gate.py`) SHALL synchronously inspect generated responses and block any response missing an explicit `[Manual ID, Section, Page]` citation or containing physical quantities (`Nm, N·m, N.m, daNm, bar, psi, Pa, kPa, MPa, V, kV, A, mA, Hz, °C, mm, µm, rpm, min, L/min, ppm, %`) absent from the retrieved parent chunks. |
| `REQ-CAL-001` | The calibration processor (`calibration.py`) SHALL increment `computeScalingMultiplier` (`M_calib`) by +0.20 when 7-day rolling P95 TTFT exceeds 1500 ms or peak VRAM exceeds 90 % of hardware capacity. |
| `REQ-CAL-002` | The calibration processor SHALL support dual-mode ingestion: real-time Cloudflare Worker events (`HYBRID_CONNECTED`/`FULL_CLOUD`) and `.jsonl.gz` batch uploads (`AIR_GAPPED_EDGE`), evaluating async RAGAS recall on a 5 % sample. |

## Traceability Status

- Requirements frozen: `REQ-DB-001` through `REQ-CAL-002` (9 requirements).
- Test mapping completeness: 9 / 9 (100 %).
- No `REQ-*` exists without a mapped `TEST-*`.
