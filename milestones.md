Decomposition of the **RAG-Architect for GMAO (v3.0)** project follows a 6-week (30-working-day) plan structured around six sequential and partially overlapping milestones (M1 through M6). In accordance with **CMMI-DEV Level 3 ("Defined")**, every milestone enforces strict **Entry Criteria**, **TDD Red-Green-Refactor execution**, **CMMI Process Area (PA) alignment**, **Process & Product Quality Assurance (PPQA) gates**, and formal **Configuration Management (CM) baselines** (BL-01 to BL-06).

## **1\. Master Milestone Schedule & CMMI-3 Alignment Matrix**

| Milestone ID | Milestone Name | Duration | Target Window | Primary CMMI-3 Process Areas | TDD Cycle Mandate | CM Baseline Tag |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **M1** | **Project Tailoring, RTM & Monorepo Baseline** | 4 Days | Week 1 (D1–D4) | PP, PMC, CM, RD, REQM, RSKM | Test Harness & CI Failure Gate Setup | BL-01-INIT |
| **M2** | **Edge Relational Persistence & Catalog Baseline** | 4 Days | Week 1–2 (D5–D8) | TS, REQM, VER, CM, PPQA | Schema & Seed Constraint TDD | BL-02-DATA |
| **M3** | **Core Mathematical Sizing Engine & Safety Gate** | 7 Days | Week 2–3 (D9–D15) | TS, VER, RSKM, DAR, PPQA | 100% Red-Green-Refactor (pytest) | BL-03-CORE |
| **M4** | **Telemetry Ingestion Pipeline & Auto-Calibration** | 6 Days | Week 4 (D16–D21) | TS, PI, VER, CM, RSKM | Edge Worker & Batch Loop TDD | BL-04-TELEM |
| **M5** | **Audit Portal UI & Multi-Tier System Integration** | 5 Days | Week 5 (D22–D26) | PI, TS, VER, VAL, CM | Component & E2E Contract TDD | BL-05-INTEG |
| **M6** | **GMP Qualification (Projet 04), FCA/PCA & Handover** | 4 Days | Week 6 (D27–D30) | VAL, VER, CM, PPQA, OPF | Golden Dataset Non-Regression | BL-06-REL-1.0 |

## **2\. Detailed Milestone Breakdown (Work Packages & Gates)**

### **Milestone 1 (M1): Project Tailoring, RTM & Monorepo Baseline (Days 1–4)**

Establishes the organizational standard software process (OSSP) tailoring, locks the Bidirectional Requirements Traceability Matrix (RTM), initializes the monorepo, and configures automated CI/CD quality gates before any functional code is written.

* **CMMI Process Areas:**  
  * **RD & REQM (Requirements Development & Management):** Freeze requirements REQ-DB-001 through REQ-CAL-002 and link each to its verification test ID (TEST-\*).  
  * **CM (Configuration Management):** Initialize Git repository structure (apps/portal, apps/telemetry-worker, services/sizing-engine, packages/db), branch protection rules, and conventional commit hooks (feat(REQ-xxx): ...).  
  * **RSKM (Risk Management):** Baseline the Failure Mode and Effects Analysis (FMEA) risk register (RSK-001 to RSK-004).  
* **TDD Execution Scope:**  
  * Configure uv workspace in services/sizing-engine with pytest, pytest-cov, mypy \--strict, and ruff.  
  * Configure Vitest / Playwright in apps/ and packages/db.  
  * Verify that CI pipelines automatically fail when test coverage is \< 95% or when no tests exist.  
* **Deliverables (Work Products):**  
  * Tailored Project Plan & FMEA Risk Register.  
  * Signed Bidirectional RTM (docs/cmmi/rtm-v3.md).  
  * Monorepo skeleton with active GitHub/GitLab CI/CD pipelines.  
