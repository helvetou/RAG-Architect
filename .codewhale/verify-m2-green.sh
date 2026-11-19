#!/usr/bin/env bash
cd /media/malek/DONNEES/pydev/RAG-Architect || exit 1
export PATH="$HOME/.local/bin:$PATH"

echo "=== [1/4] drizzle-kit generate ==="
pnpm --filter @rag-architect/db run db:generate
echo "generate exit: $?"
echo

echo "=== [2/4] tsc --noEmit (type check) ==="
pnpm --filter @rag-architect/db run check
echo "tsc exit: $?"
echo

echo "=== [3/4] vitest run (expect GREEN: all tests pass) ==="
pnpm --filter @rag-architect/db run test
echo "vitest exit: $?"
echo

echo "=== [4/4] drizzle-kit check (zero drift) ==="
pnpm --filter @rag-architect/db run db:check
echo "drizzle-kit check exit: $?"
