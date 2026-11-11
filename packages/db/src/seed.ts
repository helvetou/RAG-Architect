// Deterministic catalog seed data (Traceability: REQ-DB-001).
// Values sourced from SPEC-GMAO-RAG-ARCH-003 v3.0.0 (Sections 4.1, 5.1, 6.1, 8.2.1) and the M2 plan.
import type { InferInsertModel } from 'drizzle-orm';
import { hardwareCatalog, modelRegistry } from './schema';

export type HardwareSeed = InferInsertModel<typeof hardwareCatalog>;
export type ModelSeed = InferInsertModel<typeof modelRegistry>;

export const hardwareSeeds: HardwareSeed[] = [
  {
    id: 'rugged-edge-l4-24g',
    name: 'Industrial Rugged Server NVIDIA L4 (24GB)',
    tier: 'EDGE_RUGGED_SERVER',
    vramGb: 24.0,
    systemRamGb: 128.0,
    tdpWatts: 300,
    unitCostCapexUsd: 8210.0,
    monthlyMaintOpexUsd: 100.0,
    maxBandwidthGbps: 25.0,
  },
  {
    // Referred to as "rugged-edge-a4500" in the M2 plan; canonical ID from spec Section 4.1.
    id: 'rugged-dual-a4500-40g',
    name: 'Industrial Rugged Server Dual NVIDIA A4500 (40GB)',
    tier: 'EDGE_RUGGED_SERVER',
    vramGb: 40.0,
    systemRamGb: 128.0,
    tdpWatts: 400,
    unitCostCapexUsd: 12990.0,
    monthlyMaintOpexUsd: 140.0,
    maxBandwidthGbps: 25.0,
  },
  {
    id: 'nvidia-l40s',
    name: 'NVIDIA L40S Cloud GPU (48GB)',
    tier: 'CLOUD_HOSTED_GPU',
    vramGb: 48.0,
    systemRamGb: 192.0,
    tdpWatts: 350,
    unitCostCapexUsd: 0.0,
    monthlyMaintOpexUsd: 1490.0,
    maxBandwidthGbps: 200.0,
  },
  {
    id: 'edgestream-gw-01',
    name: 'EdgeStream Industrial Gateway 01',
    tier: 'EDGE_GATEWAY',
    vramGb: 0.0,
    systemRamGb: 8.0,
    tdpWatts: 15,
    unitCostCapexUsd: 890.0,
    monthlyMaintOpexUsd: 12.0,
    maxBandwidthGbps: 2.5,
  },
];

export const modelSeeds: ModelSeed[] = [
  {
    id: 'llama-3.2-3b-instruct-q4',
    name: 'Llama 3.2 3B Instruct (4-bit)',
    parameterCountB: 3.21,
    contextWindowTokens: 128000,
    hiddenDimension: 3072, // D_model = H_Q * D_head = 24 * 128
    layerCount: 28,
    qHeadCount: 24,
    kvHeadCount: 8,
    headDim: 128,
    weightQuantBits: 4,
    kvCacheBits: 8,
    inputTokenCostPer1M: 0.0,
    outputTokenCostPer1M: 0.0,
    isEdgeCompatible: true,
  },
];

export function getSeedData() {
  return { hardware: hardwareSeeds, models: modelSeeds };
}
