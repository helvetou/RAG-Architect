"""
CMMI Level 3 Verification Suite — Sizing & TCO Calculator.

Traceability:
- REQ-MATH-001 -> TEST-MATH-001
- REQ-MATH-002 -> TEST-MATH-002
- REQ-MATH-003 -> TEST-MATH-003
- REQ-FIN-001  -> TEST-FIN-001

Methodology: Strict TDD (write and fail before implementing core/calculator.py).
Reference vector: `aud-gmao-2026-001`.
"""
import pytest

from core.calculator import (
    DocumentProfile,
    HardwareSpec,
    ModelSpec,
    compute_3year_tco,
    compute_active_streams,
    compute_kv_cache_gb,
    compute_total_child_chunks,
    compute_vram_allocation,
)


@pytest.fixture
def llama_3_2_3b_q4() -> ModelSpec:
    """Reference model fixture (llama-3.2-3b-instruct-q4) per `aud-gmao-2026-001`."""
    return ModelSpec(
        model_id="llama-3.2-3b-instruct-q4",
        param_count_b=3.21,
        layer_count=28,
        q_head_count=24,
        kv_head_count=8,
        head_dim=128,
        weight_quant_bits=4,
        kv_cache_bits=8,
    )


@pytest.fixture
def rugged_l4_24g() -> HardwareSpec:
    """Reference hardware fixture (rugged-edge-l4-24g) per `aud-gmao-2026-001`."""
    return HardwareSpec(
        hardware_id="rugged-edge-l4-24g",
        name="Industrial Rugged Server NVIDIA L4 (24GB)",
        vram_gb=24.0,
        system_ram_gb=128.0,
        tdp_watts=300,
        unit_cost_capex_usd=8210.0,
        monthly_maint_opex_usd=100.0,
    )


def test_req_math_001_active_streams_and_kv_cache(llama_3_2_3b_q4: ModelSpec) -> None:
    """TEST-MATH-001 (REQ-MATH-001): B_active = ceil(35 x 0.40) = 14; GQA KV cache = 4.66 GB."""
    active_streams = compute_active_streams(technicians_per_shift=35, peak_query_ratio=0.40)
    assert active_streams == 14

    kv_cache_gb = compute_kv_cache_gb(
        active_streams=active_streams,
        sequence_length=5800,
        model=llama_3_2_3b_q4,
    )
    assert round(kv_cache_gb, 2) == 4.66


def test_req_math_002_document_to_chunk_conversion() -> None:
    """TEST-MATH-002 (REQ-MATH-002): 85 GB manuals + 450k work orders -> 901 313 child chunks."""
    docs = DocumentProfile(
        equipment_manuals_pdf_gb=85.0,
        historical_work_orders_count=450000,
        average_tokens_per_page=420,
        child_chunk_size_tokens=200,
    )
    total_chunks = compute_total_child_chunks(docs)
    assert total_chunks == 901313


def test_req_math_003_total_vram_allocation(llama_3_2_3b_q4: ModelSpec) -> None:
    """TEST-MATH-003 (REQ-MATH-003): total VRAM allocation = 10.96 GB."""
    vram = compute_vram_allocation(
        model=llama_3_2_3b_q4,
        active_streams=14,
        sequence_length=5800,
        total_child_chunks=901313,
        calibration_multiplier=1.0,
    )
    assert round(vram.weights_vram_gb, 2) == 1.85
    assert round(vram.kv_cache_vram_gb, 2) == 4.66
    assert round(vram.vector_db_vram_gb, 2) == 1.15
    assert round(vram.reranker_vram_gb, 2) == 2.00
    assert round(vram.total_vram_required_gb, 2) == 10.96


def test_req_fin_001_three_year_tco(rugged_l4_24g: HardwareSpec) -> None:
    """TEST-FIN-001 (REQ-FIN-001): 3-yr CAPEX vs OPEX -> CAPEX_ON_PREM_EDGE."""
    tco = compute_3year_tco(
        hardware=rugged_l4_24g,
        total_vram_required_gb=10.96,
        safety_critical=True,
        technicians_per_shift=35,
        total_shifts=3,
        avg_queries_per_tech_shift=15,
        electricity_rate_kwh_usd=0.18,
    )
    assert tco.recommended_quantity == 2
    assert round(tco.hardware_capex_usd, 2) == 16420.00
    assert round(tco.energy_and_maint_3yr_usd, 2) == 10038.24
    assert round(tco.capex_edge_total_usd, 2) == 26458.24
    assert round(tco.opex_cloud_total_usd, 2) == 54531.94
    assert round(tco.net_savings_usd, 2) == 28073.70
    assert tco.recommended_decision == "CAPEX_ON_PREM_EDGE"
