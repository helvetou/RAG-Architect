# Certificat de Conformité FCA / PCA & Retour d'expérience OPF

| Attribute | Value |
| :--- | :--- |
| **Document ID** | `FCA-PCA-GMAO-RAG-ARCH-003` |
| **Version** | `v1.0.0` |
| **Date** | 2026-11-19 |
| **Method** | CMMI-DEV Level 3 `CM` / `PPQA` / `OPF` |

## 1. Functional Configuration Audit (FCA)

### 1.1 Matrice de traçabilité (RTM) — 9/9 `REQ-*` ✅

| Requirement | Test | Statut |
| :--- | :--- | :--- |
| `REQ-DB-001` | `TEST-DB-001` | ✅ |
| `REQ-MATH-001` | `TEST-MATH-001` (FP8 + FP16) | ✅ |
| `REQ-MATH-002` | `TEST-MATH-002` | ✅ |
| `REQ-MATH-003` | `TEST-MATH-003` | ✅ |
| `REQ-FIN-001` | `TEST-FIN-001` | ✅ |
| `REQ-API-001` | `TEST-API-001` | ✅ |
| `REQ-SAFE-001` | `TEST-SAFE-001` (a–f) | ✅ |
| `REQ-CAL-001` | `TEST-CAL-001` | ✅ |
| `REQ-CAL-002` | `TEST-CAL-002` | ✅ |

### 1.2 Tests de jalons (milestone)

`TEST-DB-002`, `TEST-TEL-001/002/003/004`, `TEST-UI-001`, `TEST-INT-001`
(contrat Zod↔OpenAPI + Playwright E2E 12/12), `TEST-GMP-001..004`, benchmark
p99 — tous ✅.

### 1.3 Registre FMEA (`RSK-001..004`)

| Risk | Contrôle | Défauts ouverts |
| :--- | :--- | :--- |
| `RSK-001` (hallucination) | `gate.py` anti-spoofing + grounding (TEST-SAFE-001a–f, TEST-GMP-002) | **0 Critique/Élevé** |
| `RSK-002` (OOM) | KV sizing + headroom + Loop-1 | **0** |
| `RSK-003` (air-gapped) | dual-mode ingestion + batch-upload | **0** |
| `RSK-004` (Python→D1) | Edge BFF (catalog snapshot REST) | **0** |

## 2. Physical Configuration Audit (PCA)

| Élément | Inventaire |
| :--- | :--- |
| Baselines CM | `BL-01-INIT` (`f91dc09`), `BL-02-DATA` (`104dd83`), `BL-03-CORE` (`6fc95b6`), `BL-04-TELEM` (`6d28fda`), `BL-05-INTEG` (`7d9cddc`) |
| Migrations D1 | `0000_calm_wallflower.sql`, `0001_powerful_spectrum.sql` (+ append-only triggers) |
| Contrat OpenAPI | `packages/contracts/openapi.json` |
| Manifeste SHA-256 critique | `gmp_projet04_golden.json` = `250e43a47dae2d614e0459a70e6d7775fcf4261c92e9a9c815a200d36d0a2e96` |
| Artefacts déploiement | `services/sizing-engine/Dockerfile`, `apps/telemetry-worker/wrangler.toml`, `apps/portal/svelte.config.js` |

> **Vérification Docker finale (PCA hôte) — VALIDÉE (2026-11-19) :**
> image `localhost/rag-architect-sizing:1.0.0`, Image ID
> `sha256:f896b500c045cfa3003a61737a38529a4980c1d4af5d67e09665908827aa99f6`,
> runtime non-root `uid=10001(appuser) gid=10001(appuser)`,
> `GET /openapi.json` → HTTP 200 (`SMOKE_TEST=PASS`).

## 3. Organizational Process Focus (OPF) — leçons apprises

1. **Réconciliation formula-exact (CR-001)** — un vecteur de référence « figé » peut
   contenir des erreurs arithmétiques (chunks, KV cache, TCO) ; les figer ne remplace
   pas une vérification par les formules exactes.
2. **Isolation de toolchain** — une pre-release SvelteKit (3.x) a bloqué l'hydration
   client ; le repli sur SvelteKit 2 stable + TS 5.9 a rétabli la reproductibilité CI.
3. **Durcissement anti-spoofing** — la citation regex seule ne suffit pas ; la
   vérification contre les métadonnées des chunks récupérés et la normalisation
   d'unités GMP (décimales à virgule, plages, espaces) sont nécessaires pour `RSK-001`.
4. **Garanties en mécanisme** — les triggers SQLite append-only (et non une convention
   applicative) sont ce qui rend l'audit trail 21 CFR vérifiable par test.

## 4. Décision

FCA ✅ conforme (RTM 9/9, 0 défaut Critique/Élevé). PCA ✅ conforme (Docker hôte
validé, `SMOKE_TEST=PASS`). **Release 1.0 signée** — tag `BL-06-REL-1.0`.
