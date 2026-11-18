# Instructions projet — RAG-Architect for GMAO v3.0 (CMMI Niveau 3 & TDD)

Lois strictes du projet. Toute implémentation doit les respecter sans exception.

## 1. Architecture 4-tiers découplée

- **Tier 1 — Audit Portal & Edge BFF (Front-End)** : SvelteKit + Tailwind CSS sur Cloudflare Pages (`smartmaintenance.helveticore.com`). Les routes serveur interrogent D1 via Drizzle ORM et passent le snapshot catalogue dans le payload REST.
- **Tier 2 — Sizing Engine (Backend)** : microservice **Python 3.12** sans état, géré par **`uv`**, packagé en Docker (Fly). Calculs déterministes : VRAM, KV Cache, VectorDB, gate zéro-hallucination, TCO 3 ans.
- **Tier 3 — Knowledge Base** : base relationnelle **Cloudflare D1 (SQLite)** gérée par **Drizzle ORM** (`packages/db/src/schema.ts`). Catalogues matériels, modèles LLM, soumissions d'audit, coefficients de calibration.
- **Tier 4 — Telemetry Ingestion Pipeline (double mode)** :
  - Mode connecté/hybride : Cloudflare Workers + bucket R2 (traces temps réel, calibration nocturne).
  - Mode air-gapped (`AIR_GAPPED_EDGE`) : buffer local JSONL, upload signé `.jsonl.gz` via `POST /api/v1/telemetry/batch-upload`.

## 2. Gouvernance CMMI-DEV Niveau 3 (« Defined »)

Process Areas applicables : RD, REQM, TS, PI, VER, VAL, CM, PPQA, RSKM, DAR.
Six jalons (M1–M6) avec critères d'entrée/sortie, alignement PA, portes PPQA et baselines CM : `BL-01-INIT`, `BL-02-DATA`, `BL-03-CORE`, `BL-04-TELEM`, `BL-05-INTEG`, `BL-06-REL-1.0`.

## 3. Matrice de traçabilité bidirectionnelle (RTM)

- Chaque exigence reçoit un identifiant immuable `REQ-*` et un cas de test `TEST-*`, mappé vers une section de conception, un module source et un fichier de test.
- Exigences P0/P1 : `REQ-DB-001`, `REQ-MATH-001/002/003`, `REQ-FIN-001`, `REQ-API-001`, `REQ-SAFE-001`, `REQ-CAL-001/002`.
- Traçabilité 100 % obligatoire : aucun `REQ-*` sans `TEST-*`.

## 4. Cycle TDD Red-Green-Refactor OBLIGATOIRE

Aucun code de production ne peut être écrit avant son test en échec (`TEST-*`) validé :

1. **RED** — écrire le test en échec (docstring référençant `REQ-*` et `TEST-*`), exécuter le runner et confirmer l'échec.
2. **GREEN** — implémenter le code minimal déterministe. Le hardcoding pour contourner les formules est interdit (PPQA).
3. **REFACTOR** — typage strict, lisibilité, vectorisation, tests toujours verts.

## 5. Couverture de code obligatoire

- Couverture de **branche ≥ 95 %** sur `services/sizing-engine/core/` (maths + safety gate).
- Commande CI : `uv run pytest --cov=core --cov=api --cov-fail-under=95 --cov-branch`.
- Portes CI complémentaires : `uv run ruff check .` et `uv run mypy --strict core api tests` ; `pnpm --filter portal check` ; `pnpm --filter db test` ; `drizzle-kit check` (zéro dérive de schéma).

## 6. Outillage imposé

- **Python 3.12** + **`uv`** (workspace, lockfile `uv.lock`, `pyproject.toml`) pour `services/sizing-engine`.
- **Drizzle ORM** + **Cloudflare D1** (SQLite) pour `packages/db` ; migrations SQL immuables via `drizzle-kit`.
- SvelteKit/TypeScript : `pnpm`, `vitest`, `svelte-check`/`tsc` ; Worker : `wrangler`/Miniflare.

## 7. Invariants de calcul (vecteur de référence `aud-gmao-2026-001`)

- Streams actifs : `B_active = ceil(N_techs × R_peak)` = 14 (pour 35 techs × 0.40).
- KV Cache : 4.66 GB ; Weights : 1.85 GB ; VectorDB : 1.15 GB ; Reranker : 2.00 GB ; VRAM totale : 10.96 GB.
- Chunks enfants : 901 313 ; TCO 3 ans CAPEX edge 26 458.24 USD vs OPEX cloud 54 531.94 USD → décision `CAPEX_ON_PREM_EDGE`.

## 8. Gate zéro-hallucination (`REQ-SAFE-001`)

`gate.py` bloque toute réponse sans citation explicite `[Manual ID, Section, Page]` ou contenant une grandeur physique (`Nm, bar, psi, V, A, °C`) absente des chunks parents, avec le message `"SAFETY GATE BLOCK: Unverified numerical specification or missing citation detected. Consult physical manual directly."`

## 9. Calibration en boucle fermée (`REQ-CAL-001/002`)

- **Loop 1** : P95 TTFT > 1500 ms OU VRAM pic > 90 % → `M_calib` += 0.20.
- **Loop 2** : `context_recall` < 0.75 OU P50 reranker < 0.60 → `child_chunk_size_tokens` −20 %.
- **Loop 3** : dépense tokens cloud > baseline +15 % → activer `SEMANTIC_ROUTER_SLM_3B`.
