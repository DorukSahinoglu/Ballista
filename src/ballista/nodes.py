from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from .models import BallistaContext

LegacyNodeHandler = Callable[[BallistaContext], None]
OperatorHandler = Callable[[BallistaContext, dict[str, Any]], None]
StopCondition = Callable[[BallistaContext], bool]
ParamResolver = Callable[[BallistaContext], dict[str, Any]]
ConditionEvaluator = Callable[[BallistaContext], bool]


class Node(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def execute(self, context: BallistaContext) -> None:
        """Mutates the shared context."""


@dataclass
class PythonNode(Node):
    name: str
    handler: OperatorHandler
    params: dict[str, Any] = field(default_factory=dict)
    param_resolver: ParamResolver | None = None
    message: str | None = None
    snapshot_keys: list[str] | None = None

    def __post_init__(self) -> None:
        Node.__init__(self, self.name)

    def execute(self, context: BallistaContext) -> None:
        resolved_params = deepcopy(self.params)
        if self.param_resolver is not None:
            resolved_params.update(self.param_resolver(context))

        self.handler(context, resolved_params)
        context.record(
            self.name,
            self.message,
            snapshot_keys=self.snapshot_keys,
        )


@dataclass
class SequenceNode(Node):
    name: str
    steps: list[Node] = field(default_factory=list)

    def __post_init__(self) -> None:
        Node.__init__(self, self.name)

    @classmethod
    def from_iterable(cls, name: str, steps: Iterable[Node]) -> "SequenceNode":
        return cls(name=name, steps=list(steps))

    def execute(self, context: BallistaContext) -> None:
        for step in self.steps:
            if context.stopped:
                return
            step.execute(context)


@dataclass
class LoopNode(Node):
    name: str
    body: SequenceNode
    max_iterations: int | None = None
    stop_condition: StopCondition | None = None

    def __post_init__(self) -> None:
        Node.__init__(self, self.name)

    def execute(self, context: BallistaContext) -> None:
        while not context.stopped:
            if self.max_iterations is not None and context.iteration >= self.max_iterations:
                context.record(self.name, "max iterations reached")
                return

            self.body.execute(context)

            if context.stopped:
                return

            context.iteration += 1

            if self.stop_condition is not None and self.stop_condition(context):
                context.record(self.name, "stop condition reached")
                return


@dataclass
class ConditionNode(Node):
    name: str
    evaluator: ConditionEvaluator
    then_branch: Node
    else_branch: Node | None = None
    true_message: str | None = None
    false_message: str | None = None
    snapshot_keys: list[str] | None = None

    def __post_init__(self) -> None:
        Node.__init__(self, self.name)

    def execute(self, context: BallistaContext) -> None:
        result = self.evaluator(context)
        context.record(
            self.name,
            self.true_message if result else self.false_message,
            snapshot_keys=self.snapshot_keys,
        )

        if result:
            self.then_branch.execute(context)
            return

        if self.else_branch is not None:
            self.else_branch.execute(context)
