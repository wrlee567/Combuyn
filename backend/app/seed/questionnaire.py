"""Vendor security questionnaire template — Iteration 2.

A static template defines the questions; each vendor's *answers* are stored as a
JSONB dict keyed by question id. Keeping answers in JSONB means we can revise the
questionnaire without a schema migration. Questions are grouped into sections for
the UI, and each maps loosely to a CCF domain so later iterations can drive
control coverage from responses.
"""

from __future__ import annotations

QUESTIONNAIRE_VERSION = "1.0"

# type: "boolean" | "single_select" | "text"
QUESTIONNAIRE_TEMPLATE: list[dict] = [
    {
        "section": "Access Control",
        "ccf_domain": "Identification & Authentication",
        "questions": [
            {
                "id": "mfa_enforced",
                "text": "Is multi-factor authentication enforced for all administrative access?",
                "type": "boolean",
            },
            {
                "id": "access_reviews",
                "text": "How often are user access rights reviewed?",
                "type": "single_select",
                "options": ["never", "annually", "quarterly", "monthly"],
            },
        ],
    },
    {
        "section": "Data Protection",
        "ccf_domain": "Cryptographic Protections",
        "questions": [
            {
                "id": "encryption_at_rest",
                "text": "Is customer data encrypted at rest?",
                "type": "boolean",
            },
            {
                "id": "encryption_in_transit",
                "text": "Is data encrypted in transit using TLS 1.2 or higher?",
                "type": "boolean",
            },
        ],
    },
    {
        "section": "Security Program",
        "ccf_domain": "Continuous Monitoring",
        "questions": [
            {
                "id": "soc2_report",
                "text": "Do you hold a current SOC 2 Type II report?",
                "type": "boolean",
            },
            {
                "id": "incident_response",
                "text": "Do you have a documented incident response plan?",
                "type": "boolean",
            },
            {
                "id": "pentest_frequency",
                "text": "How frequently do you conduct third-party penetration tests?",
                "type": "single_select",
                "options": ["never", "annually", "semi_annually", "quarterly"],
            },
        ],
    },
]


def all_question_ids() -> set[str]:
    return {
        q["id"]
        for section in QUESTIONNAIRE_TEMPLATE
        for q in section["questions"]
    }


def _questions_by_id() -> dict[str, dict]:
    return {
        q["id"]: q
        for section in QUESTIONNAIRE_TEMPLATE
        for q in section["questions"]
    }


def validate_responses(responses: dict) -> list[str]:
    """Validate questionnaire answers against the template.

    Returns a list of human-readable error messages (empty if all valid):
    rejects unknown question ids and answers whose type doesn't match the
    question's declared type (boolean / single_select / text).
    """
    errors: list[str] = []
    questions = _questions_by_id()
    for qid, answer in responses.items():
        question = questions.get(qid)
        if question is None:
            errors.append(f"Unknown question id: {qid}")
            continue
        qtype = question["type"]
        if qtype == "boolean":
            if not isinstance(answer, bool):
                errors.append(f"Answer for '{qid}' must be a boolean.")
        elif qtype == "single_select":
            options = question.get("options", [])
            if answer not in options:
                errors.append(
                    f"Answer for '{qid}' must be one of: {', '.join(options)}."
                )
        elif qtype == "text":
            if not isinstance(answer, str):
                errors.append(f"Answer for '{qid}' must be a string.")
    return errors
