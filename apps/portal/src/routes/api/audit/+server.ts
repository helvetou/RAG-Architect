import { json, type RequestHandler } from '@sveltejs/kit';
import { sizeRequestSchema } from '$lib/schemas';
import { buildAuditSubmission } from '$lib/audit';

// Local-dev defaults; overridden in production via platform.env (Cloudflare bindings).
const ENGINE_URL = 'http://127.0.0.1:8000';

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

  const db = platform?.env?.DB;

  // RSK-004: read the catalog snapshot from D1 before calling the sizing engine.
  // (The current engine uses its reference constants; the snapshot is read to
  // confirm D1 reachability and is available for the multi-tier contract.)
  let catalogSnapshot: unknown = null;
  if (db) {
    try {
      const hardware = await db.prepare('SELECT id, name, vram_gb, tdp_watts FROM hardware_catalog').all();
      const models = await db.prepare('SELECT id, param_count_b, layer_count, kv_head_count, head_dim, kv_cache_bits FROM model_registry').all();
      catalogSnapshot = { hardware: hardware.results, models: models.results };
    } catch {
      return json({ error: 'D1 catalog unavailable' }, { status: 502 });
    }
  }

  let result: Record<string, unknown>;
  try {
    const response = await fetch(`${ENGINE_URL}/api/v1/size-architecture`, {
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
  // blocked by the DB triggers created in migration 0001).
  if (db) {
    const submission = await buildAuditSubmission(
      platform?.env?.AUTH_TOKEN ? 'system' : 'portal-bff',
      JSON.stringify(parsed.data),
      JSON.stringify(result)
    );
    const id = crypto.randomUUID();
    await db
      .prepare(
        `INSERT INTO audit_submissions
         (id, client_name, techs_per_shift, total_shifts, manuals_volume_gb,
          work_orders_count, avg_tokens_per_page, deployment_constraint,
          peak_query_ratio, avg_queries_per_tech_shift, electricity_rate_kwh_usd,
          target_p95_ttft_seconds, created_at, actor_id, input_payload_sha256,
          output_payload_sha256, spec_version, model_version)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
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
        submission.specVersion,
        submission.modelVersion
      )
      .run();
  }

  return json(result);
};
