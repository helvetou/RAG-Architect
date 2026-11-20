# Technical Specification: RAG-Architect for GMAO (Smart Maintenance) — v2.1

This document establishes the end-to-end technical, architectural, and data engineering requirements for **RAG-Architect for GMAO**, targeted for deployment at `rag-architect.helveticore.com`. It provides a deterministic, implementation-ready specification for engineering teams and coding agents building the automated audit, sizing, and telemetry calibration platform.

> **Scope Clarification for Coding Agents:** Sections 1 through 7 specify the **RAG-Architect Sizing & Calibration Platform** (the software to be built in this repository). Section 8 is a **Reference Case Study Appendix** (in French) illustrating how a target industrial RAG deployment looks in production once sized by this platform.

---

## 1. System Vision & Architecture Overview

The system addresses the operational realities of factory floor operations, where plant reliability engineers and field maintenance technicians require immediate, highly accurate diagnostic information. In these environments, downtime costs can reach tens of thousands of dollars per hour, and hallucinations concerning torque specifications, electrical lockouts, or hydraulic pressures represent unacceptable physical hazards.

RAG-Architect for GMAO functions as a specialized decision-support and telemetry-driven calibration workbench. It translates factory operating parameters—such as technician headcount per shift, documentation volume, and network isolation constraints—into rigorous hardware configurations, KV Cache budgets, and 3-year total cost of ownership (TCO) models.

### 1.1 Decoupled Multi-Tier Topology

The platform separates client-facing interactions, specification metadata, compute-heavy sizing calculations, and asynchronous telemetry collection across four decoupled tiers. Because Cloudflare D1 does not expose direct external TCP connections, the SvelteKit Backend-for-Frontend (BFF) queries D1 on the edge and passes the catalog context directly in the payload to the Python Sizing Engine container.

```
+-------------------------------------------------------------------------+
|                 1. Audit Portal & Edge BFF (Front-End)                  |
|              SvelteKit + Tailwind CSS on Cloudflare Pages               |
|                   rag-architect.helveticore.com                         |
+-----------------+-----------------------------------+-------------------+
                  |                                   |
                  | 1a. Fetch Catalog & Rules         | 1b. POST /api/v1/size-architecture
                  v                                   |     (Includes Catalog Snapshot)
+-----------------------------------+                 v
|  3. Knowledge Base (D1 SQLite)    |   +---------------------------------+
|      Drizzle ORM on CF Edge       |   | 2. Sizing Engine (Backend)      |
|  Hardware Specs, Pricing & Rules  |   | Python 3.12 + uv (Docker / Fly) |
+-----------------------------------+   | - VRAM & KV Cache Calculator    |
                  ^                     | - 3-Year TCO Generator          |
                  |                     | - Telemetry Calibrator          |
                  | Update Weights      +---------------------------------+
                  |                                   ^
+-----------------+-----------------------------------+-------------------+
|                      4. Telemetry Ingestion Pipeline                    |
|              Cloudflare Workers + R2 Bucket (Connected Mode)            |
|        OR Local Edge JSONL Buffer + Batch Upload (Air-Gapped Mode)      |
+-------------------------------------------------------------------------+
```

1. **Audit Portal & Edge BFF (Front-End):** A responsive qualification interface built with SvelteKit and Tailwind CSS, hosted on Cloudflare Pages. Its server routes query Cloudflare D1 via Drizzle ORM, bundle operational inputs with hardware/model catalogs, and invoke the Python Sizing Engine.
2. **Core Sizing Engine (Backend):** A stateless, high-performance Python 3.12 microservice managed with `uv` and packaged within a Docker container (deployed on Cloudflare Containers, Fly.io, or Cloud Run). It executes deterministic mathematical models for transformer memory consumption, KV Cache allocation, vector database footprints, and 3-year CAPEX versus OPEX financial projections.
3. **Knowledge Base (Pricing & Specifications):** A low-latency edge relational datastore hosted on Cloudflare D1 and managed via Drizzle ORM. It maintains structured catalogs of cloud GPU instances, ruggedized edge servers, IoT edge gateways, model architectures, and rolling calibration coefficients.
4. **Telemetry Ingestion Pipeline (Dual-Mode):**
   * **Connected / Hybrid Mode:** An asynchronous ingestion service on Cloudflare Workers that receives real-time operational traces from rugged tablets, buffers raw JSON payloads in Cloudflare R2, and triggers nightly calibration jobs.
   * **Air-Gapped Mode (`AIR_GAPPED_EDGE`):** Tablets log traces to a local SQLite/JSONL ring buffer on the factory Edge server. Administrators periodically export signed `.jsonl.gz` telemetry bundles and upload them via `POST /api/v1/telemetry/batch-upload` on the Audit Portal.

---

## 2. Relational Schema & Data Dictionary (Cloudflare D1 via Drizzle ORM)

