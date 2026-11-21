import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';

// Hardware Specifications & Cost Catalog (Traceability: REQ-DB-001)
export const hardwareCatalog = sqliteTable('hardware_catalog', {
  id: text('id').primaryKey(), // e.g., 'rugged-edge-l4-24g', 'rugged-dual-a4500-40g', 'nvidia-l40s'
  name: text('name').notNull(),
  tier: text('tier').notNull(), // 'EDGE_RUGGED_SERVER', 'EDGE_GATEWAY', 'CLOUD_HOSTED_GPU'
  vramGb: real('vram_gb').notNull(),
  systemRamGb: real('system_ram_gb').notNull(),
  tdpWatts: integer('tdp_watts').notNull(),
  unitCostCapexUsd: real('unit_cost_capex_usd').default(0.0).notNull(), // Initial acquisition
  monthlyMaintOpexUsd: real('monthly_maint_opex_usd').default(0.0).notNull(), // Hardware support or Cloud rental fee
  maxBandwidthGbps: real('max_bandwidth_gbps').notNull(),
});

// Large Language Model Architectural Parameters (Traceability: REQ-DB-001, REQ-MATH-001)
export const modelRegistry = sqliteTable('model_registry', {
  id: text('id').primaryKey(), // e.g., 'llama-3.2-3b-instruct-q4', 'claude-3-5-sonnet'
  name: text('name').notNull(),
  parameterCountB: real('param_count_b').notNull(),
  contextWindowTokens: integer('context_window_tokens').notNull(),
  hiddenDimension: integer('hidden_dim').notNull(),
  layerCount: integer('layer_count').notNull(),
  qHeadCount: integer('q_head_count').notNull(), // Query attention heads (H_Q)
  kvHeadCount: integer('kv_head_count').notNull(), // Key-Value heads for GQA (H_KV)
  headDim: integer('head_dim').notNull(), // Explicit head dimension (D_head)
  weightQuantBits: integer('weight_quant_bits').notNull(), // 4, 8, 16
  kvCacheBits: integer('kv_cache_bits').default(16).notNull(), // 8 (FP8/INT8) or 16 (FP16/BF16)
  inputTokenCostPer1M: real('input_token_cost_1m').default(0.0).notNull(),
  outputTokenCostPer1M: real('output_token_cost_1m').default(0.0).notNull(),
  isEdgeCompatible: integer('is_edge_compatible', { mode: 'boolean' }).notNull(),
});

// GMAO Qualification Submissions (Traceability: REQ-DB-001, REQ-FIN-001)
export const auditSubmissions = sqliteTable('audit_submissions', {
  id: text('id').primaryKey(), // UUID v4
  clientName: text('client_name').notNull(),
  techniciansPerShift: integer('techs_per_shift').notNull(),
  totalShifts: integer('total_shifts').default(3).notNull(),
  manualsVolumeGb: real('manuals_volume_gb').notNull(),
  historicalWorkOrdersCount: integer('work_orders_count').notNull(),
  avgTokensPerPage: integer('avg_tokens_per_page').default(420).notNull(),
  deploymentConstraint: text('deployment_constraint').notNull(), // 'AIR_GAPPED_EDGE', 'HYBRID_CONNECTED', 'FULL_CLOUD'
  peakQueryRatio: real('peak_query_ratio').default(0.4).notNull(), // Concurrency during shift changeovers
  avgQueriesPerTechShift: integer('avg_queries_per_tech_shift').default(15).notNull(),
  electricityRateKwhUsd: real('electricity_rate_kwh_usd').default(0.18).notNull(),
  targetP95TtftSeconds: real('target_p95_ttft_seconds').default(1.5).notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
  // 21 CFR Part 11 immutable audit-trail fields (append-only; see migration trigger)
  actorId: text('actor_id').notNull().default('system'),
  inputPayloadSha256: text('input_payload_sha256').notNull().default(''),
  outputPayloadSha256: text('output_payload_sha256').notNull().default(''),
  specVersion: text('spec_version').notNull().default('SPEC-GMAO-RAG-ARCH-003'),
  modelVersion: text('model_version').notNull().default('llama-3.2-3b-instruct-q4'),
  // 21 CFR Part 11 replayable payloads (full input/output JSON, not just hashes)
  inputPayloadJson: text('input_payload_json').default('').notNull(),
  outputPayloadJson: text('output_payload_json').default('').notNull(),
});

// Multi-Tier Telemetry Calibration State (Traceability: REQ-CAL-001)
export const telemetryCalibration = sqliteTable('telemetry_calibration', {
  id: text('id').primaryKey(), // Synthetic key: modelId + '_' + hardwareId
  modelId: text('model_id').notNull().references(() => modelRegistry.id),
  hardwareId: text('hardware_id').notNull().references(() => hardwareCatalog.id),
  measuredP95TtftMs: real('measured_p95_ttft_ms').notNull(),
  measuredPeakVramGb: real('measured_peak_vram_gb').notNull(),
  measuredContextRecall: real('measured_context_recall').notNull(), // Evaluated asynchronously
  measuredFaithfulness: real('measured_faithfulness').notNull(), // Evaluated asynchronously
  computeScalingMultiplier: real('compute_scaling_multiplier').default(1.0).notNull(),
  rollingSampleCount: integer('rolling_sample_count').notNull(),
  lastUpdated: integer('last_updated', { mode: 'timestamp' }).notNull(),
});
