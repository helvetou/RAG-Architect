// Deployment URL resolution for the isolated rag-architect deployment.
// Production defaults point at the Fly.io sizing engine and the Cloudflare
// telemetry worker; local dev falls back to localhost.

export interface PortalEnv {
  SIZING_ENGINE_URL?: string;
  TELEMETRY_WORKER_URL?: string;
}

export function resolveEngineUrl(env: PortalEnv | undefined, isDev: boolean): string {
  return (
    env?.SIZING_ENGINE_URL ??
    (isDev ? 'http://127.0.0.1:8000' : 'https://rag-architect-sizing.fly.dev')
  );
}

export function resolveWorkerUrl(env: PortalEnv | undefined, isDev: boolean): string {
  return (
    env?.TELEMETRY_WORKER_URL ??
    (isDev ? 'http://127.0.0.1:8787' : 'https://telemetry-worker.haroudm.workers.dev')
  );
}
