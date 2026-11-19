// See https://svelte.dev/docs/kit/types#app.d.ts for information about these interfaces
declare global {
  namespace App {
    interface Platform {
      env?: {
        DB?: D1Database;
        AUTH_TOKEN?: string;
        TELEMETRY_WORKER_URL?: string;
        SIZING_ENGINE_URL?: string;
      };
    }
  }
}

export {};
