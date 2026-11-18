"""Closed-loop auto-calibration rules (REQ-CAL-001, REQ-CAL-002).

Implements the three feedback loops from spec section 7.4:
- Loop 1: +0.20 compute scaling when P95 TTFT > 1500 ms or peak VRAM > 90%.
- Loop 2: -20% child chunk size when context recall < 0.75 or P50 reranker < 0.60.
- Loop 3: enable the semantic router when cloud token spend exceeds baseline +15%.
"""
from dataclasses import dataclass

P95_TTFT_THRESHOLD_MS = 1500.0
PEAK_VRAM_RATIO = 0.90
SCALING_INCREMENT = 0.20
CONTEXT_RECALL_THRESHOLD = 0.75
RERANKER_SCORE_THRESHOLD = 0.60
CHUNK_REDUCTION_FACTOR = 0.80
TOKEN_OVERRUN_RATIO = 0.15


@dataclass(frozen=True)
class RollingTelemetryMetrics:
    model_id: str
    hardware_id: str
    hardware_vram_gb: float
    measured_p95_ttft_ms: float
    measured_peak_vram_gb: float
    measured_context_recall: float
    current_scaling_multiplier: float
    current_child_chunk_tokens: int
    monthly_token_overrun_ratio: float
    measured_p50_reranker_score: float | None = None


@dataclass(frozen=True)
class CalibrationDecision:
    loop1_triggered: bool
    updated_scaling_multiplier: float
    loop2_triggered: bool
    recommended_child_chunk_tokens: int
    loop3_triggered: bool
    enable_semantic_router: bool


def evaluate_calibration_loops(metrics: RollingTelemetryMetrics) -> CalibrationDecision:
    loop1_triggered = (
        metrics.measured_p95_ttft_ms > P95_TTFT_THRESHOLD_MS
        or metrics.measured_peak_vram_gb > PEAK_VRAM_RATIO * metrics.hardware_vram_gb
    )
    updated_scaling_multiplier = (
        metrics.current_scaling_multiplier + SCALING_INCREMENT
        if loop1_triggered
        else metrics.current_scaling_multiplier
    )

    loop2_triggered = metrics.measured_context_recall < CONTEXT_RECALL_THRESHOLD or (
        metrics.measured_p50_reranker_score is not None
        and metrics.measured_p50_reranker_score < RERANKER_SCORE_THRESHOLD
    )
    recommended_child_chunk_tokens = (
        int(metrics.current_child_chunk_tokens * CHUNK_REDUCTION_FACTOR)
        if loop2_triggered
        else metrics.current_child_chunk_tokens
    )

    loop3_triggered = metrics.monthly_token_overrun_ratio > TOKEN_OVERRUN_RATIO

    return CalibrationDecision(
        loop1_triggered=loop1_triggered,
        updated_scaling_multiplier=updated_scaling_multiplier,
        loop2_triggered=loop2_triggered,
        recommended_child_chunk_tokens=recommended_child_chunk_tokens,
        loop3_triggered=loop3_triggered,
        enable_semantic_router=loop3_triggered,
    )
