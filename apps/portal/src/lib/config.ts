// Deployment URL resolution for the isolated rag-architect deployment.
// Production defaults point at the Fly.io sizing engine and the Cloudflare
// telemetry worker; local dev falls back to localhost.

export interface PortalEnv {
  SIZING_ENGINE_URL?: string;
  TELEMETRY_WORKER_URL?: string;
}

function normalizeUrl(raw: string | undefined, fallback: string): string {
  if (!raw) return fallback;
  const trimmed = raw.trim();
  const mdMatch = trimmed.match(/^\[[^\]]*\]\((https?:\/\/[^)\s]+)\)$/);
  const candidate = (mdMatch ? mdMatch[1] : trimmed)
    .replace(/^<|>$/g, '')
    .replace(/\/+$/, '');

  try {
    const parsed = new URL(candidate);
    if (parsed.protocol === 'https:' || parsed.protocol === 'http:') {
      return parsed.toString().replace(/\/+$/, '');
    }
  } catch {
    // Fallback if malformed
  }
  return fallback;
}

export function resolveEngineUrl(env: PortalEnv | undefined, isDev: boolean): string {
  return normalizeUrl(
    env?.SIZING_ENGINE_URL,
    isDev ? 'http://127.0.0.1:8000' : 'https://rag-architect-sizing.fly.dev'
  );
}

export function resolveWorkerUrl(env: PortalEnv | undefined, isDev: boolean): string {
  return normalizeUrl(
    env?.TELEMETRY_WORKER_URL,
    isDev ? 'http://127.0.0.1:8787' : 'https://telemetry-worker.haroudm.workers.dev'
  );
}
