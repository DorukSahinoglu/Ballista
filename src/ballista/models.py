from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SlotDefinition:
    name: str
    kind: str
    representation: str | None = None
    default: Any = None
    has_default: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StepRecord:
    iteration: int
    node: str
    message: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass
class BallistaContext:
    """Shared blackboard state for the current algorithm run."""

    slots: dict[str, Any] = field(default_factory=dict)
    slot_schema: dict[str, SlotDefinition] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    history: list[StepRecord] = field(default_factory=list)
    iteration: int = 0
    stopped: bool = False

    def get(self, key: str, default: Any = None) -> Any:
        return self.slots.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.slots[key] = value

    def get_slot_definition(self, key: str) -> SlotDefinition | None:
        return self.slot_schema.get(key)

    def update_metric(self, key: str, value: Any) -> None:
        self.metrics[key] = value

    def stop(self) -> None:
        self.stopped = True

    def record(
        self,
        node: str,
        message: str | None = None,
        *,
        snapshot_keys: list[str] | None = None,
    ) -> None:
        if snapshot_keys is None:
            snapshot = {}
        else:
            snapshot = {key: deepcopy(self.slots.get(key)) for key in snapshot_keys}

        self.history.append(
            StepRecord(
                iteration=self.iteration,
                node=node,
                message=message,
                metrics=deepcopy(self.metrics),
                snapshot=snapshot,
            )
        )
