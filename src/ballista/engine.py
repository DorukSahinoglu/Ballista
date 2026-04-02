from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from .models import BallistaContext, SlotDefinition
from .nodes import Node


@dataclass(slots=True)
class Algorithm:
    name: str
    root: Node
    description: str = ""


class AlgorithmEngine:
    """Runs a Ballista algorithm against an isolated context."""

    def run(
        self,
        algorithm: Algorithm,
        initial_slots: dict[str, object] | None = None,
        slot_schema: dict[str, SlotDefinition] | None = None,
    ) -> BallistaContext:
        context = BallistaContext(
            slots=deepcopy(initial_slots or {}),
            slot_schema=deepcopy(slot_schema or {}),
        )
        algorithm.root.execute(context)
        return context
