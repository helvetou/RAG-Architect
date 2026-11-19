// 21 CFR Part 11 immutable audit-trail helpers (REQ-DB-001, M5 integration).
// Computes SHA-256 payload digests and stamps the immutable version fields.

export interface AuditSubmission {
  actorId: string;
  inputPayloadSha256: string;
  outputPayloadSha256: string;
  specVersion: string;
  modelVersion: string;
}

export async function sha256Hex(data: string): Promise<string> {
  const bytes = new TextEncoder().encode(data);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export async function buildAuditSubmission(
  actorId: string,
  inputJson: string,
  outputJson: string
): Promise<AuditSubmission> {
  return {
    actorId,
    inputPayloadSha256: await sha256Hex(inputJson),
    outputPayloadSha256: await sha256Hex(outputJson),
    specVersion: 'SPEC-GMAO-RAG-ARCH-003',
    modelVersion: 'llama-3.2-3b-instruct-q4',
  };
}
