export interface Env {
  AUTH_TOKEN: string;
  TELEMETRY_BUCKET: R2Bucket;
  DB: D1Database;
}

const EVENT_PATH = "/api/v1/telemetry/event";
const BATCH_PATH = "/api/v1/telemetry/batch-upload";
const SIGNATURE_HEADER = "X-Batch-Signature-SHA256";

const TTFT_THRESHOLD_MS = 1500;
const PEAK_VRAM_RATIO = 0.9;
const SCALING_INCREMENT = 0.2;

function isAuthorized(request: Request, env: Env): boolean {
  const authorization = request.headers.get("Authorization");
  return authorization === `Bearer ${env.AUTH_TOKEN}`;
}

function isTelemetryEvent(value: unknown): boolean {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    typeof record.client_id === "string" &&
    typeof record.timestamp === "string" &&
    typeof record.execution_metrics === "object" &&
    record.execution_metrics !== null
  );
}

async function sha256Hex(data: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function constantTimeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) {
    return false;
  }
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    if (!isAuthorized(request, env)) {
      return new Response("Unauthorized", { status: 401 });
    }

    const url = new URL(request.url);

    if (request.method === "POST" && url.pathname === EVENT_PATH) {
      let payload: unknown;
      try {
        payload = await request.json();
      } catch {
        return new Response("Invalid JSON", { status: 400 });
      }
      if (!isTelemetryEvent(payload)) {
        return new Response("Invalid telemetry event", { status: 400 });
      }
      const key = `telemetry/events/${Date.now()}.json`;
      ctx.waitUntil(env.TELEMETRY_BUCKET.put(key, JSON.stringify(payload)));
      return new Response("Accepted", { status: 202 });
    }

    if (request.method === "POST" && url.pathname === BATCH_PATH) {
      const signature = request.headers.get(SIGNATURE_HEADER);
      if (!signature) {
        return new Response("Missing signature", { status: 400 });
      }
      const body = await request.arrayBuffer();
      const digest = await sha256Hex(body);
      if (!constantTimeEqual(digest, signature.toLowerCase())) {
        return new Response("Invalid signature", { status: 401 });
      }
      const key = `telemetry/batches/${Date.now()}.jsonl.gz`;
      ctx.waitUntil(env.TELEMETRY_BUCKET.put(key, body));
      return new Response("Accepted", { status: 202 });
    }

    return new Response("Not Found", { status: 404 });
  },

  async scheduled(
    _controller: ScheduledController,
    env: Env,
    _ctx: ExecutionContext
  ): Promise<void> {
    const row = await env.DB.prepare(
      `SELECT t.id, t.measured_p95_ttft_ms, t.measured_peak_vram_gb,
              t.measured_context_recall, t.compute_scaling_multiplier,
              h.vram_gb AS hardware_vram_gb
       FROM telemetry_calibration t
       JOIN hardware_catalog h ON t.hardware_id = h.id
       ORDER BY t.last_updated DESC LIMIT 1`
    ).first<Record<string, unknown>>();

    if (!row) {
      return;
    }

    const ttft = Number(row.measured_p95_ttft_ms);
    const peakVram = Number(row.measured_peak_vram_gb);
    const hardwareVram = Number(row.hardware_vram_gb);
    const current = Number(row.compute_scaling_multiplier);

    const loop1Triggered = ttft > TTFT_THRESHOLD_MS || peakVram > PEAK_VRAM_RATIO * hardwareVram;
    const nextMultiplier = loop1Triggered ? current + SCALING_INCREMENT : current;

    await env.DB.prepare(
      "UPDATE telemetry_calibration SET compute_scaling_multiplier = ?, last_updated = ? WHERE id = ?"
    )
      .bind(nextMultiplier, Date.now(), String(row.id))
      .run();
  },
};
