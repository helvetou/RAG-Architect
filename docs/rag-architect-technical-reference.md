# RAG-Architect for GMAO v3.0 — Dossier de Référence Technique

> Document technique exhaustif et autonome, destiné à l'import dans un Notebook IA.
> Généré à partir de l'état du dépôt `/media/malek/DONNEES/pydev/RAG-Architect` (branche `main`, commit `2cd271b`).
> Périmètre : monorepo complet — `apps/`, `services/`, `packages/`, `docs/`, configuration racine.
> Méthodologie projet : CMMI-DEV Niveau 3 (« Defined ») + Strict TDD (Red-Green-Refactor).
> Spécification gouvernante : `technical_specification_rag_architect_for_gmao_v3_0_cmmi_l3_tdd.md` (SPEC-GMAO-RAG-ARCH-003 v3.0.0).

---

## 1. Vue d'ensemble & Cartographie du Monorepo

### 1.1 Arborescence commentée

```
RAG-Architect/
├── package.json                         # racine pnpm workspace — "rag-architect-gmao", packageManager pnpm@9.12.0, script "lint": eslint .
├── pnpm-workspace.yaml                  # packages: ["apps/*", "packages/*"]
├── pnpm-lock.yaml                       # verrouillage pnpm
├── eslint.config.mjs                    # config ESLint flat (typescript-eslint)
├── .gitignore
├── README.md                            # vue d'ensemble, statut M1–M6, déploiement, ops notes
├── milestones.md                        # plan M1–M6 (critères d'entrée/sortie, portes PPQA, baselines)
├── uptoM4.md                            # synthèse d'audit externe jusqu'à M4
├── technical_specification_rag_architect_for_gmao_v3_0_cmmi_l3_tdd.md  # SPEC v3.0 (gouvernante)
├── technical_specification_rag_architect_for_gmao_v2_1.md              # SPEC v2.1 (historique, annexe cas d'étude FR)
├── codewhaleSpecIntepretation.md        # interprétation de la spec pour agents
├── .codewhale/
│   ├── instructions.md                  # lois strictes projet (architecture 4 tiers, TDD, invariants)
│   └── verify-*.sh                      # scripts de vérification (m1, m2 red/green, ts, eslint, net)
├── .github/workflows/ci-cmmi-gate.yml   # pipeline CI 4 tiers (voir §6)
├── apps/
│   ├── portal/                          # Tier 1 — SvelteKit (Cloudflare Pages)
│   └── telemetry-worker/                # Tier 4 — Cloudflare Worker (télémétrie)
├── services/
│   └── sizing-engine/                   # Tier 2 — FastAPI Python 3.12 (Fly.io)
├── packages/
│   ├── db/                              # Tier 3 — Drizzle ORM + schéma D1 + seeds + migrations
│   └── contracts/openapi.json           # contrat OpenAPI partagé (exporté depuis FastAPI)
└── docs/
    ├── progress.md                      # journal de progression / état des jalons
    ├── cmmi/                            # artefacts de gouvernance (RTM, FMEA, logs RED, PV, certificats)
    └── tutoriel_cli_glossaire_d_ploiement_rag_architect.md  # tutoriel CLI + glossaire déploiement (NON SUIVI = untracked)
```

### 1.2 Rôle exact de chaque application / service

| Composant | Tier | Stack | Rôle |
| :--- | :--- | :--- | :--- |
| `apps/portal` (`@rag-architect/portal`) | 1 — Front-End + BFF | SvelteKit 2 + `@sveltejs/adapter-cloudflare` + Tailwind v4 + Zod v4 + Vitest v3 + Playwright | Formulaire d'audit multi-étapes ; routes serveur BFF qui interrogent D1, appellent le sizing engine, persiste l'audit append-only et proxy le batch télémétrie. |
| `services/sizing-engine` | 2 — Backend calcul | Python 3.12 + `uv` + FastAPI + Pydantic v2, packagé Docker, déployé Fly.io | Calculs déterministes de dimensionnement : VRAM (weights/KV/vectorDB/reranker), volume de chunks, TCO 3 ans, gate zéro-hallucination, calibration. |
| `packages/db` (`@rag-architect/db`) | 3 — Knowledge Base | Cloudflare D1 (SQLite) via Drizzle ORM (`drizzle-kit`) | Schéma relationnel (`schema.ts`), données seed déterministes (`seed.ts`), migrations SQL immuables, conformité 21 CFR Part 11. |
| `apps/telemetry-worker` (`@rag-architect/telemetry-worker`) | 4 — Telemetry Pipeline | Cloudflare Worker + R2 + D1 | Ingestion d'événements de télémétrie temps réel, upload de lots `.jsonl.gz` signés SHA-256, cron de calibration. |
| `packages/contracts/openapi.json` | — (contrat) | OpenAPI 3.1 (généré) | Contrat d'échange Portal ↔ Sizing Engine, consommé par les tests de contrat Zod. |

### 1.3 Matrice de communication (protocoles, URLs, ports, variables, secrets)

