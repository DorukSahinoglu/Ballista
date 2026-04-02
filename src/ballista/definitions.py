from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .engine import Algorithm
from .models import BallistaContext, SlotDefinition
from .nodes import ConditionNode, LoopNode, Node, PythonNode, SequenceNode
from .registry import OperatorRegistry


@dataclass(slots=True)
class LoadedAlgorithm:
    algorithm: Algorithm
    initial_slots: dict[str, Any]
    slot_schema: dict[str, SlotDefinition]


def load_algorithm_definition(
    definition: dict[str, Any],
    registry: OperatorRegistry,
) -> LoadedAlgorithm:
    name = _require_string(definition, "name")
    description = cast(str, definition.get("description", ""))
    slot_schema = _parse_slot_definitions(
        cast(list[dict[str, Any]], definition.get("slot_definitions", []))
    )
    initial_slots = _build_initial_slots(
        slot_schema,
        cast(dict[str, Any], definition.get("initial_slots", {})),
    )
    root_payload = cast(dict[str, Any], definition["root"])
    root_node = _parse_node(root_payload, registry)
    algorithm = Algorithm(name=name, root=root_node, description=description)
    return LoadedAlgorithm(
        algorithm=algorithm,
        initial_slots=initial_slots,
        slot_schema=slot_schema,
    )


def load_algorithm_definition_file(
    path: str | Path,
    registry: OperatorRegistry,
) -> LoadedAlgorithm:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return load_algorithm_definition(payload, registry)


def _parse_node(payload: dict[str, Any], registry: OperatorRegistry) -> Node:
    node_type = _require_string(payload, "type")
    name = _require_string(payload, "name")

    if node_type == "operator":
        operator_name = _require_string(payload, "operator")
        return PythonNode(
            name=name,
            handler=registry.get_operator(operator_name),
            param_resolver=_build_param_resolver(payload.get("params", {})),
            message=cast(str | None, payload.get("message")),
            snapshot_keys=cast(list[str] | None, payload.get("snapshot_keys")),
        )

    if node_type == "sequence":
        steps = [
            _parse_node(cast(dict[str, Any], step_payload), registry)
            for step_payload in cast(list[dict[str, Any]], payload.get("steps", []))
        ]
        return SequenceNode.from_iterable(name, steps)

    if node_type == "loop":
        body_payload = cast(dict[str, Any], payload["body"])
        body_node = _parse_node(body_payload, registry)
        if not isinstance(body_node, SequenceNode):
            raise TypeError("Loop body must resolve to a SequenceNode")

        stop_condition_name = cast(str | None, payload.get("stop_condition"))
        stop_condition = None
        if stop_condition_name is not None:
            stop_condition = registry.get_stop_condition(stop_condition_name)

        return LoopNode(
            name=name,
            body=body_node,
            max_iterations=cast(int | None, payload.get("max_iterations")),
            stop_condition=stop_condition,
        )

    if node_type == "condition":
        then_node = _parse_node(cast(dict[str, Any], payload["then"]), registry)
        else_payload = cast(dict[str, Any] | None, payload.get("else"))
        else_node = None if else_payload is None else _parse_node(else_payload, registry)
        return ConditionNode(
            name=name,
            evaluator=_build_condition_evaluator(cast(dict[str, Any], payload["condition"])),
            then_branch=then_node,
            else_branch=else_node,
            true_message=cast(str | None, payload.get("true_message")),
            false_message=cast(str | None, payload.get("false_message")),
            snapshot_keys=cast(list[str] | None, payload.get("snapshot_keys")),
        )

    raise ValueError(f"Unsupported node type '{node_type}'")


def _parse_slot_definitions(
    payload: list[dict[str, Any]],
) -> dict[str, SlotDefinition]:
    definitions: dict[str, SlotDefinition] = {}
    for item in payload:
        name = _require_string(item, "name")
        kind = _require_string(item, "kind")
        representation = cast(str | None, item.get("representation"))
        metadata = cast(dict[str, Any], item.get("metadata", {}))
        if not isinstance(metadata, dict):
            raise ValueError(f"Slot '{name}' metadata must be an object")

        definitions[name] = SlotDefinition(
            name=name,
            kind=kind,
            representation=representation,
            default=deepcopy(item.get("default")),
            has_default="default" in item,
            metadata=deepcopy(metadata),
        )

    return definitions


def _build_initial_slots(
    slot_schema: dict[str, SlotDefinition],
    initial_slots: dict[str, Any],
) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for name, definition in slot_schema.items():
        if definition.has_default:
            resolved[name] = deepcopy(definition.default)

    resolved.update(deepcopy(initial_slots))
    return resolved


def _build_param_resolver(payload: Any):
    def resolve(context: BallistaContext) -> dict[str, Any]:
        resolved = _resolve_value(payload, context)
        if not isinstance(resolved, dict):
            raise TypeError("Operator params must resolve to an object")
        return resolved

    return resolve


def _build_condition_evaluator(payload: dict[str, Any]):
    if "all" in payload:
        evaluators = [
            _build_condition_evaluator(cast(dict[str, Any], item))
            for item in cast(list[dict[str, Any]], payload["all"])
        ]
        return lambda context: all(evaluator(context) for evaluator in evaluators)

    if "any" in payload:
        evaluators = [
            _build_condition_evaluator(cast(dict[str, Any], item))
            for item in cast(list[dict[str, Any]], payload["any"])
        ]
        return lambda context: any(evaluator(context) for evaluator in evaluators)

    if "not" in payload:
        evaluator = _build_condition_evaluator(cast(dict[str, Any], payload["not"]))
        return lambda context: not evaluator(context)

    operator = _require_string(payload, "operator")

    if operator == "truthy":
        value_resolver = _build_value_resolver(payload["value"])
        return lambda context: bool(value_resolver(context))

    left_resolver = _build_value_resolver(payload["left"])
    right_resolver = _build_value_resolver(payload["right"])

    operations = {
        "equals": lambda left, right: left == right,
        "not_equals": lambda left, right: left != right,
        "gt": lambda left, right: left > right,
        "gte": lambda left, right: left >= right,
        "lt": lambda left, right: left < right,
        "lte": lambda left, right: left <= right,
        "contains": lambda left, right: right in left,
        "in": lambda left, right: left in right,
    }

    if operator not in operations:
        raise ValueError(f"Unsupported condition operator '{operator}'")

    compare = operations[operator]
    return lambda context: compare(left_resolver(context), right_resolver(context))


def _build_value_resolver(spec: Any):
    return lambda context: _resolve_value(spec, context)


def _resolve_value(spec: Any, context: BallistaContext) -> Any:
    if isinstance(spec, dict):
        if "$ref" in spec:
            return _resolve_reference(cast(str, spec["$ref"]), context)

        return {key: _resolve_value(value, context) for key, value in spec.items()}

    if isinstance(spec, list):
        return [_resolve_value(item, context) for item in spec]

    return deepcopy(spec)


def _resolve_reference(reference: str, context: BallistaContext) -> Any:
    if reference == "iteration":
        return context.iteration

    parts = reference.split(".")
    root = parts[0]

    if root == "slots":
        value: Any = context.slots
    elif root == "metrics":
        value = context.metrics
    elif root == "schema":
        value = context.slot_schema
    else:
        raise ValueError(f"Unsupported reference root '{root}'")

    for part in parts[1:]:
        if isinstance(value, dict):
            value = value[part]
            continue

        if isinstance(value, list):
            value = value[int(part)]
            continue

        value = getattr(value, part)

    return deepcopy(value)


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Definition field '{key}' must be a non-empty string")
    return value
