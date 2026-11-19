"""Export the FastAPI OpenAPI schema to the shared contracts directory.

Run with: uv run python scripts/export_openapi.py
Output: packages/contracts/openapi.json (consumed by apps/portal Zod contract tests).
"""
import json
import sys
from pathlib import Path

SIZING_ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIZING_ENGINE))

from api.routes import app  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_DIR = REPO_ROOT / "packages" / "contracts"
OUTPUT = CONTRACTS_DIR / "openapi.json"


def main() -> None:
    schema = app.openapi()
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"OpenAPI schema written to {OUTPUT}")


if __name__ == "__main__":
    main()
