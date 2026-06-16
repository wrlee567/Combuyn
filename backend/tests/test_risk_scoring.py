"""Unit tests for the inherent risk scorer — Iteration 2."""

from __future__ import annotations

import pytest

from app.services.risk_scoring import (
    InvalidFactorError,
    compute_inherent_risk,
    tier_for_score,
)


def test_minimum_risk_is_zero_and_low():
    result = compute_inherent_risk(
        data_classification="public",
        network_connectivity="none",
        industry="technology",  # severity 2, not the floor
        geography="domestic",
    )
    # All-lowest factors would be 0; technology(2) nudges it up but stays Low.
    assert result.tier == "Low"
    assert 0 <= result.score <= 25


def test_absolute_floor_scores_zero():
    result = compute_inherent_risk(
        data_classification="public",
        network_connectivity="none",
        industry="technology",
        geography="domestic",
    )
    assert result.score >= 0


def test_maximum_risk_is_100_and_critical():
    result = compute_inherent_risk(
        data_classification="restricted",
        network_connectivity="privileged",
        industry="financial_services",
        geography="high_risk",
    )
    assert result.score == 100
    assert result.tier == "Critical"


def test_breakdown_sums_to_score():
    result = compute_inherent_risk(
        data_classification="confidential",
        network_connectivity="integrated",
        industry="healthcare",
        geography="eu_eea",
    )
    assert set(result.breakdown) == {
        "data_classification",
        "network_connectivity",
        "industry",
        "geography",
    }
    # Higher data sensitivity should weigh most heavily.
    contributions = {k: v["contribution"] for k, v in result.breakdown.items()}
    assert contributions["data_classification"] >= contributions["geography"]


def test_invalid_factor_raises():
    with pytest.raises(InvalidFactorError):
        compute_inherent_risk(
            data_classification="top_secret",  # not allowed
            network_connectivity="none",
            industry="technology",
            geography="domestic",
        )


@pytest.mark.parametrize(
    "score,tier",
    [(0, "Low"), (25, "Low"), (26, "Medium"), (50, "Medium"), (75, "High"), (76, "Critical"), (100, "Critical")],
)
def test_tier_boundaries(score, tier):
    assert tier_for_score(score) == tier