| Source → Cible | Protocole / mécanisme | URL / port | Variables / secrets |
| :--- | :--- | :--- | :--- |
| Portal BFF → D1 | SQL via Drizzle (binding natif Workers) | binding `DB` (D1 `rag-architect-db`) | `DB` (binding, prod + preview) |
| Portal BFF → Sizing Engine | HTTPS POST JSON | prod `https://rag-architect-sizing.fly.dev` / dev `http://127.0.0.1:8000` | `SIZING_ENGINE_URL` (normalisé par `config.ts`) |
| Portal BFF → Telemetry Worker | HTTPS POST (octet-stream) | prod `https://telemetry-worker.haroudm.workers.dev` / dev `http://127.0.0.1:8787` | `TELEMETRY_WORKER_URL`, `AUTH_TOKEN` (secret), `X-Batch-Signature-SHA256` |
| Telemetry Worker → R2 | objet Cloudflare | binding `TELEMETRY_BUCKET` (bucket `telemetry-bucket`) | `TELEMETRY_BUCKET` (binding) |
| Telemetry Worker → D1 | SQL (cron) | binding `DB` (D1 `rag-architect-db`) | `DB` (binding) |
| Sizing Engine → DB | — (aucun accès DB) | — | — (catalogue intégré en constantes déterministes dans `api/routes.py`) |
| CI → Sizing Engine | commandes `uv` | local | `uv sync --frozen`, `ruff`, `mypy`, `pytest` |
| CI → packages/apps | commandes `pnpm` | local | `eslint`, `tsc --noEmit`, `vitest`, `drizzle-kit check`, `vite build` |

**Ports locaux** : Sizing Engine `8000` (uvicorn, interne Fly également `8000`), Portal dev `4173` (Playwright `webServer`), Telemetry Worker dev `8787` (défaut wrangler).

**Secrets** : `AUTH_TOKEN` est un secret **partagé à l'identique** entre `telemetry-worker` et `rag-architect-portal` (prod + preview). Il est fourni via Cloudflare secrets / `.dev.vars` et **jamais** committé dans `wrangler.toml`.

**Domaine cible** : `rag-architect.helveticore.com` (déploiement isolé ; ancien domaine `smartmaintenance.helveticore.com` balayé — commit `f8eb21a`).

---

## 2. Modèle de Données & Validation des Contrats

### 2.1 Schémas d'entrée — Zod (TypeScript, `apps/portal/src/lib/schemas.ts`)

Le fichier définit 4 schémas Zod v4 (`z.object`), miroir exact des modèles Pydantic du moteur :

- `documentsSchema` : `equipment_manuals_pdf_gb` (number), `historical_work_orders_count` (number), `average_tokens_per_page` (number).
- `concurrencySchema` : `peak_shift_overlap_ratio` (number), `avg_queries_per_tech_shift` (number), `target_p95_ttft_seconds` (number).
- `financialsSchema` : `electricity_rate_kwh_usd` (number).
- `sizeRequestSchema` (racine) : `audit_id` (string), `client_name` (string), `deployment_constraint` (string), `technicians_per_shift` (number), `total_shifts` (number), `documents`, `concurrency`, `financials`, `safety_critical` (boolean).

Un second schéma `sizeResponseSchema` valide la réponse minimale (`audit_id`, `verdict.model_stack.total_vram_required_gb`, `max_concurrent_streams`, `rag_parameters.estimated_total_child_chunks`, `tco_3year_comparison.capex_edge_total_usd`, `opex_cloud_total_usd`, `recommended_decision`).

Le type dérivé `export type SizeRequest = z.infer<typeof sizeRequestSchema>` est utilisé côté client (`SizeAuditForm.svelte`).

### 2.2 Schémas d'entrée — Pydantic v2 (Python, `services/sizing-engine/api/routes.py`)

Modèles `BaseModel` équivalents, définis **inline** dans `routes.py` :

- `Documents` : `equipment_manuals_pdf_gb: float`, `historical_work_orders_count: int`, `average_tokens_per_page: float`.
- `Concurrency` : `peak_shift_overlap_ratio: float`, `avg_queries_per_tech_shift: int`, `target_p95_ttft_seconds: float`.
- `Financials` : `electricity_rate_kwh_usd: float`.
- `SizeRequest` : `audit_id: str`, `client_name: str`, `deployment_constraint: str`, `technicians_per_shift: int`, `total_shifts: int`, `documents: Documents`, `concurrency: Concurrency`, `financials: Financials`, `safety_critical: bool`.

Ces modèles sont exportés en OpenAPI via `scripts/export_openapi.py` vers `packages/contracts/openapi.json` (chemins : `/api/v1/size-architecture` ; schémas : `SizeRequest`, `Documents`, `Concurrency`, `Financials`, `ValidationError`, `HTTPValidationError`). Le test `apps/portal/src/lib/schemas.test.ts` (TEST-INT-001) vérifie la **parité exacte des clés** Zod ↔ OpenAPI.

### 2.3 Champs d'entrée exhaustifs (regroupés par thème)

| Thème | Champ | Type | Défaut UI |
| :--- | :--- | :--- | :--- |
| Exploitation | `deployment_constraint` | string (`AIR_GAPPED_EDGE`\|`HYBRID_CONNECTED`\|`FULL_CLOUD`) | `AIR_GAPPED_EDGE` |
| Exploitation | `client_name` | string | `Helvetic Precision Manufacturing` |
| Exploitation | `technicians_per_shift` | int | (vide, requis) |
| Exploitation | `total_shifts` | int | `3` |
| Corpus documentaire | `documents.equipment_manuals_pdf_gb` | float | `85` |
| Corpus documentaire | `documents.historical_work_orders_count` | int | `450000` |
| Corpus documentaire | `documents.average_tokens_per_page` | float | `420` |
| Concurrence/Latence | `concurrency.peak_shift_overlap_ratio` | float | `0.40` |
| Concurrence/Latence | `concurrency.avg_queries_per_tech_shift` | int | `15` |
| Concurrence/Latence | `concurrency.target_p95_ttft_seconds` | float | `1.5` |
| Énergie | `financials.electricity_rate_kwh_usd` | float | `0.18` |
| Sécurité | `safety_critical` | boolean | `true` |

### 2.4 Champs de sortie (`verdict` — `POST /api/v1/size-architecture`)

La réponse JSON retournée par `api/routes.py::size_architecture` contient :

