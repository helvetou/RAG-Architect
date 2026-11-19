// CMMI Level 3 Verification Suite — Zod <-> OpenAPI/Pydantic contract (TEST-INT-001)
// Traceability: REQ-API-001 (portal side), M5 contract-first integration.
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import {
  concurrencySchema,
  documentsSchema,
  financialsSchema,
  sizeRequestSchema,
  sizeResponseSchema,
} from './schemas';

const openapi = JSON.parse(
  readFileSync(
    fileURLToPath(new URL('../../../../packages/contracts/openapi.json', import.meta.url)),
    'utf8'
  )
) as {
  components: {
    schemas: Record<string, { properties: Record<string, unknown> }>;
  };
};

const schemas = openapi.components.schemas;

describe('TEST-INT-001 — Zod ↔ OpenAPI/Pydantic contract', () => {
  it('SizeRequest Zod keys match the OpenAPI SizeRequest schema', () => {
    const zodKeys = Object.keys(sizeRequestSchema.shape).sort();
    const openapiKeys = Object.keys(schemas.SizeRequest.properties).sort();
    expect(zodKeys).toEqual(openapiKeys);
  });

  it('Documents/Concurrency/Financials Zod keys match OpenAPI', () => {
    expect(Object.keys(documentsSchema.shape).sort()).toEqual(
      Object.keys(schemas.Documents.properties).sort()
    );
    expect(Object.keys(concurrencySchema.shape).sort()).toEqual(
      Object.keys(schemas.Concurrency.properties).sort()
    );
    expect(Object.keys(financialsSchema.shape).sort()).toEqual(
      Object.keys(schemas.Financials.properties).sort()
    );
  });

  it('SizeResponse Zod schema matches the aud-gmao-2026-001 response contract', () => {
    const result = sizeResponseSchema.safeParse({
      audit_id: 'aud-gmao-2026-001',
      verdict: {
        deployment_mode: 'AIR_GAPPED_EDGE',
        model_stack: { total_vram_required_gb: 10.96, max_concurrent_streams: 14 },
        rag_parameters: { estimated_total_child_chunks: 901313 },
        tco_3year_comparison: {
          capex_edge_total_usd: 26458.24,
          opex_cloud_total_usd: 54531.94,
          recommended_decision: 'CAPEX_ON_PREM_EDGE',
        },
      },
    });
    expect(result.success).toBe(true);
  });
});
