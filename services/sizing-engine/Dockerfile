# RAG-Architect Sizing Engine — Python 3.12 (uv) production image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# 1. Installer les dépendances uniquement (couche mise en cache tant que pyproject.toml / uv.lock ne changent pas)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# 2. Copier les métadonnées projet + le code source puis finaliser la synchro uv
COPY pyproject.toml uv.lock ./
COPY core ./core
COPY api ./api

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# 3. Exécution non-root (durcissement production / GMP)
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json', timeout=2)"]

CMD ["uvicorn", "api.routes:app", "--host", "0.0.0.0", "--port", "8000"]

