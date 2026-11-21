"""Deterministic calculation trace (justification of every computed number).

Each :class:`CalcStep` captures the human-readable formula, the substituted
expression with the actual inputs, the result, its unit and the governing spec
section. Used to render the HTML "calculation justification" report and stored
in the immutable audit trail (REQ-FIN-001, REQ-MATH-001/002/003).
"""
from dataclasses import dataclass
from typing import Any

from core.calculator import (
    CHUNK_OVERLAP_DEN,
    CHUNK_OVERLAP_NUM,
    CLOUD_VECTOR_HOST_MONTHLY,
    DAYS_PER_MONTH,
    EMBEDDING_DIM,
    HNSW_OVERHEAD,
    MONTHS,
    PAGES_PER_GB,
    PRICE_IN_PER_1M,
    PRICE_OUT_PER_1M,
    RERANKER_VRAM_GB,
    TOKENS_IN,
    TOKENS_OUT,
    VECTOR_QUANT_BYTES,
    VRAM_HEADROOM_RATIO,
    WEIGHTS_OVERHEAD,
    WORK_ORDER_TOKENS,
    ChunkCalculation,
    DocumentProfile,
    HardwareSpec,
    ModelSpec,
    TcoResult,
    VramAllocation,
)
from core.hardware_selection import CATALOG, HardwareCandidate, evaluate_candidates


@dataclass(frozen=True)
class CalcStep:
    step_id: str
    label: str
    formula: str
    inputs: dict[str, Any]
    expression: str
    result: Any
    unit: str
    spec_section: str


def _gb(value: float) -> str:
    return f"{value:.2f}"


def _usd(value: float) -> str:
    return f"{value:.2f}"


def _tokens(value: float) -> str:
    return f"{int(value):,}".replace(",", " ")


