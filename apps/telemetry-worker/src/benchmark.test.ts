import { expect, it, vi } from "vitest";

import worker, { type Env } from "./index";

it("benchmark: POST /api/v1/telemetry/event p99 < 15 ms", async () => {
  const env: Env = {
    AUTH_TOKEN: "bench-token",
    TELEMETRY_BUCKET: { put: vi.fn().mockResolvedValue(undefined) } as unknown as R2Bucket,
    DB: { prepare: vi.fn() } as unknown as D1Database,
  };
  const ctx = { waitUntil: vi.fn() } as unknown as ExecutionContext;
  const body = JSON.stringify({
    client_id: "bench-site",
    timestamp: "2026-01-01T00:00:00Z",
    execution_metrics: { ttft_ms: 1000 },
  });

  const samples = 1000;
  const latencies: number[] = [];
  for (let i = 0; i < samples; i++) {
    const request = new Request("https://worker.example/api/v1/telemetry/event", {
      method: "POST",
      headers: { Authorization: "Bearer bench-token", "Content-Type": "application/json" },
      body,
    });
    const start = performance.now();
    const response = await worker.fetch(request, env, ctx);
    latencies.push(performance.now() - start);
    expect(response.status).toBe(202);
  }

  latencies.sort((a, b) => a - b);
  const p99 = latencies[Math.ceil(latencies.length * 0.99) - 1];
  // eslint-disable-next-line no-console
  console.log(`p99 ingestion latency (${samples} samples): ${p99.toFixed(3)} ms`);
  expect(p99).toBeLessThan(15);
});