All persistence operations for catalog specifications, audit records, and rolling calibration metrics are governed by Drizzle ORM schemas compiled to Cloudflare D1 SQLite.

### 2.1 Schema Definition (`packages/db/src/schema.ts`)

```typescript
import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';

// Hardware Specifications & Cost Catalog
export const hardwareCatalog = sqliteTable('hardware_catalog', {
  id: text('id').primaryKey(), // e.g., 'rugged-edge-l4-24g', 'rugged-dual-a4500-40g', 'nvidia-l40s'
  name: text('name').notNull(),
  tier: text('tier').notNull(), // 'EDGE_RUGGED_SERVER', 'EDGE_GATEWAY', 'CLOUD_HOSTED_GPU'
  vramGb: real('vram_gb').notNull(),
  systemRamGb: real('system_ram_gb').notNull(),
  tdpWatts: integer('tdp_watts').notNull(),
  unitCostCapexUsd: real('unit_cost_capex_usd').default(0.0).notNull(), // Initial acquisition
  monthlyMaintOpexUsd: real('monthly_maint_opex_usd').default(0.0).notNull(), // Hardware support or Cloud rental fee
  maxBandwidthGbps: real('max_bandwidth_gbps').notNull()
});

// Large Language Model Architectural Parameters
export const modelRegistry = sqliteTable('model_registry', {
  id: text('id').primaryKey(), // e.g., 'llama-3.2-3b-instruct-q4', 'claude-3-5-sonnet'
  name: text('name').notNull(),
  parameterCountB: real('param_count_b').notNull(),
  contextWindowTokens: integer('context_window_tokens').notNull(),
  hiddenDimension: integer('hidden_dim').notNull(),
  layerCount: integer('layer_count').notNull(),
  qHeadCount: integer('q_head_count').notNull(),   // Query attention heads (H_Q)
  kvHeadCount: integer('kv_head_count').notNull(), // Key-Value heads for GQA (H_KV)
  headDim: integer('head_dim').notNull(),          // Explicit head dimension (D_head)
  weightQuantBits: integer('weight_quant_bits').notNull(), // 4, 8, 16
  kvCacheBits: integer('kv_cache_bits').default(16).notNull(), // 8 (FP8/INT8) or 16 (FP16/BF16)
  inputTokenCostPer1M: real('input_token_cost_1m').default(0.0).notNull(),
  outputTokenCostPer1M: real('output_token_cost_1m').default(0.0).notNull(),
  isEdgeCompatible: integer('is_edge_compatible', { mode: 'boolean' }).notNull()
});

// GMAO Qualification Submissions
export const auditSubmissions = sqliteTable('audit_submissions', {
  id: text('id').primaryKey(), // UUID v4
  clientName: text('client_name').notNull(),
  techniciansPerShift: integer('techs_per_shift').notNull(),
  totalShifts: integer('total_shifts').default(3).notNull(),
  manualsVolumeGb: real('manuals_volume_gb').notNull(),
  historicalWorkOrdersCount: integer('work_orders_count').notNull(),
  avgTokensPerPage: integer('avg_tokens_per_page').default(420).notNull(),
  deploymentConstraint: text('deployment_constraint').notNull(), // 'AIR_GAPPED_EDGE', 'HYBRID_CONNECTED', 'FULL_CLOUD'
  peakQueryRatio: real('peak_query_ratio').default(0.40).notNull(), // Concurrency during shift changeovers
  avgQueriesPerTechShift: integer('avg_queries_per_tech_shift').default(15).notNull(),
  electricityRateKwhUsd: real('electricity_rate_kwh_usd').default(0.18).notNull(),
  targetP95TtftSeconds: real('target_p95_ttft_seconds').default(1.5).notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull()
});

// Multi-Tier Telemetry Calibration State
export const telemetryCalibration = sqliteTable('telemetry_calibration', {
  id: text('id').primaryKey(), // Synthetic key: modelId + '_' + hardwareId
  modelId: text('model_id').notNull().references(() => modelRegistry.id),
  hardwareId: text('hardware_id').notNull().references(() => hardwareCatalog.id),
  measuredP95TtftMs: real('measured_p95_ttft_ms').notNull(),
  measuredPeakVramGb: real('measured_peak_vram_gb').notNull(),
  measuredContextRecall: real('measured_context_recall').notNull(), // Evaluated asynchronously
  measuredFaithfulness: real('measured_faithfulness').notNull(),   // Evaluated asynchronously
  computeScalingMultiplier: real('compute_scaling_multiplier').default(1.0).notNull(),
  rollingSampleCount: integer('rolling_sample_count').notNull(),
  lastUpdated: integer('last_updated', { mode: 'timestamp' }).notNull()
});
```

---

## 3. Mathematical Foundations & Sizing Engine

The calculation engine (`services/sizing-engine/core/calculator.py`) translates empirical operational loads into concrete hardware requirements. All memory calculations are computed in bytes and converted to Gigabytes ($\text{GB} = 10^9\text{ bytes}$).

