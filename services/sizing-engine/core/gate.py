"""Zero-hallucination safety gate (REQ-SAFE-001).

Blocks any response missing a grounded ``[Manual ID, Section, Page]`` citation,
citing a source absent from the retrieved chunks' metadata, or containing a
physical quantity absent from the retrieved parent chunks.
"""
import re
from dataclasses import dataclass

SAFETY_BLOCK_MESSAGE = (
    "SAFETY GATE BLOCK: Unverified numerical specification or missing citation "
    "detected. Consult physical manual directly."
)

_CITATION_PATTERN: re.Pattern[str] = re.compile(
    r"\[Manual\s+([A-Z0-9-]+),\s*Section\s+([0-9.]+)\s*,\s*Page\s+([0-9]+)\]"
)

_UNITS = (
    r"daNm|N·m|N\.m|Nm|kPa|MPa|bar|psi|Pa|kV|mA|Hz|°C|µm|mm|rpm|L/min|min|ppm|V|A|%"
)

_NUMERIC_PATTERN: re.Pattern[str] = re.compile(
    r"(?<!\d)(\d+(?:[.,]\d+)?(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?)\s*(" + _UNITS + r")"
)


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    manual_id: str | None = None
    section: str | None = None
    page: str | None = None


@dataclass(frozen=True)
class GateResult:
    is_safe: bool
    citation_verified: bool
    numeric_grounding_verified: bool
    final_output: str


def _citation_is_grounded(
    manual: str, section: str, page: str, chunks: list[RetrievedChunk]
) -> bool:
    return any(
        chunk.manual_id == manual and chunk.section == section and chunk.page == page
        for chunk in chunks
    )


def _normalize(value: str) -> str:
    return value.replace(",", ".")


def verify_response_safety(
    candidate_response: str, parent_chunks: list[RetrievedChunk]
) -> GateResult:
    citations = list(_CITATION_PATTERN.finditer(candidate_response))
    citation_verified = bool(citations) and all(
        _citation_is_grounded(match.group(1), match.group(2), match.group(3), parent_chunks)
        for match in citations
    )

    concatenated = _normalize(" ".join(chunk.text for chunk in parent_chunks))
    numeric_grounding_verified = True
    for match in _NUMERIC_PATTERN.finditer(candidate_response):
        value = _normalize(match.group(1))
        unit = match.group(2)
        value_pattern = re.escape(value).replace(r"\-", r"[-–]")
        grounding = re.compile(rf"(?<![\d.,]){value_pattern}\s*{re.escape(unit)}")
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
