# Change Request CR-001 — Reference Vector `aud-gmao-2026-001` (Formula-Exact Reconciliation)

| Attribute | Value |
| :--- | :--- |
| **Change Request ID** | `CR-001` |
| **Subject** | Migrate the `aud-gmao-2026-001` verification vector to the exact §5.1/§5.2/§5.3 formula values |
| **Origin** | M3 GREEN verification (TDD) — arithmetic discrepancy between the frozen vector and the governing formulas |
| **Decision** | Option B — full formula-exact (no magic numbers / special-case constants) |
| **Status** | ✅ Approved & implemented (2026-11-18) |
| **Governance** | REQM (Requirements Management) / CM (Configuration Management) |

## 1. Problem statement

While implementing `core/calculator.py` during M3 GREEN, three arithmetic defects were
found between the frozen `aud-gmao-2026-001` vector and the exact formulas in the
governing spec:

1. **Chunks** — §5.2 with the §6.1 inputs yields `901 313`, the vector stated `550 563`.
2. **KV cache** — §5.1 with the reference model yields
   `2 × 14 × 5800 × 28 × 8 × 128 × 1 / 1e9 = 4.65633 GB`, the vector stated `4.54713` (`4.55`).
3. **TCO** — §5.3 yields energy+maint `10 038.24` and cloud OPEX `54 531.94`; the vector
   stated `10 040.83` and `54 120.00`.

## 2. Decision

Adopt the **full formula-exact** values (Option B), so that every function in
`core/calculator.py` implements the exact §5.1/§5.2/§5.3 formulas with no contrived
constants or magic numbers.

## 3. Before → after

| Value | Before | After |
| :--- | :--- | :--- |
| `estimated_total_child_chunks` | 550 563 | **901 313** |
| `weights_vram_gb` | 1.85 | 1.85 (unchanged) |
| `kv_cache_allocated_gb` | 4.55 | **4.66** |
| `vector_db_vram_gb` | 0.70 | **1.15** |
| `total_vram_required_gb` | 10.38 | **10.96** |
| `hardware_capex_usd` | 16 420.00 | 16 420.00 (unchanged) |
| `energy_and_maint_3yr_usd` | 10 040.83 | **10 038.24** |
| `capex_edge_total_usd` | 26 460.83 | **26 458.24** |
| `opex_cloud_total_usd` | 54 120.00 | **54 531.94** |
| `net_savings_usd` | 27 659.17 | **28 073.70** |
| `recommended_decision` | `CAPEX_ON_PREM_EDGE` | `CAPEX_ON_PREM_EDGE` (unchanged) |

## 4. Impact analysis

| Baseline | Impact |
| :--- | :--- |
| `BL-01-INIT` | None — RTM/FMEA IDs and structure unchanged. |
| `BL-02-DATA` | None — D1 schema and seed data unchanged (hardware Q = 2 is unaffected). |
| `BL-03-CORE` | §6.1 response vector, §6.1 audit trace, §8.2.1 test snippets, §5.3 OPEX note, `.codewhale/instructions.md` §7, `milestones.md`, and the RED tests updated. |

## 5. Affected artifacts

- `.codewhale/instructions.md` §7
- `technical_specification_rag_architect_for_gmao_v3_0_cmmi_l3_tdd.md` (§5.3, §6.1, §8.2.1)
- `milestones.md` (M3)
- `services/sizing-engine/tests/test_calculator.py`, `test_api.py`
- `docs/progress.md`, `uptoM4.md`

## 6. Verification

- `pytest --cov=core --cov=api --cov-fail-under=95 --cov-branch` → 8/8 (M3) green.
- Reference vector re-derived and committed via `feat: BL-03-CORE` (`6fc95b6`).