def build_calculation_trace(
    *,
    model: ModelSpec,
    hardware: HardwareSpec,
    quantity: int,
    active_streams: int,
    sequence_length: int,
    docs: DocumentProfile,
    chunk: ChunkCalculation,
    vram: VramAllocation,
    tco: TcoResult,
    safety_critical: bool,
    technicians: int,
    total_shifts: int,
    avg_queries: int,
    peak_shift_overlap_ratio: float,
    electricity_rate: float,
    deployment_constraint: str,
    calibration_multiplier: float,
) -> list[CalcStep]:
    """Produce the ordered, deterministic list of calculation steps."""
    candidates: list[HardwareCandidate] = evaluate_candidates(
        CATALOG,
        vram.total_vram_required_gb,
        deployment_constraint,
        safety_critical,
        electricity_rate,
    )
    candidate_text = " ; ".join(
        f"{c.hardware.hardware_id} x{c.quantity} = ${c.capex_edge_total_usd:.2f}"
        for c in candidates
    )
    volume = technicians * total_shifts * avg_queries * DAYS_PER_MONTH

    steps: list[CalcStep] = [
        CalcStep(
            step_id="active_streams",
            label="Streams actifs (B_active)",
            formula="ceil(N_techs × R_peak)",
            inputs={"N_techs": technicians, "R_peak": peak_shift_overlap_ratio},
            expression=f"ceil({technicians} × {peak_shift_overlap_ratio:g})",
            result=active_streams,
            unit="streams",
            spec_section="5.1",
        ),
        CalcStep(
            step_id="kv_cache",
            label="KV Cache (GQA)",
            formula="2 × B_active × L_seq × N_layers × H_kv × D_head × (kv_bits/8) / 1e9",
            inputs={
                "B_active": active_streams,
                "L_seq": sequence_length,
                "N_layers": model.layer_count,
                "H_kv": model.kv_head_count,
                "D_head": model.head_dim,
                "kv_bits": model.kv_cache_bits,
            },
            expression=(
                f"2 × {active_streams} × {sequence_length} × {model.layer_count} "
                f"× {model.kv_head_count} × {model.head_dim} × ({model.kv_cache_bits}/8) / 1e9"
            ),
            result=_gb(vram.kv_cache_vram_gb),
            unit="GB",
            spec_section="5.1",
        ),
        CalcStep(
            step_id="manuals_tokens",
            label="Tokens des manuels",
            formula="manuals_GB × pages_per_GB × tokens_per_page",
            inputs={
                "manuals_GB": docs.equipment_manuals_pdf_gb,
                "pages_per_GB": PAGES_PER_GB,
                "tokens_per_page": docs.average_tokens_per_page,
            },
            expression=(
                f"{docs.equipment_manuals_pdf_gb:g} × {PAGES_PER_GB} "
                f"× {docs.average_tokens_per_page:g}"
            ),
            result=_tokens(chunk.manuals_tokens),
            unit="tokens",
            spec_section="5.2",
        ),
        CalcStep(
            step_id="work_order_tokens",
            label="Tokens des ordres de travail",
            formula="work_orders × tokens_per_work_order",
            inputs={
                "work_orders": docs.historical_work_orders_count,
                "tokens_per_work_order": WORK_ORDER_TOKENS,
            },
            expression=f"{docs.historical_work_orders_count} × {WORK_ORDER_TOKENS}",
            result=_tokens(chunk.work_order_tokens),
            unit="tokens",
            spec_section="5.2",
        ),
        CalcStep(
            step_id="total_tokens",
            label="Total tokens du corpus",
            formula="manuals_tokens + work_order_tokens",
            inputs={
                "manuals_tokens": _tokens(chunk.manuals_tokens),
                "work_order_tokens": _tokens(chunk.work_order_tokens),
            },
            expression=f"{_tokens(chunk.manuals_tokens)} + {_tokens(chunk.work_order_tokens)}",
            result=_tokens(chunk.total_tokens),
            unit="tokens",
            spec_section="5.2",
        ),
        CalcStep(
            step_id="child_chunks",
            label="Chunks enfants (avec chevauchement)",
            formula="ceil(total_tokens × overlap_num / (child_size × overlap_den))",
            inputs={
                "total_tokens": _tokens(chunk.total_tokens),
                "overlap_num": CHUNK_OVERLAP_NUM,
                "child_size": docs.child_chunk_size_tokens,
                "overlap_den": CHUNK_OVERLAP_DEN,
            },
            expression=(
                f"ceil({_tokens(chunk.total_tokens)} × {CHUNK_OVERLAP_NUM} "
                f"/ ({docs.child_chunk_size_tokens} × {CHUNK_OVERLAP_DEN}))"
            ),
            result=chunk.child_chunks,
            unit="chunks",
            spec_section="5.2",
        ),
        CalcStep(
            step_id="weights_vram",
            label="VRAM poids (modèle quantifié)",
            formula="param_count_b × (weight_quant_bits/8) × overhead",
            inputs={
                "param_count_b": model.param_count_b,
                "weight_quant_bits": model.weight_quant_bits,
                "overhead": WEIGHTS_OVERHEAD,
            },
            expression=(
                f"{model.param_count_b} × ({model.weight_quant_bits}/8) "
                f"× {WEIGHTS_OVERHEAD}"
            ),
            result=_gb(vram.weights_vram_gb),
            unit="GB",
            spec_section="5.2",
        ),
        CalcStep(
            step_id="vector_db_vram",
            label="VRAM base vectorielle (HNSW, SQ8)",
            formula="child_chunks × embedding_dim × quant_bytes × hnsw_overhead / 1e9",
            inputs={
                "child_chunks": chunk.child_chunks,
                "embedding_dim": EMBEDDING_DIM,
                "quant_bytes": VECTOR_QUANT_BYTES,
                "hnsw_overhead": HNSW_OVERHEAD,
            },
            expression=(
                f"{chunk.child_chunks} × {EMBEDDING_DIM} × {VECTOR_QUANT_BYTES:g} "
                f"× {HNSW_OVERHEAD} / 1e9"
            ),
            result=_gb(vram.vector_db_vram_gb),
            unit="GB",
            spec_section="5.2",
        ),
        CalcStep(
            step_id="reranker_vram",
            label="VRAM reranker",
            formula="RERANKER_VRAM_GB",
            inputs={"reranker": RERANKER_VRAM_GB},
            expression=f"{RERANKER_VRAM_GB:g} (fixe)",
            result=_gb(vram.reranker_vram_gb),
            unit="GB",
            spec_section="5.2",
        ),
        CalcStep(
            step_id="headroom_vram",
            label="Marge de sécurité (20 %)",
            formula="headroom_ratio × (weights + kv_cache)",
            inputs={
                "headroom_ratio": VRAM_HEADROOM_RATIO,
                "weights": _gb(vram.weights_vram_gb),
                "kv_cache": _gb(vram.kv_cache_vram_gb),
            },
            expression=(
                f"{VRAM_HEADROOM_RATIO} × ({_gb(vram.weights_vram_gb)} "
                f"+ {_gb(vram.kv_cache_vram_gb)})"
            ),
            result=_gb(vram.headroom_vram_gb),
            unit="GB",
            spec_section="5.2",
        ),
        CalcStep(
            step_id="total_vram",
            label="VRAM totale requise",
            formula="(weights + kv_cache + vector_db + reranker + headroom) × M_calib",
            inputs={
                "weights": _gb(vram.weights_vram_gb),
                "kv_cache": _gb(vram.kv_cache_vram_gb),
                "vector_db": _gb(vram.vector_db_vram_gb),
                "reranker": _gb(vram.reranker_vram_gb),
                "headroom": _gb(vram.headroom_vram_gb),
                "M_calib": calibration_multiplier,
            },
            expression=(
                f"({_gb(vram.weights_vram_gb)} + {_gb(vram.kv_cache_vram_gb)} "
                f"+ {_gb(vram.vector_db_vram_gb)} + {_gb(vram.reranker_vram_gb)} "
                f"+ {_gb(vram.headroom_vram_gb)}) × {calibration_multiplier:g}"
            ),
            result=_gb(vram.total_vram_required_gb),
            unit="GB",
            spec_section="5.2",
        ),
        CalcStep(
            step_id="hardware_selection",
            label="Sélection matérielle (TCO minimal)",
            formula="min(3yr edge cost) sur candidats compatibles avec le mode",
            inputs={"deployment": deployment_constraint, "candidates": candidate_text},
            expression=candidate_text,
            result=f"{hardware.hardware_id} × {quantity}",
            unit="-",
            spec_section="5.3",
        ),
        CalcStep(
            step_id="hardware_capex",
            label="CAPEX matériel",
            formula="unit_cost × quantity",
            inputs={"unit_cost": hardware.unit_cost_capex_usd, "quantity": quantity},
            expression=f"{hardware.unit_cost_capex_usd:g} × {quantity}",
            result=_usd(tco.hardware_capex_usd),
            unit="USD",
            spec_section="5.3",
        ),
        CalcStep(
            step_id="energy_maint_3yr",
            label="Énergie + maintenance (3 ans)",
            formula="(tdp × qty × hours × rate / 1000 + maint × qty) × months",
            inputs={
                "tdp": hardware.tdp_watts,
                "qty": quantity,
                "hours": 730,
                "rate": electricity_rate,
                "maint": hardware.monthly_maint_opex_usd,
                "months": MONTHS,
            },
            expression=(
                f"({hardware.tdp_watts}×{quantity}×730×{electricity_rate:g}/1000 "
                f"+ {hardware.monthly_maint_opex_usd:g}×{quantity}) × {MONTHS}"
            ),
            result=_usd(tco.energy_and_maint_3yr_usd),
            unit="USD",
            spec_section="5.3",
        ),
        CalcStep(
            step_id="capex_edge_total",
            label="CAPEX Edge total (3 ans)",
            formula="hardware_capex + energy_and_maint",
            inputs={
                "hardware_capex": _usd(tco.hardware_capex_usd),
                "energy_and_maint": _usd(tco.energy_and_maint_3yr_usd),
            },
            expression=f"{_usd(tco.hardware_capex_usd)} + {_usd(tco.energy_and_maint_3yr_usd)}",
            result=_usd(tco.capex_edge_total_usd),
            unit="USD",
            spec_section="5.3",
        ),
        CalcStep(
            step_id="cloud_volume",
            label="Volume mensuel de requêtes (cloud)",
            formula="techs × shifts × queries × days",
            inputs={
                "techs": technicians,
                "shifts": total_shifts,
                "queries": avg_queries,
                "days": DAYS_PER_MONTH,
            },
            expression=f"{technicians} × {total_shifts} × {avg_queries} × {DAYS_PER_MONTH}",
            result=_tokens(float(volume)),
            unit="requêtes",
            spec_section="5.3",
        ),
        CalcStep(
            step_id="opex_cloud_total",
            label="OPEX Cloud managé (3 ans)",
            formula="(token_cost_monthly + vector_host_monthly) × months",
            inputs={
                "tokens_in": TOKENS_IN,
                "price_in": PRICE_IN_PER_1M,
                "tokens_out": TOKENS_OUT,
                "price_out": PRICE_OUT_PER_1M,
                "vector_host": CLOUD_VECTOR_HOST_MONTHLY,
                "months": MONTHS,
            },
            expression=(
                f"(({TOKENS_IN}×{PRICE_IN_PER_1M:g} + {TOKENS_OUT}×{PRICE_OUT_PER_1M:g})/1e6"
                f" × {_tokens(float(volume))} + {CLOUD_VECTOR_HOST_MONTHLY}) × {MONTHS}"
            ),
            result=_usd(tco.opex_cloud_total_usd),
            unit="USD",
            spec_section="5.3",
        ),
        CalcStep(
            step_id="net_savings",
            label="Économies nettes (3 ans)",
            formula="opex_cloud − capex_edge",
            inputs={
                "opex": _usd(tco.opex_cloud_total_usd),
                "capex": _usd(tco.capex_edge_total_usd),
            },
            expression=f"{_usd(tco.opex_cloud_total_usd)} − {_usd(tco.capex_edge_total_usd)}",
            result=_usd(tco.net_savings_usd),
            unit="USD",
            spec_section="5.3",
        ),
        CalcStep(
            step_id="decision",
            label="Décision finale",
            formula="CAPEX_ON_PREM_EDGE si capex < opex, sinon OPEX_CLOUD_MANAGED",
            inputs={
                "capex": _usd(tco.capex_edge_total_usd),
                "opex": _usd(tco.opex_cloud_total_usd),
            },
            expression=(
                f"{_usd(tco.capex_edge_total_usd)} "
                f"{'<' if tco.capex_edge_total_usd < tco.opex_cloud_total_usd else '≥'} "
                f"{_usd(tco.opex_cloud_total_usd)}"
            ),
            result=tco.recommended_decision,
            unit="-",
            spec_section="5.3",
        ),
    ]
    return steps