### 3.1 KV Cache Memory Consumption

During inference, autoregressive generation caches intermediate Key and Value tensors for all prior tokens in the sequence. For architectures incorporating Grouped-Query Attention (GQA), the KV Cache memory consumption in bytes is governed by:

$$\text{Memory}_{\text{KV Cache (Bytes)}} = 2 \times B_{\text{active}} \times S \times L \times H_{\text{KV}} \times D_{\text{head}} \times \left(\frac{\text{Bits}_{\text{KV}}}{8}\right)$$

Where:
* $2$: Factor accounting for Key and Value matrices.
* $B_{\text{active}}$: Peak concurrent active streams:
  $$B_{\text{active}} = \lceil N_{\text{techs}} \times R_{\text{peak}} \rceil$$
  ($N_{\text{techs}}$ is technicians per shift; $R_{\text{peak}}$ is the peak query ratio during shift handovers).
* $S$: Total active sequence length per stream. By default, for GMAO Parent-Child retrieval:
  $$S = \text{Tokens}_{\text{system\_prompt}} + (\text{TopK}_{\text{generator}} \times \text{Chunk}_{\text{parent}}) + \text{Tokens}_{\text{output}}$$
  With standard baseline defaults ($\text{Tokens}_{\text{system\_prompt}} = 400$, $\text{TopK}_{\text{generator}} = 5$, $\text{Chunk}_{\text{parent}} = 1000$, $\text{Tokens}_{\text{output}} = 400$), $S = 5\,800\text{ tokens}$.
* $L$: Total number of transformer layers (`layerCount`).
* $H_{\text{KV}}$: Number of Key-Value attention heads (`kvHeadCount`).
* $D_{\text{head}}$: Attention head dimension (`headDim`, typically $\frac{D_{\text{model}}}{H_{\text{Q}}}$).
* $\text{Bits}_{\text{KV}}$: KV Cache quantization bit-width (`kvCacheBits`, e.g., $16$ for FP16 or $8$ for FP8/INT8).

### 3.2 Document-to-Chunk Conversion & Total VRAM Allocation

Before computing vector index memory, the engine converts raw document metrics into total indexed child chunks ($N_{\text{chunks}}$):

1. **Manuals Token Volume:** Industrial PDF manuals containing schematics and tables average $2\,500\text{ pages per GB}$:
   $$\text{Tokens}_{\text{manuals}} = \text{Manuals}_{\text{GB}} \times 2500 \times \text{AvgTokensPerPage}$$
2. **Work Orders Token Volume:** Historical maintenance logs average $150\text{ tokens per record}$:
   $$\text{Tokens}_{\text{WO}} = N_{\text{work\_orders}} \times 150$$
3. **Total Child Chunks ($N_{\text{chunks}}$):** Accounting for a $15\%$ sliding-window chunk overlap ($1.15$):
   $$N_{\text{chunks}} = \left\lceil \frac{\text{Tokens}_{\text{manuals}} + \text{Tokens}_{\text{WO}}}{\text{Chunk}_{\text{child}}} \times 1.15 \right\rceil$$

To prevent Out-Of-Memory (OOM) faults on rugged factory edge hosts, total allocated VRAM must satisfy:

$$\text{VRAM}_{\text{Total}} = \left(\text{VRAM}_{\text{Weights}} + \text{VRAM}_{\text{KV Cache}} + \text{VRAM}_{\text{VectorDB}} + \text{VRAM}_{\text{Reranker}} + \text{VRAM}_{\text{Headroom}}\right) \times M_{\text{calib}}$$

Where $M_{\text{calib}}$ is the `computeScalingMultiplier` from `telemetryCalibration` (defaults to $1.0$).

1. **Weights Footprint (GB):**
   $$\text{VRAM}_{\text{Weights}} = P_{\text{model (Billions)}} \times \left( \frac{\text{WeightQuantBits}}{8} \right) \times 1.15$$
   (Includes $15\%$ overhead for CUDA context and activation buffers).
2. **GPU Vector Index Footprint (GB):** If the vector database is hosted in VRAM/Unified Memory for sub-50ms retrieval (using `bge-m3` with $D_{\text{embedding}} = 1024$):
   $$\text{VRAM}_{\text{VectorDB}} = \frac{N_{\text{chunks}} \times D_{\text{embedding}} \times B_{\text{precision}} \times F_{\text{index}}}{10^9}$$
   (Where $B_{\text{precision}} = 2\text{ bytes}$ for FP16 or $1\text{ byte}$ for SQ8, and $F_{\text{index}} = 1.25$ for HNSW graph overhead).
3. **Cross-Encoder Reranker + Embedding Resident Footprint:** Fixed resident overhead $\text{VRAM}_{\text{Reranker}} = 2.0\text{ GB}$ (`bge-m3` + `bge-reranker-base`).
4. **Safety Margin:** An operational buffer of $\text{VRAM}_{\text{Headroom}} = 0.20 \times (\text{VRAM}_{\text{Weights}} + \text{VRAM}_{\text{KV Cache}})$.