```
audit_id
verdict.deployment_mode                                   (recopie de deployment_constraint)
verdict.recommended_hardware[]                            {hardware_id, name, quantity, vram_per_unit_gb, system_ram_gb, role}
verdict.model_stack.generator_model_id                    ("llama-3.2-3b-instruct-q4")
verdict.model_stack.embedding_model_id                    ("bge-m3-industrial")
verdict.model_stack.reranker_model_id                     ("bge-reranker-base")
verdict.model_stack.weights_vram_gb                       (1.85)
verdict.model_stack.kv_cache_allocated_gb                 (4.66)
verdict.model_stack.vector_db_vram_gb                     (1.15)
verdict.model_stack.total_vram_required_gb                (10.96)
verdict.model_stack.max_concurrent_streams                (14)
verdict.rag_parameters.estimated_total_child_chunks       (901313)
verdict.rag_parameters.chunking_strategy                  ("PARENT_CHILD_SEMANTIC")
verdict.rag_parameters.child_chunk_size_tokens            (200)
verdict.rag_parameters.parent_chunk_size_tokens           (1000)
verdict.rag_parameters.retrieval_mode                     ("HYBRID_BM25_VECTOR_RRF")
verdict.rag_parameters.rrf_constant_k                     (60)
verdict.rag_parameters.rerank_top_k                       (50)
verdict.rag_parameters.generator_top_k                    (5)
verdict.rag_parameters.zero_hallucination_gate            ("ENABLED")
verdict.tco_3year_comparison.hardware_capex_usd           (16420.00)
verdict.tco_3year_comparison.energy_and_maint_3yr_usd     (10038.24)
verdict.tco_3year_comparison.capex_edge_total_usd         (26458.24)
verdict.tco_3year_comparison.opex_cloud_total_usd         (54531.94)
verdict.tco_3year_comparison.net_savings_usd              (28073.70)
verdict.tco_3year_comparison.recommended_decision         ("CAPEX_ON_PREM_EDGE")
```

### 2.5 Base de données Cloudflare D1 (`rag-architect-db`, id `ba6b952e-1d76-4201-a650-aba9df3d0307`)

Schéma Drizzle dans `packages/db/src/schema.ts` ; colonnes réelles en SQL dans les migrations `packages/db/migrations/0000_calm_wallflower.sql` (création) et `0001_powerful_spectrum.sql` (colonnes audit + triggers).

**Table `hardware_catalog`** (`hardwareCatalog`) — colonnes : `id` (PK text), `name`, `tier`, `vram_gb` (real), `system_ram_gb` (real), `tdp_watts` (int), `unit_cost_capex_usd` (real, déf. 0), `monthly_maint_opex_usd` (real, déf. 0), `max_bandwidth_gbps` (real).

**Table `model_registry`** (`modelRegistry`) — colonnes : `id` (PK), `name`, `param_count_b` (real), `context_window_tokens` (int), `hidden_dim` (int), `layer_count` (int), `q_head_count` (int), `kv_head_count` (int), `head_dim` (int), `weight_quant_bits` (int), `kv_cache_bits` (int, déf. 16), `input_token_cost_1m` (real, déf. 0), `output_token_cost_1m` (real, déf. 0), `is_edge_compatible` (boolean).

**Table `audit_submissions`** (`auditSubmissions`) — colonnes : `id` (PK text, UUID v4), `client_name`, `techs_per_shift` (int), `total_shifts` (int, déf. 3), `manuals_volume_gb` (real), `work_orders_count` (int), `avg_tokens_per_page` (int, déf. 420), `deployment_constraint` (text), `peak_query_ratio` (real, déf. 0.4), `avg_queries_per_tech_shift` (int, déf. 15), `electricity_rate_kwh_usd` (real, déf. 0.18), `target_p95_ttft_seconds` (real, déf. 1.5), `created_at` (int timestamp), + champs 21 CFR (`migration 0001`) : `actor_id` (text, déf. `system`), `input_payload_sha256` (text, déf. `''`), `output_payload_sha256` (text, déf. `''`), `spec_version` (text, déf. `SPEC-GMAO-RAG-ARCH-003`), `model_version` (text, déf. `llama-3.2-3b-instruct-q4`).

**Table `telemetry_calibration`** (`telemetryCalibration`) — colonnes : `id` (PK, clé synthétique `modelId_hardwareId`), `model_id` (FK → `model_registry.id`), `hardware_id` (FK → `hardware_catalog.id`), `measured_p95_ttft_ms` (real), `measured_peak_vram_gb` (real), `measured_context_recall` (real), `measured_faithfulness` (real), `compute_scaling_multiplier` (real, déf. 1.0), `rolling_sample_count` (int), `last_updated` (int timestamp). Deux clés étrangères avec `ON DELETE NO ACTION`.

**Index** : uniquement les clés primaires (`id`) et les clés étrangères. Aucun index secondaire explicite.

### 2.6 Conformité 21 CFR Part 11 — mécanismes SQL append-only

Migration `0001_powerful_spectrum.sql` crée deux triggers :

```sql
CREATE TRIGGER `audit_submissions_append_only_update`
BEFORE UPDATE ON `audit_submissions`
BEGIN
  SELECT RAISE(ABORT, 'audit_submissions is append-only');
END;

CREATE TRIGGER `audit_submissions_append_only_delete`
BEFORE DELETE ON `audit_submissions`
BEGIN
  SELECT RAISE(ABORT, 'audit_submissions is append-only');
END;
```

