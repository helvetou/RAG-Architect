import { error } from '@sveltejs/kit';

interface AuditRow {
  id: string;
  client_name: string;
  deployment_constraint: string;
  created_at: number;
  actor_id: string;
  input_payload_sha256: string;
  output_payload_sha256: string;
  spec_version: string;
  model_version: string;
  output_payload_json: string;
}

export interface CalculationStep {
  step_id: string;
  label: string;
  formula: string;
  inputs: Record<string, string | number>;
  expression: string;
  result: string | number;
  unit: string;
  spec_section: string;
}

export async function load({
  params,
  platform,
}: {
  params: { audit_id: string };
  platform: App.Platform | undefined;
}) {
  const db = platform?.env?.DB;
  if (!db) {
    error(503, 'Database unavailable');
  }

  const row = (await db
    .prepare(
      `SELECT id, client_name, deployment_constraint, created_at, actor_id,
              input_payload_sha256, output_payload_sha256, spec_version,
              model_version, output_payload_json
       FROM audit_submissions WHERE id = ?`
    )
    .bind(params.audit_id)
    .first()) as AuditRow | null;

  if (!row) {
    error(404, 'Audit submission not found');
  }

  let output: { verdict?: unknown; calculations?: unknown } = {};
  try {
    output = JSON.parse(row.output_payload_json);
  } catch {
    error(500, 'Stored output payload is malformed');
  }

  return {
    audit: {
      id: row.id,
      clientName: row.client_name,
      deploymentConstraint: row.deployment_constraint,
      createdAt: row.created_at,
      actorId: row.actor_id,
      inputSha256: row.input_payload_sha256,
      outputSha256: row.output_payload_sha256,
      specVersion: row.spec_version,
      modelVersion: row.model_version,
    },
    calculations: (output.calculations ?? []) as CalculationStep[],
  };
}
