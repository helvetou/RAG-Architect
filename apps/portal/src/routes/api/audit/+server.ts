import { json, type RequestHandler } from '@sveltejs/kit';
import { sizeRequestSchema } from '#lib/schemas';

// Local-dev default; override in production via platform/env (Cloudflare binding).
const ENGINE_URL = 'http://127.0.0.1:8000';

export const POST: RequestHandler = async ({ request }) => {
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

  try {
    const response = await fetch(`${ENGINE_URL}/api/v1/size-architecture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed.data),
    });
    if (!response.ok) {
      return json({ error: 'Sizing engine error' }, { status: 502 });
    }
    return json(await response.json());
  } catch {
    return json({ error: 'Sizing engine unavailable' }, { status: 502 });
  }
};
