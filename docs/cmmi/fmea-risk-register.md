# FMEA Risk Register — RAG-Architect for GMAO (v3.0)

| Attribute | Value |
| :--- | :--- |
| **Document ID** | `FMEA-GMAO-RAG-ARCH-003` |
| **Version** | `v3.0.0` |
| **Baseline** | `BL-01-INIT` |
| **Process Area** | RSKM (Risk Management) |
| **Method** | Failure Mode and Effects Analysis (FMEA) |

## Risk Register

| Risk ID | Failure Mode | Operational Impact | Severity | Likelihood | Mitigation & TDD Verification Control |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `RSK-001` | Hallucinated torque, pressure, or lockout value presented to technician | Physical injury, equipment damage, or GMP batch rejection | Critical (5) | Low (1) | Deterministic regex grounding check (`REQ-SAFE-001`) enforced by `gate.py` and verified by `TEST-SAFE-001b`. |
| `RSK-002` | Edge Server GPU Out-Of-Memory (OOM) during shift handover concurrency spike | Service unavailability during critical plant downtime | High (4) | Medium (2) | Explicit GQA KV Cache sizing (`REQ-MATH-001`), 20 % headroom buffer, plus closed-loop +20 % scaling (`REQ-CAL-001` / `TEST-CAL-001`). |
| `RSK-003` | Telemetry pipeline failure in Air-Gapped factory environments | Loss of calibration visibility and drift in retrieval recall | Medium (3) | Low (1) | Dual-mode ingestion with local `.jsonl.gz` ring buffer and `POST /api/v1/telemetry/batch-upload` (`REQ-CAL-002`). |
| `RSK-004` | Direct TCP connection failure from external Python container to Cloudflare D1 | Sizing engine unable to read hardware/model catalogs | High (4) | Low (1) | Edge BFF pattern: SvelteKit server routes query D1 locally on Cloudflare Edge and pass catalog snapshot in REST payload. |

## Mitigation Plans

### RSK-001 — Hallucinated physical quantity

- **Control**: the Zero-Hallucination Gate synchronously screens every generated response before presentation.
- **Mechanism**: citation regex `\[Manual [A-Z0-9-]+,\s*Section [0-9.]+\s*,\s*Page [0-9]+\]` plus numerical grounding verification for units `Nm, N·m, bar, psi, kPa, MPa, V, kV, A, mA, Hz, °C, mm`.
- **Verification**: `TEST-SAFE-001a` (grounded response passes), `TEST-SAFE-001b` (hallucinated torque blocked), `TEST-SAFE-001c` (missing citation blocked).

### RSK-002 — Edge GPU Out-Of-Memory

- **Control**: deterministic GQA KV Cache sizing, 20 % headroom on Weights + KV Cache, and closed-loop scaling.
- **Mechanism**: `B_active = ceil(N_techs × R_peak)`; `VRAM_Total = (Weights + KV Cache + VectorDB + Reranker + Headroom) × M_calib`.
- **Verification**: `TEST-MATH-001`, `TEST-MATH-003`, and `TEST-CAL-001` (Loop 1 +0.20 scaling).

### RSK-003 — Air-gapped telemetry loss

- **Control**: dual-mode ingestion with local buffering and signed batch upload.
- **Mechanism**: local SQLite/JSONL ring buffer on the factory Edge server; periodic export of signed `.jsonl.gz` bundles.
- **Verification**: `TEST-CAL-002` (batch ingestion and async RAGAS 5 % sampling).

### RSK-004 — Python → D1 direct connection failure

- **Control**: Edge Backend-for-Frontend (BFF) pattern.
- **Mechanism**: SvelteKit server routes query D1 on the Cloudflare Edge and pass the catalog snapshot in the REST payload to the Python Sizing Engine.
- **Verification**: contract tests for the REST payload (`TEST-API-001`) and BFF integration tests (`TEST-INT-001`, M5).