Conséquence : toute tentative d'`UPDATE` ou `DELETE` lève une erreur SQLite (`ABORT`), vue côté D1 comme `SQLITE_CONSTRAINT_TRIGGER` avec le message `audit_submissions is append-only`. L'immutabilité est couverte par `packages/db/tests/schema.test.ts` (TEST-DB-002) et `packages/db/tests/gmp.test.ts` (TEST-GMP-004), et validée en production (lignes `aud-cli-test-004`, `aud-post-deploy-001`).

### 2.7 Données seed déterministes (`packages/db/src/seed.ts`)

- **Matériel** : `rugged-edge-l4-24g` (L4 24GB, 300W, $8 210, $100/mois), `rugged-dual-a4500-40g` (A4500 40GB, 400W, $12 990, $140/mois), `nvidia-l40s` (L40S 48GB cloud, $1 490/mois), `edgestream-gw-01` (gateway 8GB RAM, 15W).
- **Modèles** : `llama-3.2-3b-instruct-q4` (3.21B, ctx 128 000, hidden 3072, 28 couches, 24 têtes Q, 8 têtes KV, head_dim 128, weight_quant 4, kv_cache 8, edge-compatible).

---

## 3. Moteur de Dimensionnement (`services/sizing-engine`)

### 3.1 Architecture interne

- `api/routes.py` — application FastAPI (`app = FastAPI(title="RAG-Architect Sizing Engine")`), modèles Pydantic, route unique `POST /api/v1/size-architecture` (`size_architecture`). Constantes de référence : `_REFERENCE_MODEL`, `_REFERENCE_HARDWARE`, `_SEQUENCE_LENGTH = 5800`, `_CHILD_CHUNK_SIZE_TOKENS = 200`.
- `core/calculator.py` — moteur de calcul pur (aucun I/O) : fonctions `compute_active_streams`, `compute_kv_cache_gb`, `compute_total_child_chunks`, `compute_vram_allocation`, `compute_3year_tco` + dataclasses `ModelSpec`, `HardwareSpec`, `DocumentProfile`, `VramAllocation`, `TcoResult`.
- `core/gate.py` — gate zéro-hallucination : `verify_response_safety`, `RetrievedChunk`, `GateResult`, `SAFETY_BLOCK_MESSAGE`.
- `core/calibration.py` — boucles de calibration : `evaluate_calibration_loops`, `should_sample_for_eval`, `parse_jsonl_gz`, `RollingTelemetryMetrics`, `CalibrationDecision`.
- `core/__init__.py`, `api/__init__.py` — marqueurs de package.

### 3.2 Formules et algorithmes (`core/calculator.py`)

Constantes de la spec (§5.2/5.3), toutes explicitement déclarées :

| Constante | Valeur | Rôle |
| :--- | :--- | :--- |
| `PAGES_PER_GB` | 2500 | pages par Go de manuel |
| `WORK_ORDER_TOKENS` | 150 | tokens par ordre de travail |
| `CHUNK_OVERLAP_NUM/DEN` | 23/20 | facteur de chevauchement 1.15 |
| `WEIGHTS_OVERHEAD` | 1.15 | surcoût poids (quantization overhead) |
| `EMBEDDING_DIM` | 1024 | dimension d'embedding (bge-m3) |
| `VECTOR_QUANT_BYTES` | 1.0 | quantification SQ8 (1 octet/vecteur) |
| `HNSW_OVERHEAD` | 1.25 | surcoût index HNSW |
| `RERANKER_VRAM_GB` | 2.0 | VRAM reranker |
| `VRAM_HEADROOM_RATIO` | 0.20 | marge de sécurité 20 % sur weights+KV |
| `HOURS_PER_MONTH` / `DAYS_PER_MONTH` / `MONTHS` | 730 / 30.4 / 36 | base temporelle TCO |
| `TOKENS_IN` / `TOKENS_OUT` | 5400 / 400 | tokens par requête cloud |
| `PRICE_IN_PER_1M` / `PRICE_OUT_PER_1M` | 3.00 / 15.00 USD | prix tokens cloud |
| `CLOUD_VECTOR_HOST_MONTHLY` | 451.84 USD | coût mensuel d'hébergement vectoriel cloud |
| `_BYTES_PER_GB` | 1_000_000_000 | convention SI (1 Go = 1e9 octets) |

**a) Streams actifs (§5.1)** — `compute_active_streams(technicians_per_shift, peak_query_ratio)` :
```
B_active = ceil(N_techs × R_peak)   →   ceil(35 × 0.40) = 14
```

**b) KV-cache GQA (§5.1)** — `compute_kv_cache_gb(active_streams, sequence_length, model)` :
```
KV_GB = 2 × B_active × L_seq × N_layers × H_kv × D_head × (kv_cache_bits / 8) / 1e9
      = 2 × 14 × 5800 × 28 × 8 × 128 × (8/8) / 1e9 ≈ 4.66 GB
```
Le facteur `kv_cache_bits / 8` est **paramétré dynamiquement** (FP8 = 8 bits → 4.66 GB ; FP16 = 16 bits → 9.31 GB, testé dans TEST-MATH-001).

**c) Chunks enfants (§5.2)** — `compute_total_child_chunks(docs)` :
```
manuals_tokens   = GB × 2500 × avg_tokens_per_page        (85 × 2500 × 420 = 89 250 000)
work_order_tokens = work_orders × 150                     (450 000 × 150 = 67 500 000)
total_tokens      = 156 750 000
child_chunks      = ceil(total_tokens × 23 / (200 × 20))  = 901 313
```

**d) Allocation VRAM (§5.2)** — `compute_vram_allocation(...)` :
```
weights    = param_count_b × (weight_quant_bits/8) × 1.15      = 3.21 × 0.5 × 1.15 = 1.85 GB
kv_cache   = compute_kv_cache_gb(...)                          = 4.66 GB
vector_db  = child_chunks × 1024 × 1.0 × 1.25 / 1e9            = 1.15 GB
reranker   = 2.0 GB
headroom   = 0.20 × (weights + kv_cache)                       = 1.30 GB
total      = (weights + kv_cache + vector_db + reranker + headroom) × M_calib
           = 10.96 GB  (M_calib = 1.0)
```

