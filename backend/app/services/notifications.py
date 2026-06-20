"""Transition notifications via the Observer pattern — Iteration 3.

State transitions are *subjects*; notifiers are *observers* that react to them.
This keeps the engine decoupled from how (or whether) anyone is told about a
transition. The default observer is a **mock Slack notifier** that records the
messages it would post — no Slack credentials or network calls required, in
keeping with Combuyn's mock-first stance. A real Slack webhook notifier can be
registered later without touching the engine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

logger = logging.getLogger("combuyn.workflow")


@dataclass
class TransitionNotice:
    """An immutable description of a transition worth notifying about."""

    subject: str
    workflow: str
    from_state: str
    to_state: str
    kind: str  # "transition" | "complete" | "compensation" | ...

    def message(self) -> str:
        if self.kind == "complete":
            return f"✅ *{self.subject}* ({self.workflow}) completed at '{self.to_state}'."
        if self.kind in ("compensation", "compensated"):
            return (
                f"↩️ *{self.subject}* ({self.workflow}) rolled back "
                f"'{self.from_state}' → '{self.to_state}'."
            )
        return (
            f"➡️ *{self.subject}* ({self.workflow}) moved "
            f"'{self.from_state}' → '{self.to_state}'."
        )


class TransitionObserver(Protocol):
    def on_transition(self, notice: TransitionNotice) -> None: ...


@dataclass
class SlackNotifier:
    """Mock Slack observer: records the messages it would post to a channel."""

    channel: str = "#grc-workflows"
    sent: list[dict] = field(default_factory=list)

    def on_transition(self, notice: TransitionNotice) -> None:
        text = notice.message()
        self.sent.append(
            {
                "channel": self.channel,
                "text": text,
                "subject": notice.subject,
                "workflow": notice.workflow,
                "kind": notice.kind,
            }
        )
        logger.info("[slack:%s] %s", self.channel, text)

    def recent(self, limit: int = 50) -> list[dict]:
        return list(reversed(self.sent[-limit:]))


class WorkflowNotifier:
    """Registry of observers; broadcasts each notice to all of them."""

    def __init__(self) -> None:
        self._observers: list[TransitionObserver] = []

    def register(self, observer: TransitionObserver) -> None:
        self._observers.append(observer)

    def notify(self, notice: TransitionNotice) -> None:
        for observer in self._observers:
            observer.on_transition(notice)


# Process-wide singletons wired at import. The API exposes ``slack.recent()`` so
# the UI can show a live "notifications" feed for the demo.
slack = SlackNotifier()
notifier = WorkflowNotifier()
notifier.register(slack)
