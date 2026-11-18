export interface Env {
  AUTH_TOKEN: string;
  TELEMETRY_BUCKET: R2Bucket;
}

const EVENT_PATH = "/api/v1/telemetry/event";
const BATCH_PATH = "/api/v1/telemetry/batch-upload";

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
      const body = await request.arrayBuffer();
      const key = `telemetry/batches/${Date.now()}.jsonl.gz`;
      ctx.waitUntil(env.TELEMETRY_BUCKET.put(key, body));
      return new Response("Accepted", { status: 202 });
    }

    return new Response("Not Found", { status: 404 });
  },
};
