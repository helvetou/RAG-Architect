// CMMI Level 3 Verification Suite — 21 CFR Part 11 audit trail (TEST-INT-001, M5)
// Traceability: REQ-DB-001 (audit_submissions append-only), 21 CFR Part 11 readiness.
import { describe, expect, it } from 'vitest';

import { buildAuditSubmission, sha256Hex } from './audit';

describe('audit trail (21 CFR Part 11)', () => {
  it('sha256Hex produces the standard SHA-256 digest', async () => {
    expect(await sha256Hex('abc')).toBe(
      'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    );
  });

  it('buildAuditSubmission hashes input/output payloads and stamps immutable versions', async () => {
    const input = '{"technicians_per_shift":35}';
    const output = '{"total_vram_required_gb":10.96}';
    const submission = await buildAuditSubmission('engineer-1', input, output);

    expect(submission.actorId).toBe('engineer-1');
    expect(submission.inputPayloadSha256).toBe(await sha256Hex(input));
    expect(submission.outputPayloadSha256).toBe(await sha256Hex(output));
    expect(submission.specVersion).toBe('SPEC-GMAO-RAG-ARCH-003');
    expect(submission.modelVersion).toBe('llama-3.2-3b-instruct-q4');
  });
});