**e) TCO 3 ans (§5.3)** — `compute_3year_tco(...)` :
```
quantity              = ceil(total_vram / hw.vram_gb)   → ceil(10.96/24) = 1
if safety_critical:   quantity = max(2, quantity)       → 2  (HA actif-actif)
hardware_capex        = unit_cost × quantity            = 8210 × 2 = 16 420.00
energy_monthly        = tdp × qty × 730 × rate / 1000   = 300×2×730×0.18/1000 = 78.84
maintenance_monthly   = 100 × 2                         = 200.00
energy_and_maint_3yr  = (78.84 + 200) × 36              = 10 038.24
capex_edge_total      = 16 420 + 10 038.24              = 26 458.24
volume_monthly        = techs × shifts × queries × 30.4 = 35×3×15×30.4 = 47 880
token_cost_monthly    = ((5400×3 + 400×15)/1e6) × 47 880 = 1 062.94
opex_monthly          = token_cost + 451.84             = 1 514.78
opex_cloud_total      = 1 514.78 × 36                   = 54 531.94
net_savings           = opex − capex                    = 28 073.70
decision              = "CAPEX_ON_PREM_EDGE" si capex < opex, sinon "OPEX_CLOUD_MANAGED"
```

### 3.3 Gate zéro-hallucination (`core/gate.py`, `REQ-SAFE-001`)

`verify_response_safety(candidate_response, parent_chunks) -> GateResult` applique **deux vérifications conjointes** (les deux doivent réussir) :

1. **Anti-spoofing de citation** — la regex `_CITATION_PATTERN` (`\[Manual ID, Section X, Page Y\]`) est extraite, puis chaque citation doit correspondre à un `RetrievedChunk` réel (`_citation_is_grounded` compare `manual_id`, `section`, `page`) — pas seulement la forme regex.
2. **Ancrage numérique** — la regex `_NUMERIC_PATTERN` détecte toute grandeur physique (`12,5 bar`, `120 °C`, `10-15 Nm`, unités étendues `daNm|N·m|N.m|Nm|kPa|MPa|bar|psi|Pa|kV|mA|Hz|°C|µm|mm|rpm|L/min|min|ppm|V|A|%`), normalise la virgule (`_normalize`) et exige que la valeur apparaisse dans le texte concaténé des `parent_chunks`.

Si l'une des deux vérifications échoue, `is_safe=False` et `final_output = SAFETY_BLOCK_MESSAGE` :
```
"SAFETY GATE BLOCK: Unverified numerical specification or missing citation detected. Consult physical manual directly."
```

### 3.4 Calibration en boucle fermée (`core/calibration.py`, `REQ-CAL-001/002`)

`evaluate_calibration_loops(metrics) -> CalibrationDecision` applique 3 boucles :

| Boucle | Déclencheur | Action |
| :--- | :--- | :--- |
| Loop 1 | P95 TTFT > 1500 ms **ou** VRAM pic > 90 % du matériel | `M_calib` += 0.20 |
| Loop 2 | `context_recall` < 0.75 **ou** P50 reranker < 0.60 | `child_chunk_size_tokens` × 0.80 (arrondi int) |
| Loop 3 | dépense tokens cloud > baseline + 15 % | activer `SEMANTIC_ROUTER_SLM_3B` |

Fonctions auxiliaires :
- `should_sample_for_eval(query_hash, sample_rate=0.05)` — échantillonnage RAGAS asynchrone **déterministe** à 5 % (SHA-256 du hash → bucket modulo 100).
- `parse_jsonl_gz(payload)` — décompression gzip + parsing ligne-à-ligne d'un batch air-gapped `.jsonl.gz`.

### 3.5 Docker & Fly.io

- `Dockerfile` : image de base `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` ; `uv sync --frozen --no-dev` en deux étapes (cache) ; utilisateur **non-root** `appuser` (uid 10001) ; `EXPOSE 8000` ; `HEALTHCHECK` sur `GET /openapi.json` ; `CMD ["uvicorn", "api.routes:app", "--host", "0.0.0.0", "--port", "8000"]`.
- `.dockerignore` : exclut `.venv`, caches (`mypy/pytest/ruff`), `reports/htmlcov`, `fly.toml`, `.git`.
- `fly.toml` : app `rag-architect-sizing`, `primary_region = 'cdg'`, `internal_port = 8000`, `force_https = true`, `min_machines_running = 0`, VM `memory = '1gb'`, `cpus = 1`.
- `pyproject.toml` : `requires-python >=3.12,<3.13` ; dépendances `fastapi`, `pydantic>=2.9`, `numpy>=2.1`, `uvicorn>=0.54.0` ; dev `pytest`, `pytest-cov`, `mypy`, `ruff`, `httpx` ; config `ruff` (line-length 100, sélecteurs E/F/I/N/W/UP/B/S) et `mypy --strict` ; `pytest` avec `--cov=core --cov=api --cov-fail-under=95 --cov-branch`.

---

## 4. Portail Web & Backend-for-Frontend (`apps/portal`)

### 4.1 Configuration SvelteKit / Cloudflare

