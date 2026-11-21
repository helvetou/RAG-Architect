import { json, type RequestHandler } from '@sveltejs/kit';
import { sizeRequestSchema } from '$lib/schemas';
import { buildAuditSubmission } from '$lib/audit';
import { resolveEngineUrl } from '$lib/config';

export const POST: RequestHandler = async ({ request, platform }) => {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid JSON' }, { status: 400 });
  }

  const parsed = sizeRequestSchema.safeParse(body);
  if (!parsed.success) {
    return json({ error: 'Invalid request', issues: parsed.error.issues }, { status: 400 });
  }

  const env = platform?.env;
  const db = env?.DB;
  // Local dev injects a D1 proxy stub but has no real backing database: skip
  // the production-only catalog guard and persistence when running under vite dev.
  const dbAvailable = Boolean(db) && !import.meta.env.DEV;

  // RSK-004: confirm the D1 catalog is reachable before calling the sizing engine.
  if (dbAvailable) {
    try {
      await db.prepare('SELECT id FROM hardware_catalog LIMIT 1').first();
      await db.prepare('SELECT id FROM model_registry LIMIT 1').first();
    } catch {
      return json({ error: 'D1 catalog unavailable' }, { status: 502 });
    }
  }

  const engineUrl = resolveEngineUrl(env, import.meta.env.DEV);

  let result: Record<string, unknown>;
  try {
    const response = await fetch(`${engineUrl}/api/v1/size-architecture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed.data),
    });
    if (!response.ok) {
      return json({ error: 'Sizing engine error' }, { status: 502 });
    }
    result = (await response.json()) as Record<string, unknown>;
  } catch {
    return json({ error: 'Sizing engine unavailable' }, { status: 502 });
  }

  // 21 CFR Part 11: persist the audit append-only (INSERT only; UPDATE/DELETE are
  // blocked by the DB triggers created in migration 0001). Fail loudly if the
  // immutable audit trail cannot be written.
  if (dbAvailable) {
    try {
      const inputJson = JSON.stringify(parsed.data);
      const outputJson = JSON.stringify(result);
      const submission = await buildAuditSubmission('portal-bff', inputJson, outputJson);
      await db
        .prepare(
          `INSERT INTO audit_submissions
           (id, client_name, techs_per_shift, total_shifts, manuals_volume_gb,
            work_orders_count, avg_tokens_per_page, deployment_constraint,
            peak_query_ratio, avg_queries_per_tech_shift, electricity_rate_kwh_usd,
            target_p95_ttft_seconds, created_at, actor_id, input_payload_sha256,
            output_payload_sha256, input_payload_json, output_payload_json,
            spec_version, model_version)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          parsed.data.audit_id,
          parsed.data.client_name,
          parsed.data.technicians_per_shift,
          parsed.data.total_shifts,
          parsed.data.documents.equipment_manuals_pdf_gb,
          parsed.data.documents.historical_work_orders_count,
          parsed.data.documents.average_tokens_per_page,
          parsed.data.deployment_constraint,
          parsed.data.concurrency.peak_shift_overlap_ratio,
          parsed.data.concurrency.avg_queries_per_tech_shift,
          parsed.data.financials.electricity_rate_kwh_usd,
          parsed.data.concurrency.target_p95_ttft_seconds,
          Math.floor(Date.now() / 1000),
          submission.actorId,
          submission.inputPayloadSha256,
          submission.outputPayloadSha256,
          inputJson,
          outputJson,
          submission.specVersion,
          submission.modelVersion
        )
        .run();
    } catch {
      return json({ error: 'Audit persistence failed' }, { status: 502 });
    }
  }

  return json(result);
};
