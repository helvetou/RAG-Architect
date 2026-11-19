#!/usr/bin/env bash
cd /media/malek/DONNEES/pydev/RAG-Architect || exit 1
export PATH="$HOME/.local/bin:$PATH"

echo "=== [1/2] pnpm install (new db deps) ==="
pnpm install
echo "pnpm install exit: $?"
echo

echo "=== [2/2] vitest run (expect RED failure: schema.ts/seed.ts missing) ==="
pnpm --filter @rag-architect/db run test
echo "vitest exit: $?"
