# PV de Qualification Logicielle — Projet 04 (IQ / OQ / PQ)

| Attribute | Value |
| :--- | :--- |
| **Document ID** | `PVQ-GMAO-RAG-ARCH-003` |
| **Version** | `v1.0.0` |
| **Project** | Projet 04 — Assistant RAG pour procédures SOP / manuels GMP |
| **Governing spec** | `SPEC-GMAO-RAG-ARCH-003` (v3.0.0) |
| **Date** | 2026-11-19 |
| **Method** | CMMI-DEV Level 3 `VAL` / `VER`, strict TDD |

## 1. Objet

Qualification logicielle du RAG-Architect GMAO contre le jeu de données Golden
Projet 04 (stérilisation SIP/CIP, couples de serrage brides, habillage salle
blanche), avec vérification 21 CFR Part 11 et zero-hallucination (`RSK-001`).

## 2. Installation Qualification (IQ) — `TEST-GMP-001`

| Vérification | Résultat |
| :--- | :--- |
| Intégrité SHA-256 du jeu Golden | ✅ `250e43a47dae2d614e0459a70e6d7775fcf4261c92e9a9c815a200d36d0a2e96` |
| Parité OpenAPI ↔ FastAPI + Zod | ✅ `packages/contracts/openapi.json` (`/api/v1/size-architecture`, `SizeRequest`) |
| Manifest Docker (sizing-engine) | ✅ `FROM` + `uvicorn` présents |
| Manifest Worker (`wrangler.toml`) | ✅ bindings `TELEMETRY_BUCKET` + `crons` |
| Manifest Portal (`svelte.config.js`) | ✅ `adapter-cloudflare` |
| Zéro-drift Drizzle | ✅ migrations `0000`/`0001` + `meta/_journal.json` présents |

## 3. Operational Qualification (OQ) — `TEST-GMP-002` (100 % factual accuracy)

13 cas Golden exécutés contre `core/gate.py` :

- **6 cas ancrés** (SIP 121.5 °C/30 min/2.1 bar/120 L/min, CIP 85 °C/300 kPa, plage
  10-15 Nm, décimales `12,5 daNm`, `N·m`/`N.m`, cleanroom `0.5 µm`/`15 Pa`) → **tous PASS**.
- **7 cas adversariaux** (température 131.5 °C vs 121.5 °C, durée 45 min vs 30 min,
  couple 20-25 Nm vs 10-15 Nm, citation spoofée `FLG-99`, citations manquantes ×2,
  pression 30 Pa vs 15 Pa) → **tous BLOQUÉS** avec le message exact
  `SAFETY GATE BLOCK: Unverified numerical specification or missing citation detected. Consult physical manual directly.`

**Zéro faux négatif sur `RSK-001`.**

## 4. Performance Qualification (PQ) — `TEST-GMP-003`

| Vérification | Résultat |
| :--- | :--- |
| Exactitude mathématique ±0.01 | ✅ VRAM 10.96 GB, CAPEX 26 458.24, OPEX 54 531.94, `CAPEX_ON_PREM_EDGE` |
| Flux air-gapped `.jsonl.gz` (SHA-256) | ✅ round-trip `parse_jsonl_gz` + digest déterministe |
| 3 boucles de calibration | ✅ Loop 1 (+0.20), Loop 2 (−20% chunks), Loop 3 (Semantic Router) |
| Latence Worker p99 < 15 ms | ✅ 1.146 ms (benchmark `apps/telemetry-worker/src/benchmark.test.ts`) |

## 5. 21 CFR Part 11 — `TEST-GMP-004`

- Insertion d'un enregistrement d'audit complet (`actorId`, `inputPayloadSha256`,
  `outputPayloadSha256`, `specVersion`, `modelVersion`, timestamp UTC) → ✅.
- Reproductibilité déterministe des empreintes SHA-256 → ✅.
- Append-only : tout `UPDATE` et `DELETE` lève une erreur SQLite (`ABORT`) via les
  triggers de la migration `0001` → ✅.

## 6. Accessibilité & cible atelier

- WCAG 2.5.8 : cibles tactiles ≥ 44×44 px (inputs/select/button) → ✅.
- Labels ARIA natifs (`<label>`) → ✅.
- Panasonic Toughbook G2 (10.1" 1920×1200 paysage / 1200×1920 portrait) →
  Playwright vert sur les 2 viewports → ✅.

## 7. Bloc de signature QA / Validation

| Rôle | Nom / Fonction | Date | Signature |
| :--- | :--- | :--- | :--- |
| Validation (VAL) | ______________ | 2026-11-19 | ______________ |
| Assurance Qualité (PPQA) | ______________ | 2026-11-19 | ______________ |
| Release Manager (CM) | ______________ | 2026-11-19 | ______________ |
