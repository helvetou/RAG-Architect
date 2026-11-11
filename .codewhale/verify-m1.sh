#!/usr/bin/env bash
set +e
cd /media/malek/DONNEES/pydev/RAG-Architect || exit 1

echo "=== 1. Arborescence créée (hors .git) ==="
find . -type f -not -path './.git/*' | sort

echo
echo "=== 2. Validité TOML (pyproject.toml) ==="
python3 -c "import tomllib; d=tomllib.load(open('services/sizing-engine/pyproject.toml','rb')); print('TOML OK — name:', d['project']['name'], '| requires-python:', d['project']['requires-python'])"

echo
echo "=== 3. Validité JSON (package.json / tsconfig.json) ==="
for f in $(find . \( -name package.json -o -name tsconfig.json \) | sort); do
  python3 -m json.tool "$f" > /dev/null 2>&1 && echo "JSON OK : $f" || echo "JSON FAIL: $f"
done

echo
echo "=== 4. Traçabilité RTM (REQ-* vs TEST-*) ==="
echo -n "REQ uniques : "; grep -oE 'REQ-[A-Z]+-[0-9]+' docs/cmmi/rtm-v3.md | sort -u | wc -l
echo -n "TEST uniques: "; grep -oE 'TEST-[A-Z]+-[0-9]+[a-c]?' docs/cmmi/rtm-v3.md | sort -u | wc -l
grep -oE 'REQ-[A-Z]+-[0-9]+' docs/cmmi/rtm-v3.md | sort -u

echo
echo "=== 5. Outils système disponibles ==="
python3 -m pytest --version 2>&1 | head -2
command -v ruff >/dev/null 2>&1 && ruff --version || echo "ruff: absent"
command -v mypy >/dev/null 2>&1 && mypy --version || echo "mypy: absent"
command -v tsc >/dev/null 2>&1 && tsc --version || echo "tsc: absent"

echo
echo "=== 6. Tentative uv (cache redirigé workspace + offline) ==="
export UV_CACHE_DIR=/media/malek/DONNEES/pydev/RAG-Architect/.uv-cache
export UV_PYTHON_INSTALL_DIR="$UV_CACHE_DIR/python"
cd services/sizing-engine || exit 1
timeout 45 uv run --offline ruff check . 2>&1 | tail -25
echo "uv exit code: ${PIPESTATUS[0]}"
