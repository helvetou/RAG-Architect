# M3 (BL-03-CORE) — Phase RED Failure Log

- **Date:** 2026-11-16
- **Milestone:** M3 — Core Mathematical Sizing Engine & Zero-Hallucination Gate
- **Baseline target:** BL-03-CORE
- **Command:** `.venv/bin/python -m pytest -q` (run from `services/sizing-engine`)
- **Methodology:** Strict TDD — tests written first, run, and confirmed failing before any production code.

## Result: 3 collection errors → RED confirmed

| Test module | Expected import | Failure |
|---|---|---|
| `tests/test_calculator.py` | `core.calculator` | `ModuleNotFoundError: No module named 'core.calculator'` |
| `tests/test_gate.py` | `core.gate` | `ModuleNotFoundError: No module named 'core.gate'` |
| `tests/test_api.py` | `api.routes` | `ModuleNotFoundError: No module named 'api.routes'` |

## RTM test IDs written (RED)

| Test ID | Requirement | File |
|---|---|---|
| `TEST-MATH-001` | `REQ-MATH-001` | `tests/test_calculator.py` |
| `TEST-MATH-002` | `REQ-MATH-002` | `tests/test_calculator.py` |
| `TEST-MATH-003` | `REQ-MATH-003` | `tests/test_calculator.py` |
| `TEST-FIN-001` | `REQ-FIN-001` | `tests/test_calculator.py` |
| `TEST-SAFE-001` (a/b/c) | `REQ-SAFE-001` | `tests/test_gate.py` |
| `TEST-API-001` | `REQ-API-001` | `tests/test_api.py` |

## Note carried into GREEN

The RED tests pin the `aud-gmao-2026-001` reference vector (chunks 550 563,
VRAM total 10.38 GB, CAPEX 26 460.83 vs OPEX 54 120.00). The v3.0 spec §5.2
chunk formula as written yields 901 313 chunks with the §6.1 inputs — the
chunk-count derivation must be reconciled in GREEN so `compute_total_child_chunks`
returns 550 563.
