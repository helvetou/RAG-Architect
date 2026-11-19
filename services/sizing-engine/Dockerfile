# RAG-Architect Sizing Engine — Python 3.12 (uv) production image
# NOTE: the runtime entrypoint uses uvicorn; ensure `uvicorn` is listed in
# pyproject.toml dependencies and uv.lock before this image can serve traffic.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY core ./core
COPY api ./api

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
