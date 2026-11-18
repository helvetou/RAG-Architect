"""
CMMI Level 3 Verification Suite — Zero-Hallucination Safety Gate.

Traceability:
- REQ-SAFE-001 -> TEST-SAFE-001 (a/b/c)

Methodology: Strict TDD (write and fail before implementing core/gate.py).
"""
from core.gate import SAFETY_BLOCK_MESSAGE, verify_response_safety


def test_req_safe_001_valid_grounded_response_passes() -> None:
    """TEST-SAFE-001a (REQ-SAFE-001): grounded citation + verified physical numbers passes."""
    parent_chunks = [
        "Manual HYD-01 Section 4.2 Page 14: Tighten main relief flange bolts to 85 Nm. "
        "Normal operating hydraulic pressure is 210 bar (max temperature 65 °C)."
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
        "Manual HYD-01 Section 4.2 Page 14: Tighten main relief flange bolts to 85 Nm."
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
    parent_chunks = ["Tighten main relief flange bolts to 85 Nm."]
    uncited_candidate = "You should tighten the main relief flange bolts to 85 Nm."
    result = verify_response_safety(
        candidate_response=uncited_candidate, parent_chunks=parent_chunks
    )
    assert result.is_safe is False
    assert result.citation_verified is False
    assert result.final_output == SAFETY_BLOCK_MESSAGE