- `svelte.config.js` : `vitePreprocess()` + `adapter()` de `@sveltejs/adapter-cloudflare` (build vers `.svelte-kit/cloudflare`).
- `vite.config.ts` : plugins `sveltekit()` + `tailwindcss()` (`@tailwindcss/vite`).
- `wrangler.toml` : app `rag-architect-portal`, `pages_build_output_dir = ".svelte-kit/cloudflare"`, `compatibility_flags = ["nodejs_compat"]` ; binding `DB` → `rag-architect-db` (id `ba6b952e-...`) en **production et preview** ; vars `SIZING_ENGINE_URL` et `TELEMETRY_WORKER_URL` en prod et preview.
- `tsconfig.json` : config TypeScript (extensions SvelteKit).
- `vitest.config.ts` : environnement `jsdom`, alias `$lib → ./src/lib`, setup `./src/test-setup.ts`, `include: ['src/**/*.test.ts']`.
- `playwright.config.ts` : `baseURL http://127.0.0.1:4173`, 3 projets (`chromium`, `toughbook-landscape` 1920×1200, `toughbook-portrait` 1200×1920), `webServer` = `vite dev --port 4173`.

### 4.2 `apps/portal/src/lib/config.ts` — `normalizeUrl`

`resolveEngineUrl(env, isDev)` et `resolveWorkerUrl(env, isDev)` résolvent les URLs avec une normalisation défensive (`normalizeUrl`) qui :
- prend `SIZING_ENGINE_URL` / `TELEMETRY_WORKER_URL` sinon un fallback (dev `http://127.0.0.1:8000` / `http://127.0.0.1:8787`, prod `https://rag-architect-sizing.fly.dev` / `https://telemetry-worker.haroudm.workers.dev`) ;
- retire les enveloppes Markdown `[url](url)`, les chevrons `<>`, les slashs finaux ;
- valide le protocole (`http:`/`https:`) via `new URL(...)` et retombe sur le fallback si malformé.

C'est le correctif du bug `502 Sizing engine unavailable` (une valeur `SIZING_ENGINE_URL` au format Markdown passée telle quelle). Couvert par `config.test.ts`.

### 4.3 Route BFF `POST /api/audit` (`src/routes/api/audit/+server.ts`)

Cycle de vie d'une requête :

1. `request.json()` — en cas d'échec → `400 { error: "Invalid JSON" }`.
2. `sizeRequestSchema.safeParse(body)` — en cas d'échec → `400 { error: "Invalid request", issues }`.
3. Lecture `platform?.env` → `db = env?.DB`.
4. **RSK-004** : si `db` présent, vérifie `SELECT id FROM hardware_catalog LIMIT 1` et `model_registry` ; en échec → `502 { error: "D1 catalog unavailable" }`.
5. `resolveEngineUrl(env, import.meta.env.DEV)` puis `fetch(engineUrl + "/api/v1/size-architecture", POST JSON)`.
   - non-2xx → `502 { error: "Sizing engine error" }` ;
   - exception réseau → `502 { error: "Sizing engine unavailable" }`.
6. **21 CFR Part 11** : si `db` présent, `buildAuditSubmission('portal-bff', input, output)` (SHA-256 via `crypto.subtle.digest` dans `src/lib/audit.ts`) puis `INSERT INTO audit_submissions (...18 colonnes...)` avec `actor_id = "portal-bff"` et `created_at = floor(Date.now()/1000)`. En échec → `502 { error: "Audit persistence failed" }`.
7. Retourne `result` du moteur (`200`).

Le bloc `catch` ne fuit aucun détail de diagnostic : il renvoie des messages d'erreur JSON génériques (`Sizing engine unavailable`, etc.), jamais la stack.

### 4.4 Route BFF `POST /api/batch-upload` (`src/routes/api/batch-upload/+server.ts`)

