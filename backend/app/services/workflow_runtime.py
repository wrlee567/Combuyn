"""Durable execution helpers binding the pure engine to persistence — Iter 3.

These functions mutate ORM objects (appending the immutable event log and
advancing the persisted current state) and optionally emit observer
notifications. They deliberately do **not** commit — the caller (router or
seeder) owns the transaction boundary, mirroring the vendor API. Passing
``notifier=None`` runs silently, which the seeder uses so bootstrap activity does
not flood the live notifications feed.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.workflow import WorkflowDefinition, WorkflowEvent, WorkflowInstance
from app.services import workflow_engine as engine
from app.services.notifications import TransitionNotice, WorkflowNotifier


def _next_sequence(instance: WorkflowInstance) -> int:
    return max((e.sequence for e in instance.events), default=-1) + 1


def _emit(
    notifier: WorkflowNotifier | None,
    instance: WorkflowInstance,
    definition: WorkflowDefinition,
    from_state: str,
    to_state: str,
    kind: str,
) -> None:
    if notifier is None:
        return
    notifier.notify(
        TransitionNotice(
            subject=instance.subject,
            workflow=definition.name,
            from_state=from_state,
            to_state=to_state,
            kind=kind,
        )
    )


def start_instance(
    db: Session,
    definition: WorkflowDefinition,
    subject: str,
    context: dict | None = None,
    notifier: WorkflowNotifier | None = None,
) -> WorkflowInstance:
    """Create a new instance parked at the blueprint's initial state."""
    initial = definition.blueprint["initial"]
    instance = WorkflowInstance(
        definition_id=definition.id,
        subject=subject,
        current_state=initial,
        status="running",
        context=context or {},
    )
    instance.definition = definition
    instance.events.append(
        WorkflowEvent(
            sequence=0,
            kind="start",
            action="",
            from_state="",
            to_state=initial,
            note="Instance created",
        )
    )
    db.add(instance)
    _emit(notifier, instance, definition, "", initial, "transition")
    return instance


def advance_instance(
    db: Session,
    instance: WorkflowInstance,
    action: str,
    note: str = "",
    notifier: WorkflowNotifier | None = None,
) -> WorkflowInstance:
    """Fire ``action`` from the current state, persisting the transition.

    Raises :class:`engine.InvalidTransitionError` if the action is not allowed or
    the instance is no longer running.
    """
    definition = instance.definition
    blueprint = definition.blueprint

    if instance.status != "running":
        raise engine.InvalidTransitionError(
            f"Instance is '{instance.status}', not running; cannot advance."
        )

    transition = engine.resolve_transition(blueprint, instance.current_state, action)
    from_state = instance.current_state

    instance.events.append(
        WorkflowEvent(
            sequence=_next_sequence(instance),
            kind="transition",
            action=transition.action,
            from_state=from_state,
            to_state=transition.target,
            note=note,
        )
    )
    instance.current_state = transition.target

    completed = engine.is_terminal(blueprint, transition.target)
    _emit(
        notifier,
        instance,
        definition,
        from_state,
        transition.target,
        "complete" if completed else "transition",
    )

    if completed:
        instance.status = "completed"
        instance.events.append(
            WorkflowEvent(
                sequence=_next_sequence(instance),
                kind="complete",
                action="",
                from_state=transition.target,
                to_state=transition.target,
                note="Reached terminal state",
            )
        )
    return instance


def compensate_instance(
    db: Session,
    instance: WorkflowInstance,
    note: str = "",
    notifier: WorkflowNotifier | None = None,
) -> WorkflowInstance:
    """Roll a running instance back via Saga compensation.

    Walks the executed forward transitions in reverse, appending a compensation
    event for each, then parks the instance back at the initial state with status
    ``compensated``.
    """
    definition = instance.definition
    blueprint = definition.blueprint

    if instance.status != "running":
        raise engine.InvalidTransitionError(
            f"Instance is '{instance.status}'; only running instances can be compensated."
        )

    executed = [
        (e.action, e.from_state, e.to_state)
        for e in instance.events
        if e.kind == "transition" and e.action
    ]
    plan = engine.plan_compensation(blueprint, executed)

    for step in plan:
        instance.events.append(
            WorkflowEvent(
                sequence=_next_sequence(instance),
                kind="compensation",
                action=step.action,
                from_state=step.source,
                to_state=step.target,
                note=step.compensation,
            )
        )
        _emit(notifier, instance, definition, step.source, step.target, "compensation")
        instance.current_state = step.target

    instance.status = "compensated"
    instance.events.append(
        WorkflowEvent(
            sequence=_next_sequence(instance),
            kind="compensated",
            action="",
            from_state=instance.current_state,
            to_state=instance.current_state,
            note=note or "Saga rolled back",
        )
    )
    return instance
