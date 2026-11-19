# M6 (BL-06-REL-1.0) — Phase RED Failure Log

- **Date:** 2026-11-19
- **Milestone:** M6 — GMP Qualification (Projet 04), FCA/PCA & Release 1.0
- **Baseline target:** BL-06-REL-1.0
- **Methodology:** Strict TDD — tests written before the qualifying fixtures/manifests.

## Result: RED confirmed (pre-artifact state)

| Test | Expected artifact | Initial failure |
| :--- | :--- | :--- |
| `TEST-GMP-001` (IQ) | golden fixture + `wrangler.toml` + `svelte.config.js` | `FileNotFoundError` on `gmp_projet04_golden.json`; missing `wrangler.toml` |
| `TEST-GMP-002` (OQ) | golden fixture + `core/gate.py` | `FileNotFoundError` on golden fixture |
| `TEST-GMP-003` (PQ) | golden/sizing/calibration | `FileNotFoundError` on golden fixture |
| `TEST-GMP-004` (21 CFR) | `packages/db/tests/gmp.test.ts` | vitest collection error (file missing) |

## GREEN result (no gate code changes required)

- `TEST-GMP-001` — ✅ golden SHA-256 `250e43a4…`, OpenAPI parity, Dockerfile/wrangler.toml/svelte.config.js manifests, Drizzle migration artifacts present.
- `TEST-GMP-002` — ✅ 13/13 golden cases: 6 grounded pass + 7 adversarial blocked (altered temp/duration/torque, missing citation, spoofed citation), exact `SAFETY_BLOCK_MESSAGE`.
- `TEST-GMP-003` — ✅ math ±0.01, `.jsonl.gz` SHA-256 round-trip, 3 calibration loops.
- `TEST-GMP-004` — ✅ 21 CFR append-only (INSERT ok, UPDATE/DELETE raise SQLite ABORT via migration-0001 triggers), deterministic SHA-256.

The GMP units (SIP/CIP `°C`/`bar`/`kPa`/`min`/`L/min`, flange `Nm`/`N·m`/`N.m`/`daNm`/ranges/comma-decimals, cleanroom `µm`/`Pa`) were already covered by the AUD-03 safety-gate hardening — no gate edge-case fix was required.
