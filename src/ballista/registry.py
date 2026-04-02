from __future__ import annotations

import inspect
from dataclasses import dataclass, field

from .nodes import LegacyNodeHandler, OperatorHandler, StopCondition


@dataclass(slots=True)
class OperatorParamSchema:
    name: str
    required: bool = False
    description: str = ""
    slot_kinds: list[str] = field(default_factory=list)
    representations: list[str] = field(default_factory=list)


@dataclass(slots=True)
class OperatorSpec:
    name: str
    handler: OperatorHandler
    params: dict[str, OperatorParamSchema] = field(default_factory=dict)
    description: str = ""


@dataclass
class OperatorRegistry:
    operators: dict[str, OperatorSpec] = field(default_factory=dict)
    stop_conditions: dict[str, StopCondition] = field(default_factory=dict)

    def register_operator(
        self,
        name: str,
        handler: LegacyNodeHandler | OperatorHandler,
        *,
        params: list[OperatorParamSchema] | None = None,
        description: str = "",
    ) -> None:
        wrapped = _normalize_handler(name, handler)
        param_schema = {item.name: item for item in params or []}
        self.operators[name] = OperatorSpec(
            name=name,
            handler=wrapped,
            params=param_schema,
            description=description,
        )

    def register_stop_condition(self, name: str, handler: StopCondition) -> None:
        self.stop_conditions[name] = handler

    def has_operator(self, name: str) -> bool:
        return name in self.operators

    def has_stop_condition(self, name: str) -> bool:
        return name in self.stop_conditions

    def get_operator(self, name: str) -> OperatorHandler:
        try:
            return self.operators[name].handler
        except KeyError as exc:
            raise KeyError(f"Unknown operator '{name}'") from exc

    def get_operator_spec(self, name: str) -> OperatorSpec:
        try:
            return self.operators[name]
        except KeyError as exc:
            raise KeyError(f"Unknown operator '{name}'") from exc

    def get_stop_condition(self, name: str) -> StopCondition:
        try:
            return self.stop_conditions[name]
        except KeyError as exc:
            raise KeyError(f"Unknown stop condition '{name}'") from exc


def _normalize_handler(
    name: str,
    handler: LegacyNodeHandler | OperatorHandler,
) -> OperatorHandler:
    signature = inspect.signature(handler)
    positional_params = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    ]

    if len(positional_params) == 1:
        legacy_handler = handler

        def wrapped(context, params) -> None:
            del params
            legacy_handler(context)

        return wrapped

    if len(positional_params) == 2:
        return handler

    raise TypeError(
        f"Operator '{name}' must accept either (context) or (context, params)"
    )
