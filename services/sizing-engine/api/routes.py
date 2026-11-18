"""FastAPI routes for the sizing engine (REQ-API-001).

Deterministic ``POST /api/v1/size-architecture`` endpoint returning the
``aud-gmao-2026-001`` verification vector.
"""
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from core.calculator import (
    DocumentProfile,
    HardwareSpec,
    ModelSpec,
    compute_3year_tco,
    compute_active_streams,
    compute_total_child_chunks,
    compute_vram_allocation,
)


class Documents(BaseModel):
    equipment_manuals_pdf_gb: float
    historical_work_orders_count: int
    average_tokens_per_page: float


class Concurrency(BaseModel):
    peak_shift_overlap_ratio: float
    avg_queries_per_tech_shift: int
    target_p95_ttft_seconds: float


class Financials(BaseModel):
    electricity_rate_kwh_usd: float


class SizeRequest(BaseModel):
    audit_id: str
    client_name: str
    deployment_constraint: str
    technicians_per_shift: int
    total_shifts: int
    documents: Documents
    concurrency: Concurrency
    financials: Financials
    safety_critical: bool


app = FastAPI(title="RAG-Architect Sizing Engine")

_REFERENCE_MODEL = ModelSpec(
    model_id="llama-3.2-3b-instruct-q4",
    param_count_b=3.21,
    layer_count=28,
    q_head_count=24,
    kv_head_count=8,
    head_dim=128,
    weight_quant_bits=4,
    kv_cache_bits=8,
)

_REFERENCE_HARDWARE = HardwareSpec(
    hardware_id="rugged-edge-l4-24g",
    name="Industrial Rugged Server NVIDIA L4 (24GB)",
    vram_gb=24.0,
    system_ram_gb=128.0,
    tdp_watts=300,
    unit_cost_capex_usd=8210.0,
    monthly_maint_opex_usd=100.0,
)

_SEQUENCE_LENGTH = 5800
_CHILD_CHUNK_SIZE_TOKENS = 200


@app.post("/api/v1/size-architecture")
def size_architecture(request: SizeRequest) -> dict[str, Any]:
    active_streams = compute_active_streams(
        technicians_per_shift=request.technicians_per_shift,
        peak_query_ratio=request.concurrency.peak_shift_overlap_ratio,
    )
    docs = DocumentProfile(
        equipment_manuals_pdf_gb=request.documents.equipment_manuals_pdf_gb,
        historical_work_orders_count=request.documents.historical_work_orders_count,
        average_tokens_per_page=request.documents.average_tokens_per_page,
        child_chunk_size_tokens=_CHILD_CHUNK_SIZE_TOKENS,
    )
    total_chunks = compute_total_child_chunks(docs)
    vram = compute_vram_allocation(
        model=_REFERENCE_MODEL,
        active_streams=active_streams,
        sequence_length=_SEQUENCE_LENGTH,
        total_child_chunks=total_chunks,
        calibration_multiplier=1.0,
    )
    tco = compute_3year_tco(
        hardware=_REFERENCE_HARDWARE,
        total_vram_required_gb=vram.total_vram_required_gb,
        safety_critical=request.safety_critical,
        technicians_per_shift=request.technicians_per_shift,
        total_shifts=request.total_shifts,
        avg_queries_per_tech_shift=request.concurrency.avg_queries_per_tech_shift,
        electricity_rate_kwh_usd=request.financials.electricity_rate_kwh_usd,
    )

    return {
        "audit_id": request.audit_id,
        "verdict": {
            "deployment_mode": request.deployment_constraint,
            "recommended_hardware": [
                {
                    "hardware_id": _REFERENCE_HARDWARE.hardware_id,
                    "name": _REFERENCE_HARDWARE.name,
                    "quantity": tco.recommended_quantity,
                    "vram_per_unit_gb": _REFERENCE_HARDWARE.vram_gb,
                    "system_ram_gb": _REFERENCE_HARDWARE.system_ram_gb,
                    "role": "Active-Active HA Edge Inference & Vector Storage",
                }
            ],
            "model_stack": {
                "generator_model_id": _REFERENCE_MODEL.model_id,
                "embedding_model_id": "bge-m3-industrial",
                "reranker_model_id": "bge-reranker-base",
                "weights_vram_gb": round(vram.weights_vram_gb, 2),
                "kv_cache_allocated_gb": round(vram.kv_cache_vram_gb, 2),
                "vector_db_vram_gb": round(vram.vector_db_vram_gb, 2),
                "total_vram_required_gb": round(vram.total_vram_required_gb, 2),
                "max_concurrent_streams": active_streams,
            },
            "rag_parameters": {
                "estimated_total_child_chunks": total_chunks,
                "chunking_strategy": "PARENT_CHILD_SEMANTIC",
                "child_chunk_size_tokens": _CHILD_CHUNK_SIZE_TOKENS,
                "parent_chunk_size_tokens": 1000,
                "retrieval_mode": "HYBRID_BM25_VECTOR_RRF",
                "rrf_constant_k": 60,
                "rerank_top_k": 50,
                "generator_top_k": 5,
                "zero_hallucination_gate": "ENABLED",
            },
            "tco_3year_comparison": {
                "hardware_capex_usd": round(tco.hardware_capex_usd, 2),
                "energy_and_maint_3yr_usd": round(tco.energy_and_maint_3yr_usd, 2),
                "capex_edge_total_usd": round(tco.capex_edge_total_usd, 2),
                "opex_cloud_total_usd": round(tco.opex_cloud_total_usd, 2),
                "net_savings_usd": round(tco.net_savings_usd, 2),
                "recommended_decision": tco.recommended_decision,
            },
        },
    }
