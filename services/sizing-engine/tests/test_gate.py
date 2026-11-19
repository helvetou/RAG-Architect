"""
CMMI Level 3 Verification Suite — Zero-Hallucination Safety Gate.

Traceability:
- REQ-SAFE-001 -> TEST-SAFE-001 (a/b/c + d/e/f hardening)

Methodology: Strict TDD (write and fail before implementing core/gate.py).
"""
from core.gate import SAFETY_BLOCK_MESSAGE, RetrievedChunk, verify_response_safety


def test_req_safe_001_valid_grounded_response_passes() -> None:
    """TEST-SAFE-001a (REQ-SAFE-001): grounded citation + verified physical numbers passes."""
    parent_chunks = [
        RetrievedChunk(
            text=(
                "Manual HYD-01 Section 4.2 Page 14: Tighten main relief flange bolts to 85 Nm. "
                "Normal operating hydraulic pressure is 210 bar (max temperature 65 °C)."
            ),
            manual_id="HYD-01",
            section="4.2",
            page="14",
        )
    ]
    candidate = (
        "According to [Manual HYD-01, Section 4.2, Page 14], tighten the flange bolts "
        "to 85 Nm and verify operating pressure remains at 210 bar."
    )
    result = verify_response_safety(candidate_response=candidate, parent_chunks=parent_chunks)
    assert result.is_safe is True
    assert result.citation_verified is True
    assert result.numeric_grounding_verified is True
    assert result.final_output == candidate


def test_req_safe_001_hallucinated_torque_value_is_blocked() -> None:
    """TEST-SAFE-001b (REQ-SAFE-001): unverified 120 Nm (vs grounded 85 Nm) is blocked."""
    parent_chunks = [
        RetrievedChunk(
            text="Manual HYD-01 Section 4.2 Page 14: Tighten main relief flange bolts to 85 Nm.",
            manual_id="HYD-01",
            section="4.2",
            page="14",
        )
    ]
    hallucinated_candidate = (
        "According to [Manual HYD-01, Section 4.2, Page 14], tighten the flange bolts to 120 Nm."
    )
    result = verify_response_safety(
        candidate_response=hallucinated_candidate, parent_chunks=parent_chunks
    )
    assert result.is_safe is False
    assert result.numeric_grounding_verified is False
    assert result.final_output == SAFETY_BLOCK_MESSAGE


def test_req_safe_001_missing_citation_is_blocked() -> None:
    """TEST-SAFE-001c (REQ-SAFE-001): accurate numbers but no bracketed citation is blocked."""
    parent_chunks = [RetrievedChunk(text="Tighten main relief flange bolts to 85 Nm.")]
    uncited_candidate = "You should tighten the main relief flange bolts to 85 Nm."
    result = verify_response_safety(
        candidate_response=uncited_candidate, parent_chunks=parent_chunks
    )
    assert result.is_safe is False
    assert result.citation_verified is False
    assert result.final_output == SAFETY_BLOCK_MESSAGE


def test_req_safe_001d_citation_spoofing_blocked() -> None:
    """TEST-SAFE-001d (AUD-03): citation not present in retrieved metadata is blocked."""
    parent_chunks = [
        RetrievedChunk(
            text="Tighten bolts to 85 Nm.",
            manual_id="HYD-02",
            section="3.1",
            page="7",
        )
    ]
    spoofed_candidate = (
        "According to [Manual HYD-01, Section 4.2, Page 14], tighten the bolts to 85 Nm."
    )
    result = verify_response_safety(
        candidate_response=spoofed_candidate, parent_chunks=parent_chunks
    )
    assert result.citation_verified is False
    assert result.is_safe is False
    assert result.final_output == SAFETY_BLOCK_MESSAGE


def test_req_safe_001e_comma_decimal_and_optional_space() -> None:
    """TEST-SAFE-001e (AUD-03): comma decimals and optional spaces are grounded."""
    parent_chunks = [
        RetrievedChunk(
            text="Set relief valve to 12,5 bar. Coolant limit 120 °C.",
            manual_id="HYD-01",
            section="5",
            page="2",
        )
    ]
    candidate = (
        "According to [Manual HYD-01, Section 5, Page 2], set relief valve to 12,5 bar "
        "and coolant limit 120°C."
    )
    result = verify_response_safety(candidate_response=candidate, parent_chunks=parent_chunks)
    assert result.numeric_grounding_verified is True
    assert result.is_safe is True


def test_req_safe_001f_ranges_and_extended_units() -> None:
    """TEST-SAFE-001f (AUD-03): ranges and extended GMP units are grounded."""
    parent_chunks = [
        RetrievedChunk(
            text="Torque 10-15 Nm. Flow 5 L/min. Residual 3 ppm. Speed 1400 rpm.",
            manual_id="HYD-01",
            section="6",
            page="3",
        )
    ]
    candidate = (
        "According to [Manual HYD-01, Section 6, Page 3], torque 10-15 Nm, "
        "flow 5 L/min, residual 3 ppm, speed 1400 rpm."
    )
    result = verify_response_safety(candidate_response=candidate, parent_chunks=parent_chunks)
    assert result.numeric_grounding_verified is True
    assert result.is_safe is True