### 3.3 Three-Year TCO Financial Formulation

The platform computes a 36-month cost comparison between local capital expenditure (`CAPEX_ON_PREM_EDGE`) and cloud operational consumption (`OPEX_CLOUD_MANAGED`).

First, monthly query volume ($\text{Volume}_{\text{monthly}}$) is derived from shift parameters (assuming $30.4\text{ days/month}$):
$$\text{Volume}_{\text{monthly}} = N_{\text{techs}} \times N_{\text{shifts}} \times Q_{\text{tech\_shift}} \times 30.4$$

1. **3-Year Edge CAPEX TCO:**
   $$\text{TCO}_{\text{CAPEX}} = \left(\text{UnitCost}_{\text{HW}} \times Q\right) + \sum_{m=1}^{36} \left( \frac{\text{TDP}_{\text{Watts}} \times Q \times 730 \times \text{Rate}_{\text{kWh}}}{1000} + \left(\text{Maint}_{\text{monthly}} \times Q\right) \right)$$
   *(Where $Q$ is the required hardware unit quantity: $Q = \lceil \text{VRAM}_{\text{Total}} / \text{VRAM}_{\text{Unit}} \rceil$, and $730$ is average hours per month).*

2. **3-Year Cloud OPEX TCO:**
   $$\text{TCO}_{\text{OPEX}} = \sum_{m=1}^{36} \left[ \left( \frac{S_{\text{in}} \times \text{Price}_{\text{in\_1M}} + S_{\text{out}} \times \text{Price}_{\text{out\_1M}}}{10^6} \right) \times \text{Volume}_{\text{monthly}} + \text{CloudVectorHost}_{\text{monthly}} \right]$$

---

## 4. API Specification & Interface Contracts

The system communicates through strict REST JSON endpoints validated via Pydantic v2 schemas.

### 4.1 Architecture Sizing Endpoint

`POST /api/v1/size-architecture`

#### Request Body
```json
{
  "audit_id": "aud-gmao-2026-001",
  "client_name": "Helvetic Precision Manufacturing",
  "deployment_constraint": "AIR_GAPPED_EDGE",
  "technicians_per_shift": 35,
  "total_shifts": 3,
  "documents": {
    "equipment_manuals_pdf_gb": 85.0,
    "historical_work_orders_count": 450000,
    "average_tokens_per_page": 420
  },
  "concurrency": {
    "peak_shift_overlap_ratio": 0.40,
    "avg_queries_per_tech_shift": 15,
    "target_p95_ttft_seconds": 1.5
  },
  "financials": {
    "electricity_rate_kwh_usd": 0.18
  },
  "safety_critical": true
}
```

#### Response Body (Mathematically Verified Baseline)
*Note on worked values below:*
* $B_{\text{active}} = \lceil 35 \times 0.40 \rceil = 14\text{ concurrent streams}$.
* `llama-3.2-3b-instruct-q4` ($L=28, H_{KV}=8, D_{head}=128$) with INT8 KV Cache ($\text{Bits}_{\text{KV}}=8$) and $S=5800\text{ tokens}$ yields $\text{VRAM}_{\text{KV Cache}} = 4.55\text{ GB}$.
* Total VRAM required (Weights $1.73\text{ GB}$ + KV Cache $4.55\text{ GB}$ + VectorDB SQ8 Index $0.72\text{ GB}$ + Reranker $2.0\text{ GB}$ + Headroom $1.26\text{ GB}$) $= 10.26\text{ GB}$, fitting comfortably on **1× Rugged Server with NVIDIA L4 (24 GB VRAM)** or **1× Dual-A4500 (40 GB VRAM)**. Below shows a redundant 2-node HA setup (`rugged-edge-l4-24g` at $\$8,210$ unit CAPEX, $300\text{W}$ TDP, $\$100\text{/mo}$ maintenance per server):

