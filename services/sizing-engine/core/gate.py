"""Zero-hallucination safety gate (REQ-SAFE-001).

Blocks any response missing an explicit ``[Manual ID, Section, Page]`` citation
or containing a physical quantity absent from the retrieved parent chunks.
"""
import re
from dataclasses import dataclass

SAFETY_BLOCK_MESSAGE = (
    "SAFETY GATE BLOCK: Unverified numerical specification or missing citation "
    "detected. Consult physical manual directly."
)

_CITATION_PATTERN: re.Pattern[str] = re.compile(
    r"\[Manual [A-Z0-9-]+,\s*Section [0-9.]+\s*,\s*Page [0-9]+\]"
)
_NUMERIC_PATTERN: re.Pattern[str] = re.compile(
    r"(\d+(?:\.\d+)?)\s*(Nm|N·m|bar|psi|kPa|MPa|V|kV|A|mA|Hz|°C|mm)\b"
)


@dataclass(frozen=True)
class GateResult:
    is_safe: bool
    citation_verified: bool
    numeric_grounding_verified: bool
    final_output: str


def verify_response_safety(candidate_response: str, parent_chunks: list[str]) -> GateResult:
    citation_verified = _CITATION_PATTERN.search(candidate_response) is not None

    concatenated = " ".join(parent_chunks)
    numeric_grounding_verified = True
    for match in _NUMERIC_PATTERN.finditer(candidate_response):
        value = match.group(1)
        unit = match.group(2)
        grounding = re.compile(rf"\b{re.escape(value)}\s*{re.escape(unit)}\b")
        if grounding.search(concatenated) is None:
            numeric_grounding_verified = False
            break

    is_safe = citation_verified and numeric_grounding_verified
    final_output = candidate_response if is_safe else SAFETY_BLOCK_MESSAGE
    return GateResult(
        is_safe=is_safe,
        citation_verified=citation_verified,
        numeric_grounding_verified=numeric_grounding_verified,
        final_output=final_output,
    )
