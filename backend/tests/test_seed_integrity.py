"""Structural validation of CCF reference data and seeder idempotency."""

from __future__ import annotations

from app.seed.ccf_reference import COMMON_CONTROLS, FRAMEWORKS, REQUIREMENTS
from app.seed.questionnaire import QUESTIONNAIRE_TEMPLATE


def test_ccf_reference_all_frameworks_have_requirements():
    for fw in FRAMEWORKS:
        assert fw["key"] in REQUIREMENTS, f"No requirements for framework '{fw['key']}'"
        assert len(REQUIREMENTS[fw["key"]]) > 0, f"Empty requirements for '{fw['key']}'"


def test_ccf_reference_no_duplicate_control_keys():
    keys = [c["key"] for c in COMMON_CONTROLS]
    assert len(keys) == len(set(keys)), "Duplicate CCF control keys found"


def test_ccf_reference_required_fields_present():
    required = {"key", "name", "version", "category"}
    for fw in FRAMEWORKS:
        missing = required - set(fw.keys())
        assert not missing, f"Framework '{fw.get('key')}' missing fields: {missing}"


def test_questionnaire_all_questions_have_ids():
    for section in QUESTIONNAIRE_TEMPLATE:
        for q in section["questions"]:
            assert "id" in q, f"Question missing 'id' in section '{section['section']}'"


def test_questionnaire_no_duplicate_ids():
    ids = [q["id"] for section in QUESTIONNAIRE_TEMPLATE for q in section["questions"]]
    assert len(ids) == len(set(ids)), "Duplicate question IDs found in questionnaire template"


def test_seed_ccf_idempotent_second_run_no_error(db_session):
    from app.seed.seeder import seed_ccf

    with db_session() as session:
        result = seed_ccf(session)
    assert result == {"frameworks": 0, "requirements": 0, "controls": 0, "mappings": 0}


def test_seed_vendors_idempotent_second_run_no_error(db_session):
    from app.seed.seeder import seed_vendors

    with db_session() as session:
        created = seed_vendors(session)
    assert created == 0
