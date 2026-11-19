import { describe, expect, it, vi } from "vitest";

import worker, { type Env } from "./index";

const AUTH_TOKEN = "test-bearer-token";

async function sha256Hex(data: string): Promise<string> {
  const bytes = new TextEncoder().encode(data);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function makeEnv(db: D1Database = { prepare: vi.fn() } as unknown as D1Database): Env {
  return {
    AUTH_TOKEN,
    TELEMETRY_BUCKET: { put: vi.fn().mockResolvedValue(undefined) } as unknown as R2Bucket,
    DB: db,
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

  it("TEST-TEL-002: rejects unauthorized requests and accepts signed batch uploads", async () => {
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

    const body = "gzip-bytes-placeholder";
    const digest = await sha256Hex(body);
    const batch = new Request("https://worker.example/api/v1/telemetry/batch-upload", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        "X-Batch-Signature-SHA256": digest,
      },
      body,
    });
    const accepted = await worker.fetch(batch, env, ctx);
    expect(accepted.status).toBe(202);
    expect(env.TELEMETRY_BUCKET.put).toHaveBeenCalledTimes(1);
  });

  it("TEST-TEL-003: verifies SHA-256 batch signature (missing/invalid/valid)", async () => {
    const env = makeEnv();
    const ctx = makeCtx();
    const body = "gzip-bytes-placeholder";

    const missing = new Request("https://worker.example/api/v1/telemetry/batch-upload", {
      method: "POST",
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      body,
    });
    const resMissing = await worker.fetch(missing, env, ctx);
    expect(resMissing.status).toBe(400);
    expect(env.TELEMETRY_BUCKET.put).not.toHaveBeenCalled();

    const invalid = new Request("https://worker.example/api/v1/telemetry/batch-upload", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        "X-Batch-Signature-SHA256": "0".repeat(64),
      },
      body,
    });
    const resInvalid = await worker.fetch(invalid, env, ctx);
    expect(resInvalid.status).toBe(401);
    expect(env.TELEMETRY_BUCKET.put).not.toHaveBeenCalled();

    const digest = await sha256Hex(body);
    const valid = new Request("https://worker.example/api/v1/telemetry/batch-upload", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        "X-Batch-Signature-SHA256": digest,
      },
      body,
    });
    const resValid = await worker.fetch(valid, env, ctx);
    expect(resValid.status).toBe(202);
    expect(env.TELEMETRY_BUCKET.put).toHaveBeenCalledTimes(1);
  });

  it("TEST-TEL-004: scheduled() runs calibration and persists M_calib to D1", async () => {
    const selectFirst = vi.fn().mockResolvedValue({
      id: "row-1",
      measured_p95_ttft_ms: 1680.0,
      measured_peak_vram_gb: 18.5,
      measured_context_recall: 0.84,
      compute_scaling_multiplier: 1.0,
      hardware_vram_gb: 24.0,
    });
    const bind = vi.fn().mockReturnValue({ run: vi.fn().mockResolvedValue({}) });
    const prepare = vi.fn((query: string) => {
      if (query.trimStart().startsWith("SELECT")) {
        return { first: selectFirst };
      }
      return { bind };
    });
    const db = { prepare } as unknown as D1Database;
    const env = makeEnv(db);
    const ctx = makeCtx();

    await worker.scheduled({} as ScheduledController, env, ctx);

    expect(prepare).toHaveBeenCalledTimes(2);
    expect(bind).toHaveBeenCalledWith(1.2, expect.any(Number), "row-1");
  });
});
