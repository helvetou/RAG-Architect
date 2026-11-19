"""
CMMI Level 3 Verification Suite — Closed-Loop Telemetry Calibration.

Traceability:
- REQ-CAL-001 -> TEST-CAL-001 (hardware scaling loop)
- REQ-CAL-002 -> TEST-CAL-002 (chunk reduction + semantic router loops)

Methodology: Strict TDD (write and fail before implementing core/calibration.py).
"""
import gzip
import json

import pytest

from core.calibration import (
    RollingTelemetryMetrics,
    evaluate_calibration_loops,
    parse_jsonl_gz,
    should_sample_for_eval,
)


def test_req_cal_001_loop1_hardware_scaling_trigger() -> None:
    """TEST-CAL-001 (REQ-CAL-001): +0.20 M_calib when P95 TTFT > 1500 ms."""
    metrics = RollingTelemetryMetrics(
        model_id="llama-3.2-3b-instruct-q4",
        hardware_id="rugged-edge-l4-24g",
        hardware_vram_gb=24.0,
        measured_p95_ttft_ms=1680.0,  # Exceeds 1500 ms threshold
        measured_peak_vram_gb=18.5,
        measured_context_recall=0.84,
        current_scaling_multiplier=1.0,
        current_child_chunk_tokens=200,
        monthly_token_overrun_ratio=0.05,
    )
    decision = evaluate_calibration_loops(metrics)
    assert decision.loop1_triggered is True
    assert decision.updated_scaling_multiplier == pytest.approx(1.20)


def test_req_cal_002_loop2_and_loop3_triggers() -> None:
    """TEST-CAL-002 (REQ-CAL-002): -20% chunk size + Semantic Router triggers."""
    metrics = RollingTelemetryMetrics(
        model_id="llama-3.2-3b-instruct-q4",
        hardware_id="rugged-edge-l4-24g",
        hardware_vram_gb=24.0,
        measured_p95_ttft_ms=1120.0,
        measured_peak_vram_gb=14.0,
        measured_context_recall=0.68,  # Below 0.75 threshold
        current_scaling_multiplier=1.0,
        current_child_chunk_tokens=200,
        monthly_token_overrun_ratio=0.22,  # Exceeds 0.15 threshold
    )
    decision = evaluate_calibration_loops(metrics)
    assert decision.loop2_triggered is True
    assert decision.recommended_child_chunk_tokens == 160
    assert decision.loop3_triggered is True
    assert decision.enable_semantic_router is True


def test_cal_loop1_vram_trigger() -> None:
    """Loop 1 triggers on peak VRAM > 90% of hardware even when TTFT is fine."""
    metrics = RollingTelemetryMetrics(
        model_id="llama-3.2-3b-instruct-q4",
        hardware_id="rugged-edge-l4-24g",
        hardware_vram_gb=24.0,
        measured_p95_ttft_ms=1000.0,
        measured_peak_vram_gb=22.0,  # > 21.6 GB (90% of 24 GB)
        measured_context_recall=0.80,
        current_scaling_multiplier=1.0,
        current_child_chunk_tokens=200,
        monthly_token_overrun_ratio=0.10,
    )
    decision = evaluate_calibration_loops(metrics)
    assert decision.loop1_triggered is True
    assert decision.updated_scaling_multiplier == pytest.approx(1.20)
    assert decision.loop2_triggered is False
    assert decision.loop3_triggered is False


def test_cal_loop2_reranker_trigger() -> None:
    """Loop 2 triggers on P50 reranker < 0.60 even when context recall is fine."""
    metrics = RollingTelemetryMetrics(
        model_id="llama-3.2-3b-instruct-q4",
        hardware_id="rugged-edge-l4-24g",
        hardware_vram_gb=24.0,
        measured_p95_ttft_ms=1000.0,
        measured_peak_vram_gb=10.0,
        measured_context_recall=0.80,
        current_scaling_multiplier=1.0,
        current_child_chunk_tokens=200,
        monthly_token_overrun_ratio=0.10,
        measured_p50_reranker_score=0.50,  # Below 0.60 threshold
    )
    decision = evaluate_calibration_loops(metrics)
    assert decision.loop2_triggered is True
    assert decision.recommended_child_chunk_tokens == 160


def test_cal_no_loops_triggered() -> None:
    """No loop triggers when all metrics are healthy (incl. reranker >= 0.60)."""
    metrics = RollingTelemetryMetrics(
        model_id="llama-3.2-3b-instruct-q4",
        hardware_id="rugged-edge-l4-24g",
        hardware_vram_gb=24.0,
        measured_p95_ttft_ms=1000.0,
        measured_peak_vram_gb=10.0,
        measured_context_recall=0.80,
        current_scaling_multiplier=1.0,
        current_child_chunk_tokens=200,
        monthly_token_overrun_ratio=0.10,
        measured_p50_reranker_score=0.70,
    )
    decision = evaluate_calibration_loops(metrics)
    assert decision.loop1_triggered is False
    assert decision.loop2_triggered is False
    assert decision.loop3_triggered is False
    assert decision.updated_scaling_multiplier == pytest.approx(1.0)
    assert decision.recommended_child_chunk_tokens == 200
    assert decision.enable_semantic_router is False


def test_cal_sample_rate_boundaries_and_determinism() -> None:
    """REQ-CAL-002: async RAGAS sampling is deterministic and rate-controlled."""
    assert should_sample_for_eval("key", sample_rate=1.0) is True
    assert should_sample_for_eval("key", sample_rate=0.0) is False
    assert should_sample_for_eval("key", sample_rate=0.05) == should_sample_for_eval(
        "key", sample_rate=0.05
    )


def test_cal_parse_jsonl_gz_batch() -> None:
    """REQ-CAL-002: air-gapped .jsonl.gz batch parses into telemetry records."""
    records = [
        {"client_id": "a", "timestamp": "t1"},
        {"client_id": "b", "timestamp": "t2"},
    ]
    payload = gzip.compress(("\n".join(json.dumps(r) for r in records) + "\n").encode())
    assert parse_jsonl_gz(payload) == records