```json
{
  "audit_id": "aud-gmao-2026-001",
  "verdict": {
    "deployment_mode": "AIR_GAPPED_EDGE",
    "recommended_hardware": [
      {
        "hardware_id": "rugged-edge-l4-24g",
        "name": "Industrial Rugged Server NVIDIA L4 (24GB)",
        "quantity": 2,
        "vram_per_unit_gb": 24.0,
        "system_ram_gb": 128.0,
        "role": "Active-Active HA Edge Inference & Vector Storage"
      }
    ],
    "model_stack": {
      "generator_model_id": "llama-3.2-3b-instruct-q4",
      "embedding_model_id": "bge-m3-industrial",
      "reranker_model_id": "bge-reranker-base",
      "weights_vram_gb": 1.73,
      "kv_cache_allocated_gb": 4.55,
      "vector_db_vram_gb": 0.72,
      "total_vram_required_gb": 10.26,
      "max_concurrent_streams": 14
    },
    "rag_parameters": {
      "estimated_total_child_chunks": 550563,
      "chunking_strategy": "PARENT_CHILD_SEMANTIC",
      "child_chunk_size_tokens": 200,
      "parent_chunk_size_tokens": 1000,
      "retrieval_mode": "HYBRID_BM25_VECTOR_RRF",
      "rrf_constant_k": 60,
      "rerank_top_k": 50,
      "generator_top_k": 5,
      "zero_hallucination_gate": "ENABLED"
    },
    "tco_3year_comparison": {
      "hardware_capex_usd": 16420.00,
      "energy_and_maint_3yr_usd": 10040.83,
      "capex_edge_total_usd": 26460.83,
      "opex_cloud_total_usd": 54120.00,
      "net_savings_usd": 27659.17,
      "recommended_decision": "CAPEX_ON_PREM_EDGE"
    }
  }
}
```

### 4.2 Telemetry Ingestion Endpoints

#### 4.2.1 Real-Time Edge Event (`HYBRID_CONNECTED` & `FULL_CLOUD`)
`POST /api/v1/telemetry/event`

Real-time events capture **low-overhead synchronous execution metrics** only. Heavy semantic evaluations (`context_recall` and `faithfulness_score`) are computed asynchronously by the nightly calibration processor on a $5\%$ stratified sample of stored logs to avoid degrading edge TTFT.

```json
{
  "client_id": "helvetic-precision-site-04",
  "timestamp": "2026-11-11T09:14:22Z",
  "device_profile": {
    "device_model": "Panasonic-Toughbook-G2",
    "shift_name": "MORNING_CHANGEOVER",
    "connectivity_state": "HYBRID_EDGE_SYNC"
  },
  "execution_metrics": {
    "query_hash": "sha256-8f9d2a1b...",
    "ttft_ms": 1180.4,
    "total_latency_ms": 2410.0,
    "peak_vram_mb": 10450,
    "reranker_max_score": 0.89,
    "citation_regex_verified": true,
    "numeric_grounding_verified": true,
    "detected_error_code": "HYD-E04"
  },
  "evaluation_sample_payload": {
    "is_sampled_for_eval": true,
    "query_text_raw": "Hydraulic pack 3 overheating, error code HYD-E04",
    "retrieved_parent_chunk_ids": ["doc-hyd-01#p14", "doc-hyd-01#p15"],
    "generated_response": "According to Manual HYD-01 (Section 4.2, Page 14), error HYD-E04 indicates..."
  }
}
```

#### 4.2.2 Batch Archive Upload (`AIR_GAPPED_EDGE` Mode)
`POST /api/v1/telemetry/batch-upload`
* **Content-Type:** `multipart/form-data` (accepts `.jsonl.gz` exported from the factory floor server).
* **Behavior:** Streams the batch into Cloudflare R2 and triggers the Python calibration routine immediately.

---

## 5. GMAO-Specific Pipeline & Domain Strategies

Generic RAG architectures frequently fail when confronted with industrial maintenance documentation. Complex equipment manuals feature hierarchical numbering, exploded assembly views, diagnostic fault trees, and dense torque ratings.

```
Industrial Input Stream (Manuals, Schematics, Historical Work Orders)
                                  |
                                  v
+-----------------------------------------------------------------+
| 1. Format-Aware Structural Parsing (Layout, Tables, Schematics) |
+---------------------------------+-------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------+
| 2. Hierarchical Chunking (Child: 150-250t / Parent: 800-1200t)  |
+---------------------------------+-------------------------------+
                                  |
                 +----------------+----------------+
                 |                                 |
                 v                                 v
+--------------------------------+  +-------------------------------+
| 3a. Dense Embedding (BGE-M3)   |  | 3b. Sparse BM25 Keyword Index |
|     (Semantic Concepts)        |  |     (Part Codes, Fault SKUs)  |
+----------------+---------------+  +---------------+---------------+
                 |                                  |
                 +----------------+-----------------+
                                  |
                                  v
+-----------------------------------------------------------------+
| 4. Reciprocal Rank Fusion (RRF: k = 60, Select Top-50 Passages) |
+---------------------------------+-------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------+
| 5. Cross-Encoder Reranking (Score & Select Top-5 Passages)      |
+---------------------------------+-------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------+
| 6. Zero-Hallucination Gate (Deterministic Citation & Number Check)|
+---------------------------------+-------------------------------+
```

### 5.1 Format-Aware Parsing & Extraction

Standard flat-text tokenizers scramble table structures and schematic callouts. The GMAO pipeline enforces:
* **Table Reconstruction:** Preserving structural headers (Markdown/HTML table serialization) for torque specifications, bolt dimensions, and pinout diagrams.
* **Metadata Tagging:** Attaching machine model, subsystem ID, component family, and revision timestamps to all parsed text blocks.

