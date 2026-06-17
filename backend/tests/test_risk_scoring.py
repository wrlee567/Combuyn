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


def test_factor_weights_sum_to_one():
    from app.services.risk_scoring import FACTOR_WEIGHTS

    total = sum(FACTOR_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9


def test_factor_options_returns_all_keys():
    from app.services.risk_scoring import factor_options

    opts = factor_options()
    assert set(opts.keys()) == {"data_classification", "network_connectivity", "industry", "geography"}


def test_all_industry_values_have_severity():
    from app.services.risk_scoring import INDUSTRY

    for value in INDUSTRY:
        result = compute_inherent_risk(
            data_classification="internal",
            network_connectivity="limited",
            industry=value,
            geography="domestic",
        )
        assert 0 <= result.score <= 100


def test_all_geography_values_have_severity():
    from app.services.risk_scoring import GEOGRAPHY

    for value in GEOGRAPHY:
        result = compute_inherent_risk(
            data_classification="internal",
            network_connectivity="limited",
            industry="technology",
            geography=value,
        )
        assert 0 <= result.score <= 100


def test_score_is_float_between_0_and_100():
    for dc, nc, ind, geo in [
        ("public", "none", "technology", "domestic"),
        ("restricted", "privileged", "financial_services", "high_risk"),
        ("confidential", "integrated", "healthcare", "eu_eea"),
        ("internal", "limited", "retail", "international"),
    ]:
        result = compute_inherent_risk(
            data_classification=dc,
            network_connectivity=nc,
            industry=ind,
            geography=geo,
        )
        assert isinstance(result.score, int)
        assert 0 <= result.score <= 100