Proxifie le batch air-gapped vers le Worker : lit `request.arrayBuffer()`, propage `X-Batch-Signature-SHA256`, injecte le Bearer `env.AUTH_TOKEN` (sinon réutilise l'en-tête `Authorization` entrant), `fetch(workerUrl + "/api/v1/telemetry/batch-upload")`, retourne `202` si le Worker a répondu OK, sinon `502` (ou `502 { error: "Telemetry worker unavailable" }` sur exception).

### 4.5 Interface utilisateur

- `src/routes/+page.svelte` : `<h1>RAG-Architect Audit Portal</h1>` + `<SizeAuditForm />`.
- `src/lib/SizeAuditForm.svelte` : composant Svelte 5 (runes `$state`) gérant le formulaire « Step 1 — Parameters » et le rendu « Step 2 — Results ».
  - État : `deploymentMode`, `clientName`, `technicians`, `totalShifts`, `manualsGb`, `workOrders`, `avgTokens`, `peakRatio`, `avgQueries`, `targetTtft`, `electricityRate`, `safetyCritical`, `result`, `error`, `loading`.
  - `parseDecimal` remplace la virgule par le point (support saisies `12,5`) ; champs décimaux en `type="text" inputmode="decimal"`.
  - `submit()` : vide `error`/`result`, valide `technicians`, `sizeRequestSchema.parse(...)` avec `audit_id = randomUuid()` (UUID v4 via `crypto.randomUUID`), `fetch('/api/audit')`, gère non-2xx (message d'erreur du body ou fallback), exception réseau, `finally { loading = false }`.
  - Regroupement en 5 `<fieldset>` : Cible & Exploitation, Corpus documentaire, Concurrence & Latence, Énergie & TCO, Sécurité/HA ; grille CSS responsive (2 colonnes → 1 colonne ≤ 40rem) ; bouton « Size architecture » avec état « Sizing… » (spinner, `disabled`, `aria-busy`).
  - Résultats : `CAPEX`/`OPEX` (formatés `currency`), ventilation VRAM (`Weights`, `KV cache`, `VectorDB`, `Total`, `Max concurrent streams`), `Chunks`, `Recommended decision`.
- `src/lib/audit.ts` : `sha256Hex`, `buildAuditSubmission`, `randomUuid` (helpers 21 CFR).
- `src/app.d.ts` : typage `App.Platform.env` (`DB`, `AUTH_TOKEN`, `TELEMETRY_WORKER_URL`, `SIZING_ENGINE_URL`).

### 4.6 Limites actuelles de l'UI

- Le formulaire valide les erreurs de façon **globale** (un seul `<p role="alert">`), pas de validation champ-par-champ avec messages inline.
- Les résultats sont affichés en texte simple (pas de graphiques TCO/VRAM malgré l'exigence M5 initiale de « visualisations interactives ») — les valeurs sont rendues mais sans graphe.
- `target_p95_ttft_seconds` était historiquement codé en dur à 1.5 ; désormais exposé en champ.
- Pas de persistance côté client ni d'état multi-étapes « wizard » réel (Step 1 / Step 2 cohabitent sur une page).

---

## 5. Worker de Télémétrie (`apps/telemetry-worker`)

### 5.1 Rôle et entrées/sorties

`src/index.ts` exporte un handler Workers `default` avec deux méthodes :
- `fetch(request, env, ctx)` — HTTP entrant.
- `scheduled(controller, env, ctx)` — cron.

Interface `Env` : `AUTH_TOKEN: string`, `TELEMETRY_BUCKET: R2Bucket`, `DB: D1Database`.

### 5.2 Routes HTTP

| Route | Méthode | Comportement | Codes |
| :--- | :--- | :--- | :--- |
| `/api/v1/telemetry/event` | POST | Vérifie Bearer `AUTH_TOKEN` (`isAuthorized`), parse JSON, valide la forme via `isTelemetryEvent` (`client_id` string, `timestamp` string, `execution_metrics` objet), stocke dans R2 sous `telemetry/events/{Date.now()}.json` via `ctx.waitUntil` | 202 / 400 / 401 |
| `/api/v1/telemetry/batch-upload` | POST | Vérifie `X-Batch-Signature-SHA256` (présence → 400, correspondance SHA-256 du corps via `constantTimeEqual` → 401 sinon), stocke le binaire `.jsonl.gz` sous `telemetry/batches/{Date.now()}.jsonl.gz` | 202 / 400 / 401 |
| toute autre route | — | 404 | 404 |

### 5.3 Authentification

`isAuthorized` compare l'en-tête `Authorization` à `Bearer ${env.AUTH_TOKEN}` (comparaison stricte). `constantTimeEqual` évite les attaques par timing sur la comparaison du digest SHA-256.

### 5.4 Cron de calibration (`scheduled`)

Déclenché par `wrangler.toml` (`[triggers] crons = ["0 3 * * *"]`, quotidien 03:00 UTC). Lit la dernière ligne de `telemetry_calibration` (JOIN `hardware_catalog` pour `vram_gb`), applique la **Loop 1** (P95 TTFT > 1500 ms ou VRAM pic > 90 %) et, si déclenchée, `UPDATE telemetry_calibration SET compute_scaling_multiplier = M_calib + 0.2, last_updated = now`.

### 5.5 Format d'événement ingéré

Exemple minimal validé : `{ "client_id": "...", "timestamp": "ISO-8601", "execution_metrics": { "ttft_ms": 1180.4, ... } }`.

---

## 6. Stratégie de Tests & Qualité

### 6.1 Inventaire des fichiers de tests

**Python (`services/sizing-engine/tests/`, exécutés par `pytest`)**
- `test_calculator.py` — TEST-MATH-001/002/003 + TEST-FIN-001 : streams actifs, KV-cache FP8/FP16, conversion documents→chunks (901 313), allocation VRAM (10.96), TCO 3 ans (décision `CAPEX_ON_PREM_EDGE`).
- `test_api.py` — TEST-API-001 : vérifie le vecteur de référence complet `POST /api/v1/size-architecture`.
- `test_gate.py` — TEST-SAFE-001a..f : réponse ancrée (passe), valeur hallucinée (bloquée), citation manquante (bloquée), spoofing de citation (bloqué), décimales à virgule/espaces optionnels, plages et unités étendues.
- `test_calibration.py` — TEST-CAL-001/002 : Loop 1 (+0.20), Loop 2 (−20 %), Loop 3 (semantic router), déclencheurs VRAM/reranker, échantillonnage déterministe 5 %, parsing `.jsonl.gz`.
- `test_gmp_qualification.py` — TEST-GMP-001/002/003 : intégrité SHA-256 du golden, parité OpenAPI/manifests, 100 % factual accuracy, math ±0.01, flux air-gapped, calibration.
- Fixture : `tests/fixtures/gmp_projet04_golden.json` (13 cas SIP/CIP, brides, cleanroom ; SHA-256 `250e43a4…`).

**TypeScript — `packages/db/tests/` (Vitest + better-sqlite3)**
- `schema.test.ts` — TEST-DB-001 (colonnes des 4 tables) + TEST-DB-002 (seed, FK, append-only).
- `gmp.test.ts` — TEST-GMP-004 (21 CFR Part 11 : hash déterministe, rejet UPDATE/DELETE).

**TypeScript — `apps/telemetry-worker/src/` (Vitest)**
- `index.test.ts` — TEST-TEL-001..004 (ingestion 202, 401 non-auth, signature SHA-256 missing/invalid/valid, cron `scheduled`).
- `benchmark.test.ts` — benchmark p99 d'ingestion `< 15 ms` (1000 échantillons).

**TypeScript — `apps/portal/src/` + `e2e/` (Vitest jsdom + Playwright)**
- `SizeAuditForm.test.ts` — TEST-UI-001 : rendu des 3 modes, validation erreur, rendu TCO/VRAM, erreur serveur, erreur réseau, décimales à virgule + UUID unique.
- `schemas.test.ts` — TEST-INT-001 : parité clés Zod ↔ OpenAPI/Pydantic.
- `config.test.ts` — normalisation d'URL (`normalizeUrl`).
- `audit.test.ts` — helpers SHA-256 / audit submission / UUID.
- `e2e/audit.spec.ts` — TEST-INT-001 E2E : parcours complet 3 modes + proxy batch-upload.

### 6.2 Portes CI (` .github/workflows/ci-cmmi-gate.yml`)

Le workflow exécute (Gate 0..10) : présence RTM ; `uv sync --frozen` ; `ruff check` ; `mypy --strict core api tests` ; `pytest --cov=core --cov=api --cov-branch --cov-fail-under=95 --junitxml` (+ archives JUnit/coverage) ; `pnpm install --frozen-lockfile` ; `eslint` ; `tsc --noEmit` (db, worker, portal) ; `vitest` db ; `drizzle-kit check` ; `vitest` worker ; `vitest` portal ; `vite build` portal.

---

## 7. Flux de Données End-to-End (Séquences complètes)

### 7.1 Flux A — Soumission d'un audit d'architecture (`POST /api/audit`)

1. **UI** : l'utilisateur remplit `SizeAuditForm.svelte` (5 sections), clique « Size architecture ».
2. `submit()` : valide `technicians`, construit le payload via `sizeRequestSchema.parse(...)` avec `audit_id = randomUuid()` et `parseDecimal` sur chaque champ numérique.
3. `fetch('/api/audit', { method: 'POST', body: JSON.stringify(payload) })`.
4. **BFF** (`api/audit/+server.ts`) : parse + `safeParse` (400 si invalide).
5. **D1 snapshot** : `db.prepare('SELECT id FROM hardware_catalog LIMIT 1')` + `model_registry` (502 si D1 indisponible — RSK-004).
6. **Sizing Engine** : `fetch(SIZING_ENGINE_URL + '/api/v1/size-architecture')` → FastAPI `size_architecture` exécute `compute_active_streams` → `compute_total_child_chunks` → `compute_vram_allocation` → `compute_3year_tco`, retourne le verdict JSON.
7. **Persistance append-only** : le BFF calcule `input_payload_sha256`/`output_payload_sha256` (`buildAuditSubmission`, `actor_id='portal-bff'`) puis `INSERT INTO audit_submissions` (18 colonnes). Tout `UPDATE`/`DELETE` ultérieur est bloqué par les triggers 21 CFR.
8. **UI** : `result` est affecté ; `Step 2 — Results` affiche CAPEX/OPEX, ventilation VRAM, chunks, décision recommandée.

### 7.2 Flux B — Import par lots (`POST /api/batch-upload`)

1. Un client air-gapped envoie un binaire `.jsonl.gz` + en-tête `X-Batch-Signature-SHA256` (+ éventuel `Authorization`) à `POST /api/batch-upload`.
2. **BFF** (`api/batch-upload/+server.ts`) : lit `arrayBuffer`, propage la signature, injecte `Bearer ${env.AUTH_TOKEN}`, forwarde vers `TELEMETRY_WORKER_URL + '/api/v1/telemetry/batch-upload'`.
3. **Worker** : vérifie Bearer (401 sinon), vérifie signature SHA-256 du corps (400 absent / 401 invalide), stocke dans R2 `telemetry/batches/{ts}.jsonl.gz` via `ctx.waitUntil`.
4. **BFF** : retourne `202` (ou `502`).

### 7.3 Flux C — Remontée de télémétrie (`telemetry-worker`)

1. **Temps réel** : un client edge POST `/api/v1/telemetry/event` avec Bearer → le Worker valide la forme et écrit `telemetry/events/{ts}.json` dans R2 (202).
2. **Cron quotidien** (`0 3 * * *`) : `scheduled()` lit la dernière ligne `telemetry_calibration` (JOIN `hardware_catalog`), évalue la Loop 1, et persiste `compute_scaling_multiplier` dans D1 (incrément +0.20 si déclenché).
3. **Boucle de fermeture** : le résultat de calibration (`M_calib`) alimente les calculs futurs du sizing engine (multiplier `calibration_multiplier` dans `compute_vram_allocation`), tandis que les boucles Loop 2/3 sont évaluées hors ligne (`core/calibration.py::evaluate_calibration_loops`) sur des métriques RAGAS échantillonnées à 5 %.

---

## Annexe — Points de repère rapides

- **Vecteur de référence `aud-gmao-2026-001`** : 35 techs × 0.40 → 14 streams ; weights 1.85 / KV 4.66 / vectorDB 1.15 / reranker 2.0 → **10.96 GB VRAM** ; 901 313 chunks ; 2× L4 24GB ; CAPEX 26 458.24 vs OPEX 54 531.94 → **CAPEX_ON_PREM_EDGE**.
- **Exigences P0/P1** : `REQ-DB-001`, `REQ-MATH-001/002/003`, `REQ-FIN-001`, `REQ-API-001`, `REQ-SAFE-001`, `REQ-CAL-001/002`.
- **Risques FMEA** : `RSK-001` hallucination numérique/citation, `RSK-002` Edge GPU OOM, `RSK-003` (télémétrie/calibration), `RSK-004` D1 indisponible.
- **Baselines** : `BL-01-INIT`, `BL-02-DATA`, `BL-03-CORE`, `BL-04-TELEM`, `BL-05-INTEG`, `BL-06-REL-1.0` (tous ✅ Complete).
- **Fichier non suivi** présent au moment de l'analyse : `docs/tutoriel_cli_glossaire_d_ploiement_rag_architect.md` (tutoriel CLI + glossaire de déploiement, non committé).