### 5.2 Hierarchical Parent-Child Retrieval

To reconcile search precision with generation context:
* **Child Chunks (150 to 250 tokens):** Capture discrete troubleshooting steps, error codes, and symptoms. Embeddings are calculated over child chunks for high-precision vector matching.
* **Parent Chunks (800 to 1200 tokens):** Enclose the complete procedural task or mechanical subsystem. Upon retrieval, deduplicated parent chunks are forwarded to the LLM prompt, providing full context without fragmentation.

### 5.3 Hybrid Search & Reciprocal Rank Fusion

Field technicians often query exact part numbers (e.g., `SKF-6204-2RSH`) or colloquial symptoms (e.g., "high-pitched whine from pump B"). A hybrid pipeline runs parallel searches:
* **Dense Vector Index:** Retrieves conceptual and functional matches.
* **Sparse BM25 Index:** Matches exact alphanumeric SKUs, error codes, and component tags.

Results are fused via Reciprocal Rank Fusion (RRF):

$$\text{RRF\_Score}(d) = \sum_{m \in \{\text{Dense}, \text{BM25}\}} \frac{1}{60 + \text{Rank}_m(d)}$$

### 5.4 Zero-Hallucination Verification Gate

For safety-critical environments, generated responses are screened synchronously via deterministic regex and AST rules before presentation:
1. **Citation Presence Check:** The response must state explicit document citations matching the retrieved metadata (`[Manual ID, Section, Page]`).
2. **Numerical Grounding Verification:** All numerical quantities with physical units (e.g., $\text{Nm}$, $\text{bar}$, $\text{psi}$, $\text{V}$, $\text{A}$, $^{\circ}\text{C}$) extracted from the generated answer via regular expressions must exist verbatim in the retrieved parent chunks. If a number lacks explicit grounding in the source context, the gate blocks the output and returns:
   `"SAFETY GATE BLOCK: Unverified numerical specification detected. Consult physical manual directly."`

---

## 6. Closed-Loop Auto-Calibration Engine

Field telemetry collected via Cloudflare Workers (or batch-uploaded in Air-Gapped mode) feeds three continuous optimization feedback loops.

```
                         Factory Floor Operations
                    (Technician Rugged Tablets)
                                 |
            +--------------------+--------------------+
            | (Connected Mode)                        | (Air-Gapped Mode)
            v                                         v
Cloudflare Workers Collector               Local Edge JSONL Buffer
            |                                         | (Manual Batch Upload)
            +--------------------+--------------------+
                                 |
                                 v
                    Cloudflare R2 Storage Buffer
                                 |
                                 v (Nightly Cron / Batch Trigger)
                 Python Engine Calibration Processor
                 (Runs Async RAGAS Eval on 5% Sample)
                                 |
       +-------------------------+-------------------------+
       |                         |                         |
       v                         v                         v
+--------------+          +--------------+          +--------------+
| Loop 1: HW   |          | Loop 2:      |          | Loop 3:      |
| Sizing       |          | Ingestion    |          | Semantic     |
| Calibration  |          | Tuning       |          | Router       |
+--------------+          +--------------+          +--------------+
```

### 6.1 Loop 1: Hardware Sizing Correction
* **Detection Trigger:** 7-day rolling telemetry shows that 95th-percentile TTFT exceeds $1.5\text{ seconds}$, or GPU VRAM utilization breaches $90\%$ during shift changes.
* **Action:** The calibration job increments `computeScalingMultiplier` ($M_{\text{calib}}$) by $+0.20$ ($+20\%$) in the `telemetryCalibration` table for that hardware/model pair, ensuring future audits automatically provision higher-tier or additional edge nodes.

### 6.2 Loop 2: Ingestion & Vocabulary Alignment
* **Detection Trigger:** Asynchronous evaluation on sampled traces indicates *Context Recall* drops below $0.75$, or synchronous `reranker_max_score` frequently falls below $0.60$, signaling a mismatch between technician phrasing and manual jargon.
* **Action:** The audit system generates updated chunking recommendations, decreasing child chunk sizes by $20\%$ (e.g., from $200$ to $160\text{ tokens}$) and flagging `detected_error_code` terms for domain synonym expansion.

### 6.3 Loop 3: Financial Rationalization via Semantic Routing
* **Detection Trigger:** Monthly token consumption on hybrid/cloud deployments exceeds projected baseline estimates by $>15\%$.
* **Action:** The system recommends and provisions a **Semantic Router**:
  * **Route A (Routine Inquiries):** Queries matching standard maintenance intervals or part locations are routed to a local quantized 3B SLM hosted on the factory floor.
  * **Route B (Complex Diagnostics):** Multi-fault diagnostic problems are forwarded to high-capacity cloud models (e.g., Claude 3.5 Sonnet).

---

## 7. Implementation Roadmap & Coding Agent Instructions

Coding agents must execute implementation following this sequential dependency structure:

