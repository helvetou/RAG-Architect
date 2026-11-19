// Zod schemas mirroring the Pydantic v2 request/response models of the sizing
// engine (exported in packages/contracts/openapi.json) — TEST-INT-001 contract.
import { z } from 'zod';

export const documentsSchema = z.object({
  equipment_manuals_pdf_gb: z.number(),
  historical_work_orders_count: z.number(),
  average_tokens_per_page: z.number(),
});

export const concurrencySchema = z.object({
  peak_shift_overlap_ratio: z.number(),
  avg_queries_per_tech_shift: z.number(),
  target_p95_ttft_seconds: z.number(),
});

export const financialsSchema = z.object({
  electricity_rate_kwh_usd: z.number(),
});

export const sizeRequestSchema = z.object({
  audit_id: z.string(),
  client_name: z.string(),
  deployment_constraint: z.string(),
  technicians_per_shift: z.number(),
  total_shifts: z.number(),
  documents: documentsSchema,
  concurrency: concurrencySchema,
  financials: financialsSchema,
  safety_critical: z.boolean(),
});

export const sizeResponseSchema = z.object({
  audit_id: z.string(),
  verdict: z.object({
    deployment_mode: z.string(),
    model_stack: z.object({
      total_vram_required_gb: z.number(),
      max_concurrent_streams: z.number(),
    }),
    rag_parameters: z.object({
      estimated_total_child_chunks: z.number(),
    }),
    tco_3year_comparison: z.object({
      capex_edge_total_usd: z.number(),
      opex_cloud_total_usd: z.number(),
      recommended_decision: z.string(),
    }),
  }),
});

export type SizeRequest = z.infer<typeof sizeRequestSchema>;
