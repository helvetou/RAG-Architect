// CMMI Level 3 Verification Suite — D1 Relational Schema & Seed Integrity
// Traceability: REQ-DB-001
// Test Cases: TEST-DB-001 (schema columns), TEST-DB-002 (seed integrity + FK enforcement)
// Methodology: Strict TDD (RED first)
import { describe, it, expect } from 'vitest';
import { fileURLToPath } from 'node:url';
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { migrate } from 'drizzle-orm/better-sqlite3/migrator';
import { eq, getTableColumns } from 'drizzle-orm';
import type { AnySQLiteTable } from 'drizzle-orm/sqlite-core';
import {
  hardwareCatalog,
  modelRegistry,
  auditSubmissions,
  telemetryCalibration,
} from '../src/schema';
import { hardwareSeeds, modelSeeds } from '../src/seed';

const migrationsDir = fileURLToPath(new URL('../migrations', import.meta.url));

function dbColumnNames(table: AnySQLiteTable): string[] {
  return Object.keys(getTableColumns(table));
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

describe('TEST-DB-001 — Schema columns (REQ-DB-001)', () => {
  it('defines the four required tables', () => {
    expect(hardwareCatalog).toBeDefined();
    expect(modelRegistry).toBeDefined();
    expect(auditSubmissions).toBeDefined();
    expect(telemetryCalibration).toBeDefined();
  });

  it('modelRegistry exposes the GQA attention parameters', () => {
    const columns = dbColumnNames(modelRegistry);
    expect(columns).toEqual(
      expect.arrayContaining(['qHeadCount', 'kvHeadCount', 'headDim', 'kvCacheBits']),
    );
  });

  it('auditSubmissions exposes document & concurrency parameters', () => {
    const columns = dbColumnNames(auditSubmissions);
    expect(columns).toEqual(
      expect.arrayContaining(['avgTokensPerPage', 'avgQueriesPerTechShift', 'electricityRateKwhUsd']),
    );
  });
});

describe('TEST-DB-002 — Seed integrity & foreign keys (REQ-DB-001)', () => {
  it('seeds the deterministic hardware & model catalog', () => {
    const { db } = setupDb();
    const llama = db
      .select()
      .from(modelRegistry)
      .where(eq(modelRegistry.id, 'llama-3.2-3b-instruct-q4'))
      .get();
    expect(llama?.qHeadCount).toBe(24);
    expect(llama?.kvHeadCount).toBe(8);
    expect(llama?.headDim).toBe(128);

    const hardware = db.select().from(hardwareCatalog).all();
    expect(hardware.map((h) => h.id)).toEqual(
      expect.arrayContaining(['rugged-edge-l4-24g', 'rugged-dual-a4500-40g', 'nvidia-l40s', 'edgestream-gw-01']),
    );
  });

  it('enforces foreign keys on telemetryCalibration (invalid parents rejected)', () => {
    const { db } = setupDb();
    expect(() =>
      db
        .insert(telemetryCalibration)
        .values({
          id: 'cal-bad-fk',
          modelId: 'missing-model',
          hardwareId: 'missing-hardware',
          measuredP95TtftMs: 1180.4,
          measuredPeakVramGb: 10.45,
          measuredContextRecall: 0.84,
          measuredFaithfulness: 0.9,
          computeScalingMultiplier: 1.0,
          rollingSampleCount: 7,
          lastUpdated: new Date(),
        })
        .run(),
    ).toThrow();
  });

  it('accepts a valid telemetryCalibration row referencing seeded parents', () => {
    const { db } = setupDb();
    expect(() =>
      db
        .insert(telemetryCalibration)
        .values({
          id: 'cal-ok',
          modelId: 'llama-3.2-3b-instruct-q4',
          hardwareId: 'rugged-edge-l4-24g',
          measuredP95TtftMs: 1180.4,
          measuredPeakVramGb: 10.45,
          measuredContextRecall: 0.84,
          measuredFaithfulness: 0.9,
          computeScalingMultiplier: 1.0,
          rollingSampleCount: 7,
          lastUpdated: new Date(),
        })
        .run(),
    ).not.toThrow();
  });
});
