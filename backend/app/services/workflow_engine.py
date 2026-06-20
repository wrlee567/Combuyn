"""Workflow state-machine engine — Iteration 3 (pure, tested).

This module is the brain of the orchestration engine and is deliberately free of
any database or I/O concerns, so it is deterministic and trivially testable. The
router and seeder layer persistence and notifications on top of these functions.

A *blueprint* is a plain dict::

    {
      "initial": "intake",
      "states": [{"id": "intake", "label": "Intake", "type": "start"}, ...],
      "transitions": [
        {"action": "submit", "from": "intake", "to": "review",
         "compensation": "Re-open intake"},
        ...
      ],
    }

A state ``type`` of ``"end"`` marks a terminal state (the run completes). A
forward transition may carry a ``compensation`` label describing how to undo it;
:func:`plan_compensation` walks the executed transitions in reverse to build the
Saga rollback plan.
"""

from __future__ import annotations

from dataclasses import dataclass


class BlueprintError(ValueError):
    """Raised when a workflow blueprint is structurally invalid."""


class InvalidTransitionError(ValueError):
    """Raised when an action is not allowed from the instance's current state."""


@dataclass
class Transition:
    action: str
    source: str
    target: str
    compensation: str = ""


def _states(blueprint: dict) -> dict[str, dict]:
    return {s["id"]: s for s in blueprint.get("states", [])}


def validate_blueprint(blueprint: dict) -> None:
    """Validate a blueprint's structure, raising :class:`BlueprintError`."""
    if not isinstance(blueprint, dict):
        raise BlueprintError("Blueprint must be an object.")

    states = blueprint.get("states")
    if not states:
        raise BlueprintError("Blueprint must define at least one state.")

    ids: list[str] = []
    for state in states:
        sid = state.get("id")
        if not sid:
            raise BlueprintError("Every state needs an 'id'.")
        ids.append(sid)
    if len(ids) != len(set(ids)):
        raise BlueprintError("Duplicate state ids in blueprint.")
    id_set = set(ids)

    initial = blueprint.get("initial")
    if initial not in id_set:
        raise BlueprintError(f"Initial state '{initial}' is not a defined state.")

    seen: set[tuple[str, str]] = set()
    for tr in blueprint.get("transitions", []):
        action, src, dst = tr.get("action"), tr.get("from"), tr.get("to")
        if not action or not src or not dst:
            raise BlueprintError("Each transition needs 'action', 'from', and 'to'.")
        if src not in id_set or dst not in id_set:
            raise BlueprintError(
                f"Transition '{action}' references an unknown state ({src}->{dst})."
            )
        key = (src, action)
        if key in seen:
            raise BlueprintError(
                f"Ambiguous transition: action '{action}' is defined twice "
                f"from state '{src}'."
            )
        seen.add(key)

    if not any(is_terminal(blueprint, sid) for sid in id_set):
        raise BlueprintError("Blueprint must define at least one terminal (end) state.")


def is_terminal(blueprint: dict, state: str) -> bool:
    """True when no transitions leave ``state`` (or it is typed ``end``)."""
    meta = _states(blueprint).get(state, {})
    if meta.get("type") == "end":
        return True
    return not any(t.get("from") == state for t in blueprint.get("transitions", []))


def available_actions(blueprint: dict, state: str) -> list[Transition]:
    """Transitions that can fire from ``state``, in blueprint order."""
    out: list[Transition] = []
    for tr in blueprint.get("transitions", []):
        if tr.get("from") == state:
            out.append(
                Transition(
                    action=tr["action"],
                    source=tr["from"],
                    target=tr["to"],
                    compensation=tr.get("compensation", ""),
                )
            )
    return out


def resolve_transition(blueprint: dict, state: str, action: str) -> Transition:
    """Resolve ``action`` from ``state`` or raise :class:`InvalidTransitionError`."""
    for tr in available_actions(blueprint, state):
        if tr.action == action:
            return tr
    allowed = ", ".join(t.action for t in available_actions(blueprint, state)) or "none"
    raise InvalidTransitionError(
        f"Action '{action}' is not allowed from state '{state}'. Allowed: {allowed}."
    )


def replay_state(blueprint: dict, transitions: list[tuple[str, str]]) -> str:
    """Rebuild the current state from the initial state + an ordered list of
    ``(from_state, to_state)`` transitions. This is how a crashed instance is
    recovered: replay its durable event log instead of trusting volatile memory.
    """
    state = blueprint["initial"]
    for src, dst in transitions:
        if src != state:
            raise InvalidTransitionError(
                f"Event log is inconsistent: expected to leave '{state}' but "
                f"event left '{src}'."
            )
        state = dst
    return state


def plan_compensation(
    blueprint: dict, executed: list[tuple[str, str, str]]
) -> list[Transition]:
    """Build a Saga rollback plan from already-executed forward transitions.

    ``executed`` is an ordered list of ``(action, from_state, to_state)`` tuples.
    Compensation runs them in reverse, producing inverse transitions (target ->
    source) carrying each forward step's compensation label.
    """
    plan: list[Transition] = []
    for action, src, dst in reversed(executed):
        comp = ""
        for tr in blueprint.get("transitions", []):
            if tr.get("action") == action and tr.get("from") == src and tr.get("to") == dst:
                comp = tr.get("compensation", "")
                break
        plan.append(
            Transition(
                action=f"compensate_{action}",
                source=dst,
                target=src,
                compensation=comp or f"Undo '{action}'",
            )
        )
    return plan
