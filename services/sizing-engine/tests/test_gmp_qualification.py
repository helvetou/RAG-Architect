"""CMMI Level 3 Verification Suite — GMP Qualification Projet 04 (TEST-GMP-001..003).

Traceability: VAL (Validation), VER (Verification), 21 CFR Part 11, RSK-001..004.
Methodology: Strict TDD (write and fail before qualifying).
"""
import gzip
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.routes import app
from core.calibration import (
    RollingTelemetryMetrics,
    evaluate_calibration_loops,
    parse_jsonl_gz,
)
from core.gate import SAFETY_BLOCK_MESSAGE, RetrievedChunk, verify_response_safety

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDEN_PATH = Path(__file__).resolve().parent / "fixtures" / "gmp_projet04_golden.json"
GOLDEN_SHA256 = "250e43a47dae2d614e0459a70e6d7775fcf4261c92e9a9c815a200d36d0a2e96"

client = TestClient(app)


def _load_golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text())


def _canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def test_gmp_001_iq_golden_integrity_and_artifacts() -> None:
    """TEST-GMP-001 (IQ): golden dataset SHA-256, OpenAPI parity, manifests, Drizzle drift."""
    golden = _load_golden()
    assert hashlib.sha256(_canonical(golden).encode()).hexdigest() == GOLDEN_SHA256

    openapi = json.loads((REPO_ROOT / "packages" / "contracts" / "openapi.json").read_text())
    assert "/api/v1/size-architecture" in openapi["paths"]
    assert "SizeRequest" in openapi["components"]["schemas"]

    dockerfile = REPO_ROOT / "services" / "sizing-engine" / "Dockerfile"
    docker_text = dockerfile.read_text()
    assert dockerfile.exists() and "FROM" in docker_text and "uvicorn" in docker_text

    wrangler = REPO_ROOT / "apps" / "telemetry-worker" / "wrangler.toml"
    wrangler_text = wrangler.read_text()
    assert wrangler.exists() and "TELEMETRY_BUCKET" in wrangler_text and "crons" in wrangler_text

    svelte_config = REPO_ROOT / "apps" / "portal" / "svelte.config.js"
    assert svelte_config.exists() and "adapter-cloudflare" in svelte_config.read_text()

    migrations = REPO_ROOT / "packages" / "db" / "migrations"
    assert (migrations / "0000_calm_wallflower.sql").exists()
    assert (migrations / "0001_powerful_spectrum.sql").exists()
    assert (migrations / "meta" / "_journal.json").exists()


def test_gmp_002_oq_100_percent_factual_accuracy() -> None:
    """TEST-GMP-002 (OQ): 100% grounded pass, 100% altered/uncited/spoofed blocked (RSK-001)."""
    golden = _load_golden()
    passed = blocked = 0
    for case in golden["cases"]:
        chunks = [
            RetrievedChunk(
                text=chunk["text"],
                manual_id=chunk.get("manual_id"),
                section=chunk.get("section"),
                page=chunk.get("page"),
            )
            for chunk in case["parent_chunks"]
        ]
        result = verify_response_safety(case["candidate"], chunks)
        if case["expected_safe"]:
            assert result.is_safe is True, f"{case['id']}: expected PASS, got {result}"
            passed += 1
        else:
            assert result.is_safe is False, f"{case['id']}: expected BLOCK, got {result}"
            assert result.final_output == SAFETY_BLOCK_MESSAGE
            blocked += 1

    assert passed >= 5
    assert blocked >= 5


def test_gmp_003_pq_math_jsonl_and_calibration() -> None:
    """TEST-GMP-003 (PQ): math ±0.01, air-gapped .jsonl.gz SHA-256, 3 calibration loops."""
    response = client.post(
        "/api/v1/size-architecture",
        json={
            "audit_id": "gmp-projet04-2026-001",
            "client_name": "Helvetic Precision Manufacturing",
            "deployment_constraint": "AIR_GAPPED_EDGE",
            "technicians_per_shift": 35,
            "total_shifts": 3,
            "documents": {
                "equipment_manuals_pdf_gb": 85.0,
                "historical_work_orders_count": 450000,
                "average_tokens_per_page": 420,
            },
            "concurrency": {
                "peak_shift_overlap_ratio": 0.40,
                "avg_queries_per_tech_shift": 15,
                "target_p95_ttft_seconds": 1.5,
            },
            "financials": {"electricity_rate_kwh_usd": 0.18},
            "safety_critical": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"]["model_stack"]["total_vram_required_gb"] == pytest.approx(10.96, abs=0.01)
    tco = body["verdict"]["tco_3year_comparison"]
    assert tco["capex_edge_total_usd"] == pytest.approx(26458.24, abs=0.01)
    assert tco["opex_cloud_total_usd"] == pytest.approx(54531.94, abs=0.01)
    assert tco["recommended_decision"] == "CAPEX_ON_PREM_EDGE"

    records = [{"client_id": "a", "ttft_ms": 1200}, {"client_id": "b", "ttft_ms": 1600}]
    payload = gzip.compress(("\n".join(json.dumps(r) for r in records) + "\n").encode())
    assert parse_jsonl_gz(payload) == records
    assert hashlib.sha256(payload).hexdigest() == hashlib.sha256(payload).hexdigest()

    loop1 = evaluate_calibration_loops(
        RollingTelemetryMetrics(
            model_id="llama-3.2-3b-instruct-q4",
            hardware_id="rugged-edge-l4-24g",
            hardware_vram_gb=24.0,
            measured_p95_ttft_ms=1680.0,
            measured_peak_vram_gb=18.5,
            measured_context_recall=0.84,
            current_scaling_multiplier=1.0,
            current_child_chunk_tokens=200,
            monthly_token_overrun_ratio=0.05,
        )
    )
    assert loop1.loop1_triggered is True
    assert loop1.updated_scaling_multiplier == pytest.approx(1.20)

    loop23 = evaluate_calibration_loops(
        RollingTelemetryMetrics(
            model_id="llama-3.2-3b-instruct-q4",
            hardware_id="rugged-edge-l4-24g",
            hardware_vram_gb=24.0,
            measured_p95_ttft_ms=1120.0,
            measured_peak_vram_gb=14.0,
            measured_context_recall=0.68,
            current_scaling_multiplier=1.0,
            current_child_chunk_tokens=200,
            monthly_token_overrun_ratio=0.22,
        )
    )
    assert loop23.loop2_triggered is True
    assert loop23.recommended_child_chunk_tokens == 160
    assert loop23.loop3_triggered is True
    assert loop23.enable_semantic_router is True
