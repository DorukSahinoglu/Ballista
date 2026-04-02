from __future__ import annotations

import inspect
from dataclasses import dataclass, field

from .nodes import LegacyNodeHandler, OperatorHandler, StopCondition


@dataclass
class OperatorRegistry:
    operators: dict[str, OperatorHandler] = field(default_factory=dict)
    stop_conditions: dict[str, StopCondition] = field(default_factory=dict)

    def register_operator(
        self,
        name: str,
        handler: LegacyNodeHandler | OperatorHandler,
    ) -> None:
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

            self.operators[name] = wrapped
            return

        if len(positional_params) == 2:
            self.operators[name] = handler
            return

        raise TypeError(
            f"Operator '{name}' must accept either (context) or (context, params)"
        )

    def register_stop_condition(self, name: str, handler: StopCondition) -> None:
        self.stop_conditions[name] = handler

    def get_operator(self, name: str) -> OperatorHandler:
        try:
            return self.operators[name]
        except KeyError as exc:
            raise KeyError(f"Unknown operator '{name}'") from exc

    def get_stop_condition(self, name: str) -> StopCondition:
        try:
            return self.stop_conditions[name]
        except KeyError as exc:
            raise KeyError(f"Unknown stop condition '{name}'") from exc
