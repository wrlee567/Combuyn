"""Inherent risk scoring — Iteration 2.

Inherent risk is a vendor's calculated risk *before* any controls are applied.
We derive it from four factors the TPRM blueprint calls out: the data the vendor
processes, how deeply they connect to our network, their industry, and their
geography (data-residency exposure).

The scorer is a pure function so it is trivially testable and deterministic. It
returns a 0-100 score, a tier, and a per-factor breakdown the UI can show.
"""

from __future__ import annotations

from dataclasses import dataclass

# Each factor contributes a 1-4 severity. Severities are combined with the
# weights below, then normalized to 0-100. Weights sum to 1.0.
FACTOR_WEIGHTS = {
    "data_classification": 0.35,
    "network_connectivity": 0.30,
    "industry": 0.20,
    "geography": 0.15,
}

# Allowed values mapped to a 1 (low) - 4 (high) severity.
DATA_CLASSIFICATION = {
    "public": 1,
    "internal": 2,
    "confidential": 3,
    "restricted": 4,
}

NETWORK_CONNECTIVITY = {
    "none": 1,        # no direct connection
    "limited": 2,     # scoped API / SaaS
    "integrated": 3,  # systems integration
    "privileged": 4,  # privileged / admin access to our environment
}

# Industries carry different baseline data-sensitivity / regulatory exposure.
INDUSTRY = {
    "technology": 2,
    "manufacturing": 2,
    "retail": 2,
    "professional_services": 2,
    "financial_services": 4,
    "healthcare": 4,
    "government": 4,
    "medical_devices": 4,
    "other": 3,
}

# Geography reflects data-residency / cross-border transfer exposure.
GEOGRAPHY = {
    "domestic": 1,
    "eu_eea": 2,
    "international": 3,
    "high_risk": 4,
}

# Score thresholds → tier. Upper-bound inclusive.
TIERS = [
    (25, "Low"),
    (50, "Medium"),
    (75, "High"),
    (100, "Critical"),
]


@dataclass
class RiskResult:
    score: int  # 0-100
    tier: str
    breakdown: dict[str, dict]  # factor -> {value, severity, weight, contribution}


class InvalidFactorError(ValueError):
    """Raised when a factor value is outside its allowed set."""


def _severity(name: str, lookup: dict[str, int], value: str) -> int:
    try:
        return lookup[value]
    except KeyError as exc:
        allowed = ", ".join(sorted(lookup))
        raise InvalidFactorError(
            f"Invalid {name} '{value}'. Allowed: {allowed}."
        ) from exc


def tier_for_score(score: int) -> str:
    for upper, tier in TIERS:
        if score <= upper:
            return tier
    return TIERS[-1][1]


def compute_inherent_risk(
    *,
    data_classification: str,
    network_connectivity: str,
    industry: str,
    geography: str,
) -> RiskResult:
    """Compute a vendor's inherent risk score, tier, and factor breakdown."""
    factors = {
        "data_classification": (DATA_CLASSIFICATION, data_classification),
        "network_connectivity": (NETWORK_CONNECTIVITY, network_connectivity),
        "industry": (INDUSTRY, industry),
        "geography": (GEOGRAPHY, geography),
    }

    breakdown: dict[str, dict] = {}
    weighted_severity = 0.0
    for name, (lookup, value) in factors.items():
        severity = _severity(name, lookup, value)
        weight = FACTOR_WEIGHTS[name]
        contribution = severity * weight
        weighted_severity += contribution
        breakdown[name] = {
            "value": value,
            "severity": severity,
            "weight": weight,
            "contribution": round(contribution, 4),
        }

    # weighted_severity ranges 1..4; normalize to 0..100.
    score = round((weighted_severity - 1) / 3 * 100)
    score = max(0, min(100, score))
    return RiskResult(score=score, tier=tier_for_score(score), breakdown=breakdown)


def factor_options() -> dict[str, list[str]]:
    """Allowed values for each factor — used to drive the intake form UI."""
    return {
        "data_classification": list(DATA_CLASSIFICATION),
        "network_connectivity": list(NETWORK_CONNECTIVITY),
        "industry": list(INDUSTRY),
        "geography": list(GEOGRAPHY),
    }
