"""CMMI Level 3 Verification Suite — Deterministic calculation trace.

Traceability:
- REQ-MATH-001/002/003, REQ-FIN-001 -> step-by-step justification of the
  aud-gmao-2026-001 reference vector.

Methodology: Strict TDD (write and fail before implementing core/trace.py).
"""
from core.calculator import (
    DocumentProfile,
    ModelSpec,
    compute_3year_tco,
    compute_active_streams,
    compute_chunk_breakdown,
    compute_vram_allocation,
)
from core.hardware_selection import CATALOG, select_hardware
from core.trace import CalcStep, build_calculation_trace


def _build_reference_trace() -> list[CalcStep]:
    model = ModelSpec(
        model_id="llama-3.2-3b-instruct-q4",
        param_count_b=3.21,
        layer_count=28,
        q_head_count=24,
        kv_head_count=8,
        head_dim=128,
        weight_quant_bits=4,
        kv_cache_bits=8,
    )
    docs = DocumentProfile(
        equipment_manuals_pdf_gb=85.0,
        historical_work_orders_count=450000,
        average_tokens_per_page=420.0,
        child_chunk_size_tokens=200,
    )
    active_streams = compute_active_streams(35, 0.40)
    chunk = compute_chunk_breakdown(docs)
    vram = compute_vram_allocation(model, active_streams, 5800, chunk.child_chunks, 1.0)
    hardware, quantity = select_hardware(
        CATALOG,
        vram.total_vram_required_gb,
        "AIR_GAPPED_EDGE",
        True,
        0.18,
    )
    tco = compute_3year_tco(
        hardware=hardware,
        total_vram_required_gb=vram.total_vram_required_gb,
        safety_critical=True,
        technicians_per_shift=35,
        total_shifts=3,
        avg_queries_per_tech_shift=15,
        electricity_rate_kwh_usd=0.18,
    )
    return build_calculation_trace(
        model=model,
        hardware=hardware,
        quantity=quantity,
        active_streams=active_streams,
        sequence_length=5800,
        docs=docs,
        chunk=chunk,
        vram=vram,
        tco=tco,
        safety_critical=True,
        technicians=35,
        total_shifts=3,
        avg_queries=15,
        peak_shift_overlap_ratio=0.40,
        electricity_rate=0.18,
        deployment_constraint="AIR_GAPPED_EDGE",
        calibration_multiplier=1.0,
    )


def _step(trace: list[CalcStep], step_id: str) -> CalcStep:
    return next(s for s in trace if s.step_id == step_id)


def test_trace_reproduces_reference_vector() -> None:
    """TEST-TRACE-001: the 19 steps reproduce aud-gmao-2026-001 exactly."""
    trace = _build_reference_trace()
    assert [s.step_id for s in trace] == [
        "active_streams",
        "kv_cache",
        "manuals_tokens",
        "work_order_tokens",
        "total_tokens",
        "child_chunks",
        "weights_vram",
        "vector_db_vram",
        "reranker_vram",
        "headroom_vram",
        "total_vram",
        "hardware_selection",
        "hardware_capex",
        "energy_maint_3yr",
        "capex_edge_total",
        "cloud_volume",
        "opex_cloud_total",
        "net_savings",
        "decision",
    ]

    assert _step(trace, "active_streams").result == 14
    assert _step(trace, "kv_cache").result == "4.66"
    assert _step(trace, "manuals_tokens").result == "89 250 000"
    assert _step(trace, "work_order_tokens").result == "67 500 000"
    assert _step(trace, "total_tokens").result == "156 750 000"
    assert _step(trace, "child_chunks").result == 901313
    assert _step(trace, "weights_vram").result == "1.85"
    assert _step(trace, "vector_db_vram").result == "1.15"
    assert _step(trace, "total_vram").result == "10.96"
    assert _step(trace, "hardware_selection").result == "rugged-edge-l4-24g × 2"
    assert _step(trace, "hardware_capex").result == "16420.00"
    assert _step(trace, "capex_edge_total").result == "26458.24"
    assert _step(trace, "opex_cloud_total").result == "54531.94"
    assert _step(trace, "net_savings").result == "28073.70"
    assert _step(trace, "decision").result == "CAPEX_ON_PREM_EDGE"


def test_trace_is_deterministic() -> None:
    """TEST-TRACE-002: the trace is bit-for-bit reproducible."""
    first = _build_reference_trace()
    second = _build_reference_trace()
    assert first == second