* **Exit Criteria & PPQA Gate (BL-01-INIT):**  
  * 100% of requirements have a mapped TEST-\* identifier.  
  * CI pipeline executes linters (ruff, eslint) and type-checkers (mypy, tsc) with zero errors.

### **Milestone 2 (M2): Edge Relational Persistence & Catalog Baseline (Days 5–8)**

Implements the Cloudflare D1 SQLite relational schema via Drizzle ORM and seeds the verified baseline hardware and LLM architectural specifications.

* **Entry Criteria:** BL-01-INIT signed off.  
* **CMMI Process Areas:**  
  * **TS (Technical Solution):** Design and implement normalized schemas in packages/db/src/schema.ts (hardwareCatalog, modelRegistry, auditSubmissions, telemetryCalibration).  
  * **VER (Verification):** Peer review SQL migrations and foreign key constraints.  
* **TDD Execution Scope:**  
  * **Phase RED:** Write schema validation and seed integrity tests (TEST-DB-001, TEST-DB-002) asserting the presence of qHeadCount, headDim, kvCacheBits, avgTokensPerPage, avgQueriesPerTechShift, and electricityRateKwhUsd, plus foreign key enforcement on telemetryCalibration.  
  * **Phase GREEN:** Implement Drizzle schemas, generate SQLite migrations via drizzle-kit, and write deterministic seed scripts (rugged-edge-a4500 with 40GB Dual-GPU VRAM, nvidia-l40s with 48GB VRAM, edgestream-gw-01, and llama-3.2-3b-instruct-q4).  
  * **Phase REFACTOR:** Optimize SQLite indexes on lookup keys (model\_id, hardware\_id, deployment\_constraint).  
* **Deliverables (Work Products):**  
  * packages/db/src/schema.ts, SQL migration files, and seed script (seed.ts).  
  * Automated D1 local test suite report.  
* **Exit Criteria & PPQA Gate (BL-02-DATA):**  
  * npx drizzle-kit check passes with zero drift.  
  * TEST-DB-001 and TEST-DB-002 pass at 100% on local D1 SQLite instance.

### **Milestone 3 (M3): Core Mathematical Sizing Engine & Zero-Hallucination Gate (Days 9–15)**

Develops the Python 3.12 mathematical microservice (services/sizing-engine) handling GQA KV Cache computation, VRAM allocation, 36-month CAPEX/OPEX TCO modeling, and the safety-critical citation/numeric verification gate.

* **Entry Criteria:** BL-02-DATA signed off.  
* **CMMI Process Areas:**  
  * **TS & DAR (Decision Analysis and Resolution):** Implement deterministic mathematical models for VRAM headroom (\$20\\%\$), HNSW index overhead (${F}_{index}=1.25$), and RRF hybrid parameters ($k=60$).  
  * **RSKM & VER:** Mitigate RSK-001 (OOM on factory edge) and RSK-002 (numeric hallucination on torque/pressure values) via strict unit verification.  
* **TDD Execution Scope:**  
  * **Phase RED:** Commit the complete test suite (tests/test\_calculator.py covering TEST-MATH-001 to TEST-MATH-003 and TEST-FIN-001, tests/test\_gate.py covering TEST-SAFE-001, and tests/test\_api.py covering TEST-API-001) and record the initial failure log (ImportError / AssertionError).  
  * **Phase GREEN:**  
    1. Implement core/calculator.py: concurrency (\$\\lceil 35 \\times 0.40 \\rceil \= 14\$), KV Cache ($4.66GB$), chunk estimation ($901,313chunks$), total VRAM ($10.96GB$), and 3-year TCO ($26,458.24USDCAPEX$ vs $54,531.94USDOPEX$).  
    2. Implement core/gate.py: regex and AST numeric extractor verifying that every numeric quantity (Nm, bar, V, °C) and SOP citation in generated answers exists verbatim in retrieved parent chunks.  
    3. Implement api/routes.py: FastAPI endpoint POST /api/v1/size-architecture with strict Pydantic v2 models.  
  * **Phase REFACTOR:** Vectorize calculations with NumPy and enforce zero-warning mypy \--strict typing.  
