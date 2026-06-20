"""Unit tests for the pure workflow state-machine engine — Iteration 3."""

from __future__ import annotations

import pytest

from app.services import workflow_engine as engine

BLUEPRINT = {
    "initial": "a",
    "states": [
        {"id": "a", "type": "start"},
        {"id": "b"},
        {"id": "done", "type": "end"},
        {"id": "killed", "type": "end"},
    ],
    "transitions": [
        {"action": "go", "from": "a", "to": "b", "compensation": "undo go"},
        {"action": "finish", "from": "b", "to": "done"},
        {"action": "abort", "from": "a", "to": "killed"},
        {"action": "abort", "from": "b", "to": "killed"},
    ],
}


def test_validate_blueprint_accepts_valid():
    engine.validate_blueprint(BLUEPRINT)  # no raise


def test_validate_blueprint_rejects_missing_initial():
    bad = {**BLUEPRINT, "initial": "nope"}
    with pytest.raises(engine.BlueprintError):
        engine.validate_blueprint(bad)


def test_validate_blueprint_rejects_no_states():
    with pytest.raises(engine.BlueprintError):
        engine.validate_blueprint({"initial": "a", "states": []})


def test_validate_blueprint_rejects_unknown_transition_target():
    bad = {
        "initial": "a",
        "states": [{"id": "a"}, {"id": "done", "type": "end"}],
        "transitions": [{"action": "go", "from": "a", "to": "ghost"}],
    }
    with pytest.raises(engine.BlueprintError):
        engine.validate_blueprint(bad)


def test_validate_blueprint_rejects_ambiguous_action():
    bad = {
        "initial": "a",
        "states": [{"id": "a"}, {"id": "b"}, {"id": "c", "type": "end"}],
        "transitions": [
            {"action": "go", "from": "a", "to": "b"},
            {"action": "go", "from": "a", "to": "c"},
        ],
    }
    with pytest.raises(engine.BlueprintError):
        engine.validate_blueprint(bad)


def test_validate_blueprint_requires_terminal_state():
    bad = {
        "initial": "a",
        "states": [{"id": "a"}, {"id": "b"}],
        "transitions": [
            {"action": "go", "from": "a", "to": "b"},
            {"action": "back", "from": "b", "to": "a"},
        ],
    }
    with pytest.raises(engine.BlueprintError):
        engine.validate_blueprint(bad)


def test_is_terminal():
    assert engine.is_terminal(BLUEPRINT, "done")
    assert engine.is_terminal(BLUEPRINT, "killed")
    assert not engine.is_terminal(BLUEPRINT, "a")


def test_available_actions():
    actions = {t.action for t in engine.available_actions(BLUEPRINT, "a")}
    assert actions == {"go", "abort"}


def test_resolve_transition_ok():
    tr = engine.resolve_transition(BLUEPRINT, "a", "go")
    assert tr.target == "b"
    assert tr.compensation == "undo go"


def test_resolve_transition_invalid():
    with pytest.raises(engine.InvalidTransitionError):
        engine.resolve_transition(BLUEPRINT, "a", "finish")


def test_replay_state_rebuilds_current_state():
    state = engine.replay_state(BLUEPRINT, [("a", "b"), ("b", "done")])
    assert state == "done"


def test_replay_state_detects_inconsistent_log():
    with pytest.raises(engine.InvalidTransitionError):
        engine.replay_state(BLUEPRINT, [("b", "done")])  # didn't start at 'a'


def test_plan_compensation_reverses_executed_transitions():
    executed = [("go", "a", "b"), ("finish", "b", "done")]
    plan = engine.plan_compensation(BLUEPRINT, executed)
    # Reversed order: undo finish first, then undo go.
    assert [p.source for p in plan] == ["done", "b"]
    assert [p.target for p in plan] == ["b", "a"]
    assert plan[1].compensation == "undo go"