### 7.1 Target File Tree Structure
```
rag-architect-gmao/
├── apps/
│   ├── portal/                    # SvelteKit + Tailwind CSS (Cloudflare Pages)
│   │   ├── src/
│   │   │   ├── routes/
│   │   │   │   ├── +page.svelte   # Landing & Audit Workflow UI
│   │   │   │   └── api/
│   │   │   │       ├── audit/+server.ts        # Queries D1 & calls Python service
│   │   │   │       └── batch-upload/+server.ts # Air-gapped JSONL upload to R2
│   │   │   └── lib/
│   │   ├── package.json
│   │   └── svelte.config.js
│   └── telemetry-worker/          # Cloudflare Worker for real-time edge ingestion
│       ├── src/
│       │   └── index.ts           # R2 streaming & bearer token validation
│       └── wrangler.toml
├── services/
│   └── sizing-engine/             # Python 3.12 microservice
│       ├── core/
│       │   ├── calculator.py      # Deterministic VRAM, KV Cache, Chunks & TCO math
│       │   ├── gate.py            # Zero-Hallucination regex & numerical verifier
│       │   └── calibration.py     # Rolling feedback loops (Loops 1, 2, 3)
│       ├── api/
│       │   ├── schemas.py         # Pydantic v2 request/response contracts
│       │   └── routes.py          # FastAPI endpoints
│       ├── tests/
│       │   └── test_calculator.py # Mathematical verification suite
│       ├── pyproject.toml         # uv configuration
│       └── Dockerfile
├── packages/
│   └── db/                        # Cloudflare D1 & Drizzle ORM
│       ├── src/
│       │   ├── schema.ts          # Relational schemas (Section 2.1)
│       │   └── seed.ts            # Initial hardware & model catalog seed
│       ├── drizzle.config.ts
│       └── migrations/
└── README.md
```

### 7.2 Step-by-Step Task Execution

1. **Database Setup (`packages/db`):**
   * Initialize Drizzle ORM configured for Cloudflare D1.
   * Apply schemas for `hardwareCatalog`, `modelRegistry`, `auditSubmissions`, and `telemetryCalibration`.
   * Seed `hardwareCatalog` with accurate baseline specs:
     * `rugged-edge-l4-24g`: $\$8,210$ CAPEX, $\$100\text{/mo}$ maint, $24\text{ GB}$ VRAM, $128\text{ GB}$ RAM, $300\text{W}$ TDP.
     * `rugged-dual-a4500-40g`: $\$12,500$ CAPEX, $\$140\text{/mo}$ maint, $40\text{ GB}$ VRAM ($2\times 20\text{ GB}$), $128\text{ GB}$ RAM, $450\text{W}$ TDP.
     * `nvidia-l40s-cloud`: $\$0$ CAPEX, $\$684\text{/mo}$ OPEX ($\$0.95\text{/hr}$), $48\text{ GB}$ VRAM, $350\text{W}$ TDP.
     * `edgestream-gw-01`: $\$2,800$ CAPEX, $\$30\text{/mo}$ maint, $8\text{ GB}$ VRAM, $32\text{ GB}$ RAM, $65\text{W}$ TDP.
   * Seed `modelRegistry` with `llama-3.2-3b-instruct-q4` ($P=3.21\text{B}, L=28, H_Q=24, H_{KV}=8, D_{\text{head}}=128, \text{WeightBits}=4, \text{KVBits}=8$) and `claude-3-5-sonnet`.
2. **Sizing Engine Development (`services/sizing-engine`):**
   * Implement `calculator.py` implementing the exact KV Cache, Chunk conversion, VRAM, and 3-year TCO formulas specified in Section 3.
   * Expose `POST /api/v1/size-architecture` and `POST /api/v1/calibrate` using FastAPI with strict Pydantic v2 validation.
   * Write unit tests in `test_calculator.py` asserting that the sample input in Section 4.1 produces the exact output values documented in Section 4.1.
3. **Audit Portal Interface (`apps/portal`):**
   * Build the multi-step audit qualification form capturing plant operational parameters and electricity rates.
   * Implement `/api/audit/+server.ts` to fetch catalog rules from D1 and dispatch the calculation request to the Python Sizing Engine.
   * Render side-by-side comparative views of 3-year CAPEX versus OPEX projections and memory breakdowns.
4. **Telemetry Ingestion (`apps/telemetry-worker` & `/api/batch-upload`):**
   * Create the Cloudflare Worker intercepting `POST /api/v1/telemetry/event` for connected sites, plus the `/api/batch-upload` endpoint for air-gapped `.jsonl.gz` archives.
5. **Auto-Calibration Processor:**
   * Implement the calibration trigger that aggregates 7-day rolling metrics from R2 and updates `computeScalingMultiplier` in Cloudflare D1.

---

## 8. Annexe Métier (Cas d'Usage de Référence) : Projet 04 — Assistant RAG pour Procédures SOP / Manuels GMP

