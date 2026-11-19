import { json, type RequestHandler } from '@sveltejs/kit';

// Local-dev default; override in production via platform/env (Cloudflare binding).
const WORKER_URL = 'http://127.0.0.1:8787';

export const POST: RequestHandler = async ({ request }) => {
  const body = await request.arrayBuffer();
  const signature = request.headers.get('X-Batch-Signature-SHA256');

  try {
    const headers: Record<string, string> = { 'Content-Type': 'application/octet-stream' };
    if (signature) {
      headers['X-Batch-Signature-SHA256'] = signature;
    }
    const response = await fetch(`${WORKER_URL}/api/v1/telemetry/batch-upload`, {
      method: 'POST',
      headers,
      body,
    });
    return json({ status: response.status }, { status: response.ok ? 202 : 502 });
  } catch {
    return json({ error: 'Telemetry worker unavailable' }, { status: 502 });
  }
};