* **Deliverables (Work Products):**  
  * Containerized Python 3.12 sizing microservice (Dockerfile \+ pyproject.toml managed by uv).  
  * JUnit XML test report and coverage artifact.  
* **Exit Criteria & PPQA Gate (BL-03-CORE):**  
  * 100% pass rate on TEST-MATH-\*, TEST-FIN-\*, TEST-SAFE-\*, and TEST-API-\* with \$\\ge 95\\%\$ branch coverage.  
  * Exact numerical match with the reference JSON specification (aud-gmao-2026-001).

### **Milestone 4 (M4): Telemetry Ingestion Pipeline & Closed-Loop Auto-Calibration (Days 16–21)**

Builds the Cloudflare Worker ingestion service (apps/telemetry-worker), the offline air-gapped JSONL batch importer, and the 3-loop auto-calibration engine.

* **Entry Criteria:** BL-03-CORE signed off.  
* **CMMI Process Areas:**  
  * **TS & PI (Product Integration):** Implement dual-mode ingestion (real-time HTTP streaming to Cloudflare R2 for connected plants; signed JSONL batch upload for AIR\_GAPPED\_EDGE plants).  
  * **VER:** Verify asynchronous 5% RAGAS sampling so edge inference latency (TTFT $\leq 1.5s$) is never impacted by evaluation overhead.  
* **TDD Execution Scope:**  
  * **Phase RED:** Commit tests/test\_calibration.py (TEST-CAL-001 and TEST-CAL-002) and Worker unit tests (TEST-TEL-001, TEST-TEL-002).  
  * **Phase GREEN:**  
    1. Implement apps/telemetry-worker/src/index.ts for POST /api/v1/telemetry/event and POST /api/v1/telemetry/batch-upload with Bearer token validation and non-blocking ctx.waitUntil() R2 writes.  
    2. Implement services/sizing-engine/core/calibration.py executing Loop 1 (\$+20\\%\$ compute scaling if P95 TTFT $>1500ms$ or VRAM \$\> 90\\%\$), Loop 2 (\$-20\\%\$ child chunk size if Context Recall $<0.75$), and Loop 3 (Semantic Router provisioning if cloud token spend exceeds baseline by \$\> 15\\%\$).  
  * **Phase REFACTOR:** Harden SHA-256 signature verification on air-gapped batch uploads.  
* **Deliverables (Work Products):**  
  * Cloudflare Worker deployment package (wrangler.toml, src/index.ts).  
  * Calibration engine module (core/calibration.py) and scheduled cron handler.  
* **Exit Criteria & PPQA Gate (BL-04-TELEM):**  
  * Worker ingestion p99 overhead $<15ms$ in Miniflare/Wrangler local simulation.  
  * All calibration state transitions (Loop 1, Loop 2, Loop 3\) verified by automated tests and persisted in D1 telemetryCalibration.

### **Milestone 5 (M5): Audit Portal UI & Multi-Tier System Integration (Days 22–26)**

Develops the SvelteKit \+ Tailwind CSS qualification workbench (apps/portal) and integrates all four architectural tiers end-to-end.

* **Entry Criteria:** BL-02-DATA, BL-03-CORE, and BL-04-TELEM signed off.  
* **CMMI Process Areas:**  
  * **PI (Product Integration):** Connect SvelteKit Server Actions (apps/portal/src/routes/api/audit/) to Cloudflare D1 (packages/db) and the Python Sizing Engine (services/sizing-engine).  
  * **VAL (Validation):** Validate UI workflows against plant reliability engineer user journeys.  