*Note : Cette section illustre un cas d'application concret d'une architecture dimensionnée et auditée par la plateforme RAG-Architect en environnement industriel réglementé.*

### 8.1 Profil du Projet

* **Identifiant du projet :** Projet 04 — Assistant RAG pour procédures SOP / manuels GMP
* **Domaine industriel cible :** Environnements de fabrication réglementés sous Bonnes Pratiques de Fabrication (GMP / BPF) : industrie pharmaceutique, biotechnologies et agroalimentaire de pointe.
* **Environnement d'exploitation :** Lignes de production en salle blanche et ateliers de conditionnement avec terminaux durcis mobiles opérant en mode *Air-Gapped* ou Cloud Privé Qualifié.

### 8.2 Le Constat & Friction Métier

En environnement GMP, la recherche manuelle dans les classeurs qualité ou la Gestion Électronique des Documents (GED) conventionnelle requiert 20 à 45 minutes par intervention de maintenance ou de changement de format. La dispersion des informations et la rigidité des systèmes de recherche par mots-clés augmentent considérablement le risque d'omission d'une étape critique :
* Oubli ou mauvais séquençage d'un cycle de purge ou de stérilisation (SIP/CIP).
* Erreur d'application des couples de serrage sur les brides et étanchéités de tuyauteries.
* Non-respect de l'ordre d'habillage ou de décontamination sas.

Ces écarts d'exécution engendrent des déviations qualité majeures, des arrêts prolongés de lignes de fabrication et des non-conformités sévères lors des audits d'inspection réglementaire (FDA / ANSM).

### 8.3 Architecture Cible Recommandée par RAG-Architect

Un assistant conversationnel souverain fondé sur l'architecture RAG avancée spécifiée dans la Section 5, configuré pour garantir zéro hallucination et une traçabilité totale :
* **Parsing Structuré et OCR Haute Précision :** Extraction intelligente préservant la topologie des manuels de maintenance, tableaux de couple, plans P&ID et logigrammes de décision.
* **Découpage Sémantique Hiérarchique (Parent-Child) :** Indexation fine des instructions élémentaires (150–250 tokens) pour le repérage chirurgical, couplée à la restitution du bloc de procédure complet (800–1200 tokens) dans le contexte du modèle pour éviter toute interprétation tronquée.
* **Recherche Hybride et Re-classement (RRF + Cross-Encoder) :** Combinaison de la recherche vectorielle dense (compréhension sémantique des symptômes) et lexicale clairsemée BM25 (références exactes de pièces détachées, codes vannes, numéros d'articles), réordonnée par un cross-encoder résidant en VRAM.
* **Citation Obligatoire & Garde-Fous Anti-Hallucination (`Zero-Hallucination Gate`) :** Validation déterministe imposant l'affichage du document source, de la révision exacte de la SOP et du numéro de paragraphe, avec vérification par expression régulière de toutes les grandeurs physiques chiffrées.
* **Déploiement Souverain & Filtrage de Version :** Déploiement en local (*Air-Gapped* sur serveurs durcis industriels dimensionnés via RAG-Architect) ou en cloud privé qualifié (GxP / 21 CFR Part 11). Application stricte de métadonnées assurant que seules les versions de SOP en vigueur sont accessibles selon le profil d'autorisation du technicien.

### 8.4 Livrables Opérationnels du Déploiement Client

1. **Rapport d'Audit & de Dimensionnement RAG-Architect :** Calcul certifié de la VRAM, du KV Cache et du TCO à 3 ans.
2. **Index Vectoriel & Lexical Calibré :** Base hybride (vectorielle dense + BM25) partitionnée par atelier et version documentaire.
3. **Jeu de Tests Signé & Dossier de Qualification (IQ/OQ/PQ) :** Matrice de validation logicielle, tests automatisés de non-régression et procès-verbal de validation de la fidélité contextuelle (*Context Recall* et *Faithfulness*).
4. **Audit Trail des Requêtes :** Journalisation immuable et horodatée de l'intégralité des invites, contextes extraits, identifiants de documents cités et réponses générées pour conformité réglementaire.

### 8.5 Résultats Attendus & Indicateurs de Performance (KPI)

| Indicateur | Cible Opérationnelle | Mécanisme de Mesure RAG-Architect |
| :--- | :--- | :--- |
| **Temps d'accès documentaire** | **−30 %** par intervention | Horodatage télémétrique du premier token (`ttft_ms`) et durée de session |
| **Non-conformités d'exécution** | **−50 %** d'écarts de procédure | Analyse des rapports de déviation usine et suivi des ordres de travail |
| **Exactitude factuelle** | **100 %** de conformité stricte | Garde-fou déterministe des citations et valeurs numériques (`Zero-Hallucination Gate`) |
| **Délai de déploiement (Horizon)** | **4 à 6 semaines** | Déploiement accéléré via conteneurs standardisés et sizing automatisé |