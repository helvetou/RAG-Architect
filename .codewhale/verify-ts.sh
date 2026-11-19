#!/usr/bin/env bash
cd /media/malek/DONNEES/pydev/RAG-Architect || exit 1

# 1. Ensure pnpm is available (user-level install, needs network)
if ! command -v pnpm >/dev/null 2>&1; then
  echo "=== installing pnpm@9.12.0 to ~/.local ==="
  npm install -g pnpm@9.12.0 --prefix "$HOME/.local"
fi
export PATH="$HOME/.local/bin:$PATH"
echo "=== pnpm version ==="
pnpm --version

# 2. Install workspace dependencies (generates pnpm-lock.yaml)
echo "=== [1/5] pnpm install ==="
pnpm install
echo "pnpm install exit: $?"
echo

# 3. Type-check each workspace package
echo "=== [2/5] @rag-architect/db : tsc --noEmit ==="
pnpm --filter @rag-architect/db run check
echo "db check exit: $?"
echo

echo "=== [3/5] @rag-architect/telemetry-worker : tsc --noEmit ==="
pnpm --filter @rag-architect/telemetry-worker run check
echo "worker check exit: $?"
echo

echo "=== [4/5] @rag-architect/portal : tsc --noEmit ==="
pnpm --filter @rag-architect/portal run check
echo "portal check exit: $?"
echo

echo "=== [5/5] TypeScript gate verification done ==="
