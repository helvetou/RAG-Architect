"""Deterministic sizing and TCO calculations (REQ-MATH-001/002/003, REQ-FIN-001).

Implements the exact formulas in spec sections 5.1, 5.2, and 5.3 with no
special-case constants beyond the spec's documented coefficients.
"""
import math
from dataclasses import dataclass

# Section 5.2 document/chunk coefficients.
PAGES_PER_GB = 2500
WORK_ORDER_TOKENS = 150
CHUNK_OVERLAP_NUM = 23  # 1.15 overlap factor == 23/20
CHUNK_OVERLAP_DEN = 20
WEIGHTS_OVERHEAD = 1.15
EMBEDDING_DIM = 1024
VECTOR_QUANT_BYTES = 1.0  # SQ8 quantization
HNSW_OVERHEAD = 1.25
RERANKER_VRAM_GB = 2.0
VRAM_HEADROOM_RATIO = 0.20

# Section 5.3 TCO coefficients.
HOURS_PER_MONTH = 730
DAYS_PER_MONTH = 30.4
MONTHS = 36
TOKENS_IN = 5400
TOKENS_OUT = 400
PRICE_IN_PER_1M = 3.00
PRICE_OUT_PER_1M = 15.00
CLOUD_VECTOR_HOST_MONTHLY = 451.84

_BYTES_PER_GB = 1_000_000_000  # SI convention: 1 GB = 1e9 bytes
_TOKENS_PER_1M = 1_000_000


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    param_count_b: float
    layer_count: int
    q_head_count: int
    kv_head_count: int
    head_dim: int
    weight_quant_bits: int
    kv_cache_bits: int


@dataclass(frozen=True)
class HardwareSpec:
    hardware_id: str
    name: str
    vram_gb: float
    system_ram_gb: float
    tdp_watts: int
    unit_cost_capex_usd: float
    monthly_maint_opex_usd: float


@dataclass(frozen=True)
class DocumentProfile:
    equipment_manuals_pdf_gb: float
    historical_work_orders_count: int
    average_tokens_per_page: float
    child_chunk_size_tokens: int


@dataclass(frozen=True)
class VramAllocation:
    weights_vram_gb: float
    kv_cache_vram_gb: float
    vector_db_vram_gb: float
    reranker_vram_gb: float
    total_vram_required_gb: float


@dataclass(frozen=True)
class TcoResult:
    recommended_quantity: int
    hardware_capex_usd: float
    energy_and_maint_3yr_usd: float
    capex_edge_total_usd: float
    opex_cloud_total_usd: float
    net_savings_usd: float
    recommended_decision: str


def compute_active_streams(technicians_per_shift: float, peak_query_ratio: float) -> int:
    """Section 5.1: B_active = ceil(N_techs x R_peak)."""
    return math.ceil(technicians_per_shift * peak_query_ratio)


def compute_kv_cache_gb(active_streams: int, sequence_length: int, model: ModelSpec) -> float:
    """Section 5.1: GQA KV cache memory in GB."""
    return (
        2
        * active_streams
        * sequence_length
        * model.layer_count
        * model.kv_head_count
        * model.head_dim
        * (model.kv_cache_bits / 8)
        / _BYTES_PER_GB
    )


def compute_total_child_chunks(docs: DocumentProfile) -> int:
    """Section 5.2: manuals + work orders -> indexed child chunks with 15% overlap."""
    manuals_tokens = docs.equipment_manuals_pdf_gb * PAGES_PER_GB * docs.average_tokens_per_page
    work_order_tokens = docs.historical_work_orders_count * WORK_ORDER_TOKENS
    total_tokens = manuals_tokens + work_order_tokens
    return math.ceil(
        total_tokens * CHUNK_OVERLAP_NUM / (docs.child_chunk_size_tokens * CHUNK_OVERLAP_DEN)
    )


def compute_vram_allocation(
    model: ModelSpec,
    active_streams: int,
    sequence_length: int,
    total_child_chunks: int,
    calibration_multiplier: float,
) -> VramAllocation:
    """Section 5.2: weights + KV + vectorDB + reranker + 20% headroom, scaled by M_calib."""
    weights = model.param_count_b * (model.weight_quant_bits / 8) * WEIGHTS_OVERHEAD
    kv_cache = compute_kv_cache_gb(active_streams, sequence_length, model)
    vector_db = (
        total_child_chunks * EMBEDDING_DIM * VECTOR_QUANT_BYTES * HNSW_OVERHEAD / _BYTES_PER_GB
    )
    reranker = RERANKER_VRAM_GB
    headroom = VRAM_HEADROOM_RATIO * (weights + kv_cache)
    total = (weights + kv_cache + vector_db + reranker + headroom) * calibration_multiplier
    return VramAllocation(
        weights_vram_gb=weights,
        kv_cache_vram_gb=kv_cache,
        vector_db_vram_gb=vector_db,
        reranker_vram_gb=reranker,
        total_vram_required_gb=total,
    )


def compute_3year_tco(
    hardware: HardwareSpec,
    total_vram_required_gb: float,
    safety_critical: bool,
    technicians_per_shift: int,
    total_shifts: int,
    avg_queries_per_tech_shift: int,
    electricity_rate_kwh_usd: float,
) -> TcoResult:
    """Section 5.3: 36-month edge CAPEX vs cloud OPEX TCO."""
    quantity = math.ceil(total_vram_required_gb / hardware.vram_gb)
    if safety_critical:
        quantity = max(2, quantity)

    hardware_capex = hardware.unit_cost_capex_usd * quantity
    energy_monthly = (
        hardware.tdp_watts * quantity * HOURS_PER_MONTH * electricity_rate_kwh_usd / 1000
    )
    maintenance_monthly = hardware.monthly_maint_opex_usd * quantity
    energy_and_maint_3yr = (energy_monthly + maintenance_monthly) * MONTHS
    capex_edge_total = hardware_capex + energy_and_maint_3yr

    volume_monthly = (
        technicians_per_shift * total_shifts * avg_queries_per_tech_shift * DAYS_PER_MONTH
    )
    token_cost_monthly = (
        (TOKENS_IN * PRICE_IN_PER_1M + TOKENS_OUT * PRICE_OUT_PER_1M) / _TOKENS_PER_1M
    ) * volume_monthly
    opex_monthly = token_cost_monthly + CLOUD_VECTOR_HOST_MONTHLY
    opex_cloud_total = opex_monthly * MONTHS

    net_savings = opex_cloud_total - capex_edge_total
    decision = "CAPEX_ON_PREM_EDGE" if capex_edge_total < opex_cloud_total else "OPEX_CLOUD_MANAGED"

    return TcoResult(
        recommended_quantity=quantity,
        hardware_capex_usd=hardware_capex,
        energy_and_maint_3yr_usd=energy_and_maint_3yr,
        capex_edge_total_usd=capex_edge_total,
        opex_cloud_total_usd=opex_cloud_total,
        net_savings_usd=net_savings,
        recommended_decision=decision,
    )
