"""Workflow blueprints + sample instances — Iteration 3.

Two realistic GRC blueprints so the orchestration engine, the React Flow-style
graph, and the Saga rollback are all immediately demonstrable. Sample instances
are advanced through their blueprints at seed time (via the real engine), so
their state, event log, and available actions reflect the live rules.
"""

from __future__ import annotations

WORKFLOW_DEFINITIONS: list[dict] = [
    {
        "key": "vendor_onboarding",
        "name": "Vendor Onboarding Approval",
        "description": (
            "Gates a new third party through security, risk, and legal review "
            "before approval. Any reviewer can reject; an in-flight onboarding "
            "can be rolled back via Saga compensation."
        ),
        "blueprint": {
            "initial": "intake",
            "states": [
                {"id": "intake", "label": "Intake", "type": "start"},
                {"id": "security_review", "label": "Security Review"},
                {"id": "risk_assessment", "label": "Risk Assessment"},
                {"id": "legal_review", "label": "Legal & DPA Review"},
                {"id": "approved", "label": "Approved", "type": "end"},
                {"id": "rejected", "label": "Rejected", "type": "end"},
            ],
            "transitions": [
                {
                    "action": "submit",
                    "from": "intake",
                    "to": "security_review",
                    "compensation": "Re-open the intake form",
                },
                {
                    "action": "pass_security",
                    "from": "security_review",
                    "to": "risk_assessment",
                    "compensation": "Revoke security sign-off",
                },
                {
                    "action": "accept_risk",
                    "from": "risk_assessment",
                    "to": "legal_review",
                    "compensation": "Re-open risk assessment",
                },
                {
                    "action": "approve",
                    "from": "legal_review",
                    "to": "approved",
                },
                {"action": "reject", "from": "security_review", "to": "rejected"},
                {"action": "reject", "from": "risk_assessment", "to": "rejected"},
                {"action": "reject", "from": "legal_review", "to": "rejected"},
            ],
        },
    },
    {
        "key": "access_request",
        "name": "Privileged Access Request",
        "description": (
            "Provisions privileged access after manager and security approval, "
            "then schedules an access review. Denials are terminal."
        ),
        "blueprint": {
            "initial": "requested",
            "states": [
                {"id": "requested", "label": "Requested", "type": "start"},
                {"id": "manager_approval", "label": "Manager Approval"},
                {"id": "security_approval", "label": "Security Approval"},
                {"id": "provisioned", "label": "Provisioned"},
                {"id": "review_scheduled", "label": "Review Scheduled", "type": "end"},
                {"id": "denied", "label": "Denied", "type": "end"},
            ],
            "transitions": [
                {
                    "action": "manager_approve",
                    "from": "requested",
                    "to": "manager_approval",
                    "compensation": "Withdraw manager approval",
                },
                {
                    "action": "security_approve",
                    "from": "manager_approval",
                    "to": "security_approval",
                    "compensation": "Withdraw security approval",
                },
                {
                    "action": "provision",
                    "from": "security_approval",
                    "to": "provisioned",
                    "compensation": "De-provision the granted access",
                },
                {
                    "action": "schedule_review",
                    "from": "provisioned",
                    "to": "review_scheduled",
                },
                {"action": "deny", "from": "requested", "to": "denied"},
                {"action": "deny", "from": "manager_approval", "to": "denied"},
                {"action": "deny", "from": "security_approval", "to": "denied"},
            ],
        },
    },
]

# Each sample instance is driven through these actions at seed time.
SAMPLE_INSTANCES: list[dict] = [
    {
        "definition_key": "vendor_onboarding",
        "subject": "Northwind Payments onboarding",
        "context": {"vendor": "Northwind Payments", "tier": "Critical"},
        "actions": ["submit", "pass_security"],
    },
    {
        "definition_key": "vendor_onboarding",
        "subject": "Cedar Analytics onboarding",
        "context": {"vendor": "Cedar Analytics", "tier": "High"},
        "actions": ["submit", "pass_security", "accept_risk", "approve"],
    },
    {
        "definition_key": "access_request",
        "subject": "Prod DB admin for S. Okafor",
        "context": {"system": "prod-db", "requestor": "S. Okafor"},
        "actions": ["manager_approve", "security_approve"],
    },
]
