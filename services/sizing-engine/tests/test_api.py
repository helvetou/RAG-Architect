"""
CMMI Level 3 Verification Suite — Sizing Engine REST API.

Traceability:
- REQ-API-001 -> TEST-API-001

Methodology: Strict TDD (write and fail before implementing api/routes.py).
Reference vector: `aud-gmao-2026-001` (spec section 6.1).
"""
import pytest
from fastapi.testclient import TestClient

from api.routes import app

client = TestClient(app)

REFERENCE_REQUEST = {
    "audit_id": "aud-gmao-2026-001",
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
}


def test_req_api_001_size_architecture_reference_vector() -> None:
    """TEST-API-001 (REQ-API-001): endpoint returns the aud-gmao-2026-001 vector."""
    response = client.post("/api/v1/size-architecture", json=REFERENCE_REQUEST)
    assert response.status_code == 200

    body = response.json()
    verdict = body["verdict"]
    model_stack = verdict["model_stack"]
    rag = verdict["rag_parameters"]
    tco = verdict["tco_3year_comparison"]

    assert body["audit_id"] == "aud-gmao-2026-001"
    assert verdict["deployment_mode"] == "AIR_GAPPED_EDGE"
    assert model_stack["weights_vram_gb"] == pytest.approx(1.85, abs=0.01)
    assert model_stack["kv_cache_allocated_gb"] == pytest.approx(4.66, abs=0.01)
    assert model_stack["vector_db_vram_gb"] == pytest.approx(1.15, abs=0.01)
    assert model_stack["total_vram_required_gb"] == pytest.approx(10.96, abs=0.01)
    assert model_stack["max_concurrent_streams"] == 14
    assert rag["estimated_total_child_chunks"] == 901313
    assert rag["zero_hallucination_gate"] == "ENABLED"
    assert tco["hardware_capex_usd"] == pytest.approx(16420.00, abs=0.01)
    assert tco["energy_and_maint_3yr_usd"] == pytest.approx(10038.24, abs=0.01)
    assert tco["capex_edge_total_usd"] == pytest.approx(26458.24, abs=0.01)
    assert tco["opex_cloud_total_usd"] == pytest.approx(54531.94, abs=0.01)
    assert tco["net_savings_usd"] == pytest.approx(28073.70, abs=0.01)
    assert tco["recommended_decision"] == "CAPEX_ON_PREM_EDGE"
