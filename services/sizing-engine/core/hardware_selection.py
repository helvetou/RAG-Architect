"""Catalog-driven hardware selection (REQ-MATH-003, REQ-FIN-001).

Picks the cost-optimal inference hardware for a given VRAM requirement,
deployment constraint and high-availability requirement, from a deterministic
catalog aligned with packages/db/src/seed.ts (REQ-DB-001).
"""
from dataclasses import dataclass

from core.calculator import (
    HOURS_PER_MONTH,
    MONTHS,
    HardwareSpec,
    compute_quantity,
)

EDGE_TIERS = frozenset({"EDGE_RUGGED_SERVER", "EDGE_GATEWAY"})
CLOUD_TIERS = frozenset({"CLOUD_HOSTED_GPU"})

# Deterministic hardware catalog, aligned with packages/db/src/seed.ts.
CATALOG: list[HardwareSpec] = [
    HardwareSpec(
        hardware_id="rugged-edge-l4-24g",
        name="Industrial Rugged Server NVIDIA L4 (24GB)",
        vram_gb=24.0,
        system_ram_gb=128.0,
        tdp_watts=300,
        unit_cost_capex_usd=8210.0,
        monthly_maint_opex_usd=100.0,
        tier="EDGE_RUGGED_SERVER",
    ),
    HardwareSpec(
        hardware_id="rugged-dual-a4500-40g",
        name="Industrial Rugged Server Dual NVIDIA A4500 (40GB)",
        vram_gb=40.0,
        system_ram_gb=128.0,
        tdp_watts=400,
        unit_cost_capex_usd=12990.0,
        monthly_maint_opex_usd=140.0,
        tier="EDGE_RUGGED_SERVER",
    ),
    HardwareSpec(
        hardware_id="nvidia-l40s",
        name="NVIDIA L40S Cloud GPU (48GB)",
        vram_gb=48.0,
        system_ram_gb=192.0,
        tdp_watts=350,
        unit_cost_capex_usd=0.0,
        monthly_maint_opex_usd=1490.0,
        tier="CLOUD_HOSTED_GPU",
    ),
    HardwareSpec(
        hardware_id="edgestream-gw-01",
        name="EdgeStream Industrial Gateway 01",
        vram_gb=0.0,
        system_ram_gb=8.0,
        tdp_watts=15,
        unit_cost_capex_usd=890.0,
        monthly_maint_opex_usd=12.0,
        tier="EDGE_GATEWAY",
    ),
]


@dataclass(frozen=True)
class HardwareCandidate:
    hardware: HardwareSpec
    quantity: int
    capex_edge_total_usd: float


def _allowed_tiers(deployment_constraint: str) -> frozenset[str]:
    """Map a deployment constraint to the hardware tiers it may use."""
    if deployment_constraint == "FULL_CLOUD":
        return CLOUD_TIERS
    return EDGE_TIERS


def _edge_3yr_cost(
    hardware: HardwareSpec,
    total_vram: float,
    safety_critical: bool,
    electricity_rate: float,
) -> tuple[float, int]:
    """36-month edge CAPEX + energy/maintenance for a candidate hardware."""
    quantity = compute_quantity(total_vram, hardware, safety_critical)
    capex = hardware.unit_cost_capex_usd * quantity
    energy_monthly = hardware.tdp_watts * quantity * HOURS_PER_MONTH * electricity_rate / 1000
    maintenance_monthly = hardware.monthly_maint_opex_usd * quantity
    return capex + (energy_monthly + maintenance_monthly) * MONTHS, quantity


def evaluate_candidates(
    catalog: list[HardwareSpec],
    total_vram: float,
    deployment_constraint: str,
    safety_critical: bool,
    electricity_rate: float,
) -> list[HardwareCandidate]:
    """Score every admissible hardware candidate by 3-year edge cost."""
    tiers = _allowed_tiers(deployment_constraint)
    pool = [h for h in catalog if h.tier in tiers and h.vram_gb > 0]
    fitting = [h for h in pool if h.vram_gb >= total_vram]
    candidates = fitting if fitting else ([max(pool, key=lambda h: h.vram_gb)] if pool else [])

    scored: list[HardwareCandidate] = []
    for hardware in candidates:
        cost, quantity = _edge_3yr_cost(hardware, total_vram, safety_critical, electricity_rate)
        scored.append(HardwareCandidate(hardware, quantity, cost))
    return sorted(scored, key=lambda c: c.capex_edge_total_usd)


def select_hardware(
    catalog: list[HardwareSpec],
    total_vram: float,
    deployment_constraint: str,
    safety_critical: bool,
    electricity_rate: float,
) -> tuple[HardwareSpec, int]:
    """Select the lowest-3-year-edge-cost hardware that satisfies the requirement."""
    candidates = evaluate_candidates(
        catalog, total_vram, deployment_constraint, safety_critical, electricity_rate
    )
    if not candidates:
        raise ValueError(
            f"No hardware available for deployment constraint {deployment_constraint!r}"
        )
    best = candidates[0]
    return best.hardware, best.quantity