* **TDD Execution Scope:**  
  * **Phase RED:** Write Playwright E2E and Vitest component tests (TEST-UI-001, TEST-INT-001) asserting form validation, air-gapped constraint toggles, and 3-year CAPEX vs. OPEX chart rendering.  
  * **Phase GREEN:** Build the multi-step qualification interface in \+page.svelte, server-side proxy actions, and interactive TCO/VRAM breakdown visualizations.  
  * **Phase REFACTOR:** Enforce accessibility (WCAG AA contrast for factory floor tablets) and responsive layout for Panasonic Toughbook G2 viewports.  
* **Deliverables (Work Products):**  
  * Full SvelteKit portal ready for deployment at smartmaintenance.helveticore.com.  
  * End-to-End integration test report across Pages, D1, R2, and Python Docker container.  
* **Exit Criteria & PPQA Gate (BL-05-INTEG):**  
  * Zero contract mismatches between TypeScript Zod/Drizzle schemas and Python Pydantic schemas.  
  * E2E Playwright suite passes across all three deployment modes (AIR\_GAPPED\_EDGE, HYBRID\_CONNECTED, FULL\_CLOUD).

### **Milestone 6 (M6): GMP Qualification (Projet 04), FCA/PCA Audit & Release (Days 27–30)**

Executes formal validation against the regulated pharmaceutical/GMP reference case (**Projet 04 — SOP / Manuels GMP**), conducts the Functional and Physical Configuration Audits (FCA/PCA), and releases version 1.0.

* **Entry Criteria:** BL-05-INTEG signed off.  
* **CMMI Process Areas:**  
  * **VAL (Validation):** Execute the GMP Qualification Protocol (IQ/OQ/PQ) using the reference dataset (SIP/CIP sterilization sequences, flange torque tables, cleanroom gowning SOPs).  
  * **CM & PPQA:** Perform formal **Functional Configuration Audit (FCA)** (verifying every RTM requirement test is green) and **Physical Configuration Audit (PCA)** (verifying Docker images, D1 migrations, and documentation match the repository tag).  
* **TDD Execution Scope:**  
  * Execute the signed non-regression golden test suite (TEST-GMP-001 to TEST-GMP-004) verifying **100% factual accuracy** (zero ungrounded torque/pressure numbers allowed through the gate) and immutable audit trail logging (21 CFR Part 11 readiness).  
* **Deliverables (Work Products):**  
  * Signed Software Validation Report (PV de Qualification) & Immutable Audit Trail verification.  
  * FCA/PCA Compliance Certificate & Production Release BL-06-REL-1.0.  
* **Exit Criteria & PPQA Gate (BL-06-REL-1.0):**  
  * 100% pass rate on the full RTM test matrix (\$\\ge 95\\%\$ code coverage overall).  
  * Zero open Critical or High severity defects; formal sign-off for production deployment on smartmaintenance.helveticore.com.

## **3\. Critical Path & Dependency Sequence**

\[M1: Tailoring, RTM & CI Setup (BL-01)\]  
                  │  
                  ▼  
\[M2: D1 Schema & Catalog Seed (BL-02)\]  
        │                     │  
        ▼                     ▼  
\[M3: Python Sizing    \[M4: Telemetry Worker  
 & Safety Gate (BL-03)\]    & Calibration (BL-04)\]  
        │                     │  
        └──────────┬──────────┘  
                   ▼  
\[M5: SvelteKit Portal & 4-Tier Integration (BL-05)\]  
                   │  
                   ▼  
\[M6: GMP Projet 04 Qualification & FCA/PCA Release (BL-06)\]

* **Parallelization Opportunity:** Once **M2 (BL-02-DATA)** locks the Drizzle D1 schemas and seed data on Day 8, **M3 (Python Sizing Engine)** and the ingestion portion of **M4 (Cloudflare Telemetry Worker)** can run in parallel before converging on Day 18 for the closed-loop calibration integration.

Would you like me to generate the **Milestone 1 & Milestone 2 execution files** (the packages/db/src/schema.ts, seed.ts, and the Phase RED pytest test files) so you can initialize BL-01-INIT and BL-02-DATA immediately?