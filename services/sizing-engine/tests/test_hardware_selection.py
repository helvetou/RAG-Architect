"""CMMI Level 3 Verification Suite — Catalog-driven hardware selection.

Traceability:
- REQ-MATH-003 -> hardware capacity selection
- REQ-FIN-001  -> TCO-minimal hardware choice

Methodology: Strict TDD (write and fail before implementing core/hardware_selection.py).
"""
import pytest

from core.hardware_selection import CATALOG, select_hardware


def test_select_hardware_raises_when_no_candidate() -> None:
    """Empty catalog raises ValueError (no hardware satisfies the constraint)."""
    with pytest.raises(ValueError):
        select_hardware(
            catalog=[],
            total_vram=10.96,
            deployment_constraint="AIR_GAPPED_EDGE",
            safety_critical=True,
            electricity_rate=0.18,
        )


def test_select_edge_reference_vector() -> None:
    """AIR_GAPPED_EDGE + 10.96 GB + safety -> L4 x2 (reference vector preserved)."""
    hardware, quantity = select_hardware(
        catalog=CATALOG,
        total_vram=10.96,
        deployment_constraint="AIR_GAPPED_EDGE",
        safety_critical=True,
        electricity_rate=0.18,
    )
    assert hardware.hardware_id == "rugged-edge-l4-24g"
    assert quantity == 2


def test_select_full_cloud() -> None:
    """FULL_CLOUD selects the cloud-hosted GPU (L40S)."""
    hardware, quantity = select_hardware(
        catalog=CATALOG,
        total_vram=10.96,
        deployment_constraint="FULL_CLOUD",
        safety_critical=True,
        electricity_rate=0.18,
    )
    assert hardware.hardware_id == "nvidia-l40s"


def test_select_larger_vram_picks_a4500() -> None:
    """45 GB exceeds L4 (24GB) -> dual-A4500 40GB selected with 2 units."""
    hardware, quantity = select_hardware(
        catalog=CATALOG,
        total_vram=45.0,
        deployment_constraint="AIR_GAPPED_EDGE",
        safety_critical=True,
        electricity_rate=0.18,
    )
    assert hardware.hardware_id == "rugged-dual-a4500-40g"
    assert quantity == 2


def test_safety_off_drops_quantity_to_one() -> None:
    """safety_critical=False -> single unit (CAPEX halves)."""
    hardware, quantity = select_hardware(
        catalog=CATALOG,
        total_vram=10.96,
        deployment_constraint="AIR_GAPPED_EDGE",
        safety_critical=False,
        electricity_rate=0.18,
    )
    assert hardware.hardware_id == "rugged-edge-l4-24g"
    assert quantity == 1
