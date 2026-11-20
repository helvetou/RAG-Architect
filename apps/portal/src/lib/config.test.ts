// CMMI Level 3 Verification Suite — deployment URL isolation (rag-architect).
import { describe, expect, it } from 'vitest';

import { resolveEngineUrl, resolveWorkerUrl } from './config';

describe('deployment URL resolution (rag-architect isolation)', () => {
  it('production defaults point at rag-architect services', () => {
    expect(resolveEngineUrl(undefined, false)).toBe('https://rag-architect-sizing.fly.dev');
    expect(resolveWorkerUrl(undefined, false)).toBe('https://telemetry-worker.haroudm.workers.dev');
  });

  it('dev defaults fall back to localhost', () => {
    expect(resolveEngineUrl(undefined, true)).toBe('http://127.0.0.1:8000');
    expect(resolveWorkerUrl(undefined, true)).toBe('http://127.0.0.1:8787');
  });

  it('env overrides win', () => {
    expect(resolveEngineUrl({ SIZING_ENGINE_URL: 'https://custom.example' }, false)).toBe(
      'https://custom.example'
    );
    expect(resolveWorkerUrl({ TELEMETRY_WORKER_URL: 'https://worker.example' }, true)).toBe(
      'https://worker.example'
    );
  });

  it('normalizes Markdown-link formatted URLs ([label](url))', () => {
    expect(
      resolveEngineUrl(
        {
          SIZING_ENGINE_URL:
            '[https://rag-architect-sizing.fly.dev](https://rag-architect-sizing.fly.dev)',
        },
        false
      )
    ).toBe('https://rag-architect-sizing.fly.dev');
  });

  it('strips trailing slashes and angle brackets', () => {
    expect(
      resolveEngineUrl({ SIZING_ENGINE_URL: 'https://rag-architect-sizing.fly.dev/' }, false)
    ).toBe('https://rag-architect-sizing.fly.dev');
    expect(
      resolveWorkerUrl(
        { TELEMETRY_WORKER_URL: '<https://telemetry-worker.haroudm.workers.dev>' },
        false
      )
    ).toBe('https://telemetry-worker.haroudm.workers.dev');
  });

  it('falls back to the default on malformed URLs', () => {
    expect(resolveEngineUrl({ SIZING_ENGINE_URL: 'not-a-url' }, false)).toBe(
      'https://rag-architect-sizing.fly.dev'
    );
    expect(resolveWorkerUrl({ TELEMETRY_WORKER_URL: '   ' }, true)).toBe('http://127.0.0.1:8787');
  });
});
