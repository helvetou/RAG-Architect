// CMMI Level 3 Verification Suite — 21 CFR Part 11 immutable audit trail (TEST-GMP-004)
// Traceability: REQ-DB-001, 21 CFR Part 11, migration 0001 append-only triggers.
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { eq } from 'drizzle-orm';
import { migrate } from 'drizzle-orm/better-sqlite3/migrator';

import { auditSubmissions, hardwareCatalog, modelRegistry } from '../src/schema';
import { hardwareSeeds, modelSeeds } from '../src/seed';

const migrationsDir = fileURLToPath(new URL('../migrations', import.meta.url));

function sha256(data: string): string {
  return createHash('sha256').update(data, 'utf8').digest('hex');
}

function setupDb() {
  const sqlite = new Database(':memory:');
  sqlite.pragma('foreign_keys = ON');
  const db = drizzle(sqlite);
  migrate(db, { migrationsFolder: migrationsDir });
  db.insert(hardwareCatalog).values(hardwareSeeds).run();
  db.insert(modelRegistry).values(modelSeeds).run();
  return { sqlite, db };
}

describe('TEST-GMP-004 — 21 CFR Part 11 immutable audit trail', () => {
  it('inserts a full audit record with deterministic hashes and rejects UPDATE/DELETE', () => {
    const { db } = setupDb();

    const input = JSON.stringify({ technicians_per_shift: 35, deployment_constraint: 'AIR_GAPPED_EDGE' });
    const output = JSON.stringify({ total_vram_required_gb: 10.96, decision: 'CAPEX_ON_PREM_EDGE' });
    const inputHash = sha256(input);
    const outputHash = sha256(output);

    // Deterministic reproducibility of the SHA-256 digests
    expect(sha256(input)).toBe(inputHash);
    expect(sha256(output)).toBe(outputHash);

    db.insert(auditSubmissions)
      .values({
        id: 'audit-gmp-004',
        clientName: 'Helvetic Precision Manufacturing',
        techniciansPerShift: 35,
        totalShifts: 3,
        manualsVolumeGb: 85,
        historicalWorkOrdersCount: 450000,
        avgTokensPerPage: 420,
        deploymentConstraint: 'AIR_GAPPED_EDGE',
        peakQueryRatio: 0.4,
        avgQueriesPerTechShift: 15,
        electricityRateKwhUsd: 0.18,
        targetP95TtftSeconds: 1.5,
        createdAt: new Date(),
        actorId: 'qa-engineer-1',
        inputPayloadSha256: inputHash,
        outputPayloadSha256: outputHash,
        inputPayloadJson: input,
        outputPayloadJson: output,
        specVersion: 'SPEC-GMAO-RAG-ARCH-003',
        modelVersion: 'llama-3.2-3b-instruct-q4',
      })
      .run();

    // Replayability: the full payloads are persisted verbatim (not just hashes).
    const stored = db
      .select()
      .from(auditSubmissions)
      .where(eq(auditSubmissions.id, 'audit-gmp-004'))
      .get();
    expect(stored?.inputPayloadJson).toBe(input);
    expect(stored?.outputPayloadJson).toBe(output);

    // Append-only: UPDATE must raise SQLite ABORT (migration 0001 trigger)
    expect(() => db.update(auditSubmissions).set({ actorId: 'tampered' }).run()).toThrow();
    // Append-only: DELETE must raise SQLite ABORT (migration 0001 trigger)
    expect(() => db.delete(auditSubmissions).run()).toThrow();
  });
});
