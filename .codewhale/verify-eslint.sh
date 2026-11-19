#!/usr/bin/env bash
cd /media/malek/DONNEES/pydev/RAG-Architect || exit 1
export PATH="$HOME/.local/bin:$PATH"

echo "=== pnpm version ==="
pnpm --version

echo "=== [1/4] pnpm install (update lockfile + install eslint deps) ==="
pnpm install
echo "pnpm install exit: $?"
echo

echo "=== [2/4] pnpm lint (eslint) ==="
pnpm lint
echo "eslint exit: $?"
echo

echo "=== [3/4] re-verify tsc gates ==="
pnpm --filter @rag-architect/db run check
echo "db check exit: $?"
pnpm --filter @rag-architect/telemetry-worker run check
echo "worker check exit: $?"
pnpm --filter @rag-architect/portal run check
echo "portal check exit: $?"
echo

echo "=== [4/4] verify frozen-lockfile is satisfiable ==="
pnpm install --frozen-lockfile
echo "frozen-lockfile exit: $?"
