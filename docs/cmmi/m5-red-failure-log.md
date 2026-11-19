# M5 (BL-05-INTEG) — Phase RED Failure Log

- **Date:** 2026-11-19
- **Milestone:** M5 — Audit Portal UI & Multi-Tier System Integration
- **Baseline target:** BL-05-INTEG
- **Methodology:** Strict TDD — tests written first, run, and confirmed failing before any implementation.

## Result: RED confirmed

| Test file | Expected module | Failure |
|---|---|---|
| `src/lib/schemas.test.ts` | `./schemas` (Zod contract) | `Failed to resolve import "./schemas"` |
| `src/lib/SizeAuditForm.test.ts` | `./SizeAuditForm.svelte` | `Failed to resolve import "./SizeAuditForm.svelte"` |

`vitest run` → **2 failed (no tests collected)**.

## Test IDs written (RED)

| Test ID | Scope | File |
|---|---|---|
| `TEST-UI-001` | multi-step form, mode toggles, TCO/VRAM rendering | `src/lib/SizeAuditForm.test.ts` |
| `TEST-INT-001` | Zod ↔ OpenAPI/Pydantic contract + E2E + batch-upload proxy | `src/lib/schemas.test.ts`, `e2e/audit.spec.ts` |

## Note carried into GREEN

- `TEST-INT-001` (contract) validates the portal Zod request schemas against the
  Pydantic request models exported in `packages/contracts/openapi.json`, and the
  response schema against the `aud-gmao-2026-001` vector.
- `TEST-INT-001` (E2E, Playwright) covers all three deployment modes
  (`AIR_GAPPED_EDGE`, `HYBRID_CONNECTED`, `FULL_CLOUD`) plus the batch-upload proxy.
