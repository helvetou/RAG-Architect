import { json, type RequestHandler } from '@sveltejs/kit';
import { resolveWorkerUrl } from '$lib/config';

export const POST: RequestHandler = async ({ request, platform }) => {
  const env = platform?.env;
  const body = await request.arrayBuffer();
  const signature = request.headers.get('X-Batch-Signature-SHA256');
  const authorization = request.headers.get('Authorization');
  const bearer = env?.AUTH_TOKEN ? `Bearer ${env.AUTH_TOKEN}` : authorization;

  const headers: Record<string, string> = { 'Content-Type': 'application/octet-stream' };
  if (signature) {
    headers['X-Batch-Signature-SHA256'] = signature;
  }
  if (bearer) {
    headers['Authorization'] = bearer;
  }

  const workerUrl = resolveWorkerUrl(env, import.meta.env.DEV);

  try {
    const response = await fetch(`${workerUrl}/api/v1/telemetry/batch-upload`, {
      method: 'POST',
      headers,
      body,
    });
    return json({ status: response.status }, { status: response.ok ? 202 : 502 });
  } catch {
    return json({ error: 'Telemetry worker unavailable' }, { status: 502 });
  }
};
