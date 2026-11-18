import { describe, expect, it, vi } from "vitest";

import worker, { type Env } from "./index";

const AUTH_TOKEN = "test-bearer-token";

function makeEnv(): Env {
  return {
    AUTH_TOKEN,
    TELEMETRY_BUCKET: { put: vi.fn().mockResolvedValue(undefined) } as unknown as R2Bucket,
  };
}

function makeCtx(): ExecutionContext {
  return { waitUntil: vi.fn() } as unknown as ExecutionContext;
}

describe("telemetry-worker (BL-04-TELEM)", () => {
  it("TEST-TEL-001: ingests a telemetry event with a valid Bearer token", async () => {
    const env = makeEnv();
    const ctx = makeCtx();
    const request = new Request("https://worker.example/api/v1/telemetry/event", {
      method: "POST",
      headers: { Authorization: `Bearer ${AUTH_TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: "helvetic-precision-site-04",
        timestamp: "2026-11-18T10:00:00Z",
        execution_metrics: { ttft_ms: 1180.4 },
      }),
    });

    const response = await worker.fetch(request, env, ctx);

    expect(response.status).toBe(202);
    expect(env.TELEMETRY_BUCKET.put).toHaveBeenCalledTimes(1);
    expect(ctx.waitUntil).toHaveBeenCalledTimes(1);
  });

  it("TEST-TEL-002: rejects unauthorized requests and accepts batch uploads", async () => {
    const env = makeEnv();
    const ctx = makeCtx();

    const unauthorized = new Request("https://worker.example/api/v1/telemetry/event", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const rejected = await worker.fetch(unauthorized, env, ctx);
    expect(rejected.status).toBe(401);
    expect(env.TELEMETRY_BUCKET.put).not.toHaveBeenCalled();

    const batch = new Request("https://worker.example/api/v1/telemetry/batch-upload", {
      method: "POST",
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      body: "gzip-bytes-placeholder",
    });
    const accepted = await worker.fetch(batch, env, ctx);
    expect(accepted.status).toBe(202);
    expect(env.TELEMETRY_BUCKET.put).toHaveBeenCalledTimes(1);
  });
});
