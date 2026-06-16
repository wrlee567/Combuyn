"""Sample vendors — Iteration 2.

A small, realistic set spanning the risk spectrum so the TPRM list and risk
tiers are immediately demonstrable. Inherent risk is computed at seed time from
the factors below (not hard-coded), so it always reflects the live scoring rules.
"""

from __future__ import annotations

SAMPLE_VENDORS: list[dict] = [
    {
        "name": "Northwind Payments",
        "contact_name": "Dana Ruiz",
        "contact_email": "security@northwindpay.example",
        "description": "Payment processing and card tokenization provider.",
        "industry": "financial_services",
        "data_classification": "restricted",
        "network_connectivity": "privileged",
        "geography": "international",
        "lifecycle_status": "assessment",
        "questionnaire_responses": {
            "mfa_enforced": True,
            "encryption_at_rest": True,
            "soc2_report": True,
        },
    },
    {
        "name": "Cedar Analytics",
        "contact_name": "Sam Okafor",
        "contact_email": "trust@cedaranalytics.example",
        "description": "Marketing analytics SaaS processing customer datasets.",
        "industry": "technology",
        "data_classification": "confidential",
        "network_connectivity": "integrated",
        "geography": "eu_eea",
        "lifecycle_status": "monitoring",
        "questionnaire_responses": {"mfa_enforced": True, "soc2_report": False},
    },
    {
        "name": "Brightline Health Systems",
        "contact_name": "Priya Nair",
        "contact_email": "compliance@brightlinehealth.example",
        "description": "Clinical data platform integrating with patient records.",
        "industry": "healthcare",
        "data_classification": "restricted",
        "network_connectivity": "integrated",
        "geography": "domestic",
        "lifecycle_status": "onboarding",
        "questionnaire_responses": {},
    },
    {
        "name": "Office Supplies Direct",
        "contact_name": "Lee Carter",
        "contact_email": "accounts@officesuppliesdirect.example",
        "description": "Office consumables vendor, no system access.",
        "industry": "retail",
        "data_classification": "public",
        "network_connectivity": "none",
        "geography": "domestic",
        "lifecycle_status": "management",
        "questionnaire_responses": {},
    },
]
