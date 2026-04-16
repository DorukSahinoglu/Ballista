from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from .expression import SUPPORTED_EXPRESSION_OPERATORS
from .registry import OperatorParamSchema, OperatorRegistry


@dataclass(slots=True)
class ValidationIssue:
    path: str
    message: str
    severity: str = "error"


def validate_algorithm_definition(
    definition: dict[str, Any],
    registry: OperatorRegistry,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    slot_schema = _collect_slot_schema(definition, issues)
    subgraph_payloads = _collect_subgraph_payloads(definition, issues)

    if not isinstance(definition.get("name"), str) or not definition.get("name", "").strip():
        issues.append(ValidationIssue(path="name", message="Definition name is required"))

    root = definition.get("root")
    if not isinstance(root, dict):
        issues.append(ValidationIssue(path="root", message="Root node must be an object"))
        return issues

    for subgraph_name, payload in subgraph_payloads.items():
        _validate_node(
            payload,
            f"subgraphs.{subgraph_name}.node",
            registry,
            slot_schema,
            subgraph_payloads,
            issues,
        )

    _validate_node(root, "root", registry, slot_schema, subgraph_payloads, issues)
    return issues


def assert_valid_algorithm_definition(
    definition: dict[str, Any],
    registry: OperatorRegistry,
) -> None:
    issues = validate_algorithm_definition(definition, registry)
    errors = [issue for issue in issues if issue.severity == "error"]
    if not errors:
        return

    details = "\n".join(f"- {issue.path}: {issue.message}" for issue in errors)
    raise ValueError(f"Invalid algorithm definition:\n{details}")


def _collect_slot_schema(
    definition: dict[str, Any],
    issues: list[ValidationIssue],
) -> dict[str, dict[str, Any]]:
    collected: dict[str, dict[str, Any]] = {}
    raw_slot_definitions = definition.get("slot_definitions", [])

    if not isinstance(raw_slot_definitions, list):
        issues.append(
            ValidationIssue(
                path="slot_definitions",
                message="slot_definitions must be a list",
            )
        )
        return collected

    for index, item in enumerate(raw_slot_definitions):
        path = f"slot_definitions[{index}]"
        if not isinstance(item, dict):
            issues.append(ValidationIssue(path=path, message="Slot definition must be an object"))
            continue

        name = item.get("name")
        kind = item.get("kind")
        if not isinstance(name, str) or not name.strip():
            issues.append(ValidationIssue(path=f"{path}.name", message="Slot name is required"))
            continue

        if not isinstance(kind, str) or not kind.strip():
            issues.append(ValidationIssue(path=f"{path}.kind", message="Slot kind is required"))
            continue

        collected[name] = {
            "kind": kind,
            "representation": item.get("representation"),
        }

    return collected


def _collect_subgraph_payloads(
    definition: dict[str, Any],
    issues: list[ValidationIssue],
) -> dict[str, dict[str, Any]]:
    collected: dict[str, dict[str, Any]] = {}
    raw_subgraphs = definition.get("subgraphs", [])

    if raw_subgraphs is None:
        return collected

    if not isinstance(raw_subgraphs, list):
        issues.append(ValidationIssue(path="subgraphs", message="subgraphs must be a list"))
        return collected

    for index, item in enumerate(raw_subgraphs):
        path = f"subgraphs[{index}]"
        if not isinstance(item, dict):
            issues.append(ValidationIssue(path=path, message="Subgraph must be an object"))
            continue

        name = item.get("name")
        node_payload = item.get("node")
        if not isinstance(name, str) or not name.strip():
            issues.append(ValidationIssue(path=f"{path}.name", message="Subgraph name is required"))
            continue

        if not isinstance(node_payload, dict):
            issues.append(ValidationIssue(path=f"{path}.node", message="Subgraph node must be an object"))
            continue

        collected[name] = node_payload

    return collected


def _validate_node(
    payload: dict[str, Any],
    path: str,
    registry: OperatorRegistry,
    slot_schema: dict[str, dict[str, Any]],
    subgraph_payloads: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
) -> None:
    node_type = payload.get("type")
    node_name = payload.get("name")

    if not isinstance(node_name, str) or not node_name.strip():
        issues.append(ValidationIssue(path=f"{path}.name", message="Node name is required"))

    if not isinstance(node_type, str) or not node_type.strip():
        issues.append(ValidationIssue(path=f"{path}.type", message="Node type is required"))
        return

    if node_type == "operator":
        _validate_operator_node(payload, path, registry, slot_schema, issues)
        return

    if node_type == "sequence":
        steps = payload.get("steps", [])
        if not isinstance(steps, list):
            issues.append(ValidationIssue(path=f"{path}.steps", message="Sequence steps must be a list"))
            return

        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                issues.append(
                    ValidationIssue(
                        path=f"{path}.steps[{index}]",
                        message="Sequence step must be an object",
                    )
                )
                continue

            _validate_node(
                step,
                f"{path}.steps[{index}]",
                registry,
                slot_schema,
                subgraph_payloads,
                issues,
            )
        return

    if node_type == "loop":
        body = payload.get("body")
        if not isinstance(body, dict):
            issues.append(ValidationIssue(path=f"{path}.body", message="Loop body must be an object"))
        else:
            _validate_node(
                body,
                f"{path}.body",
                registry,
                slot_schema,
                subgraph_payloads,
                issues,
            )

        stop_condition = payload.get("stop_condition")
        if stop_condition is not None and not registry.has_stop_condition(cast(str, stop_condition)):
            issues.append(
                ValidationIssue(
                    path=f"{path}.stop_condition",
                    message=f"Unknown stop condition '{stop_condition}'",
                )
            )
        return

    if node_type == "condition":
        condition = payload.get("condition")
        if not isinstance(condition, dict):
            issues.append(
                ValidationIssue(path=f"{path}.condition", message="Condition payload must be an object")
            )
        else:
            _validate_condition(condition, f"{path}.condition", slot_schema, issues)

        then_payload = payload.get("then")
        if not isinstance(then_payload, dict):
            issues.append(ValidationIssue(path=f"{path}.then", message="Condition then branch is required"))
        else:
            _validate_node(
                then_payload,
                f"{path}.then",
                registry,
                slot_schema,
                subgraph_payloads,
                issues,
            )

        else_payload = payload.get("else")
        if else_payload is not None:
            if not isinstance(else_payload, dict):
                issues.append(
                    ValidationIssue(path=f"{path}.else", message="Condition else branch must be an object")
                )
            else:
                _validate_node(
                    else_payload,
                    f"{path}.else",
                    registry,
                    slot_schema,
                    subgraph_payloads,
                    issues,
                )
        return

    if node_type == "subgraph":
        reference = payload.get("ref")
        if not isinstance(reference, str) or not reference.strip():
            issues.append(ValidationIssue(path=f"{path}.ref", message="Subgraph reference is required"))
            return

        if reference not in subgraph_payloads:
            issues.append(
                ValidationIssue(path=f"{path}.ref", message=f"Unknown subgraph reference '{reference}'")
            )
        params = payload.get("params", {})
        if not isinstance(params, dict):
            issues.append(ValidationIssue(path=f"{path}.params", message="Subgraph params must be an object"))
            return
        for param_name, value in params.items():
            _validate_value(value, f"{path}.params.{param_name}", slot_schema, issues)
        return

    issues.append(ValidationIssue(path=f"{path}.type", message=f"Unsupported node type '{node_type}'"))


def _validate_operator_node(
    payload: dict[str, Any],
    path: str,
    registry: OperatorRegistry,
    slot_schema: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
) -> None:
    operator_name = payload.get("operator")
    if not isinstance(operator_name, str) or not operator_name.strip():
        issues.append(ValidationIssue(path=f"{path}.operator", message="Operator name is required"))
        return

    if not registry.has_operator(operator_name):
        issues.append(
            ValidationIssue(path=f"{path}.operator", message=f"Unknown operator '{operator_name}'")
        )
        return

    params = payload.get("params", {})
    if not isinstance(params, dict):
        issues.append(ValidationIssue(path=f"{path}.params", message="Operator params must be an object"))
        return

    spec = registry.get_operator_spec(operator_name)
    for param_name, param_schema in spec.params.items():
        if param_schema.required and param_name not in params:
            issues.append(
                ValidationIssue(
                    path=f"{path}.params.{param_name}",
                    message="Required operator parameter is missing",
                )
            )

    for param_name, value in params.items():
        schema = spec.params.get(param_name)
        if schema is None:
            issues.append(
                ValidationIssue(
                    path=f"{path}.params.{param_name}",
                    message="Unknown operator parameter",
                    severity="warning",
                )
            )
        _validate_value(value, f"{path}.params.{param_name}", slot_schema, issues, schema)


def _validate_condition(
    payload: dict[str, Any],
    path: str,
    slot_schema: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
) -> None:
    if "expression" in payload:
        if not isinstance(payload["expression"], dict):
            issues.append(
                ValidationIssue(path=f"{path}.expression", message="Condition expression must be an object")
            )
            return
        _validate_expression(payload["expression"], f"{path}.expression", slot_schema, issues)
        return

    if "all" in payload:
        values = payload["all"]
        if not isinstance(values, list):
            issues.append(ValidationIssue(path=f"{path}.all", message="all must be a list"))
            return

        for index, item in enumerate(values):
            if not isinstance(item, dict):
                issues.append(
                    ValidationIssue(path=f"{path}.all[{index}]", message="Condition entry must be an object")
                )
                continue
            _validate_condition(item, f"{path}.all[{index}]", slot_schema, issues)
        return

    if "any" in payload:
        values = payload["any"]
        if not isinstance(values, list):
            issues.append(ValidationIssue(path=f"{path}.any", message="any must be a list"))
            return

        for index, item in enumerate(values):
            if not isinstance(item, dict):
                issues.append(
                    ValidationIssue(path=f"{path}.any[{index}]", message="Condition entry must be an object")
                )
                continue
            _validate_condition(item, f"{path}.any[{index}]", slot_schema, issues)
        return

    if "not" in payload:
        nested = payload["not"]
        if not isinstance(nested, dict):
            issues.append(ValidationIssue(path=f"{path}.not", message="not must wrap an object"))
            return
        _validate_condition(nested, f"{path}.not", slot_schema, issues)
        return

    operator = payload.get("operator")
    if not isinstance(operator, str) or not operator.strip():
        issues.append(ValidationIssue(path=f"{path}.operator", message="Condition operator is required"))
        return

    if operator == "truthy":
        if "value" not in payload:
            issues.append(ValidationIssue(path=f"{path}.value", message="truthy expects a value"))
            return
        _validate_value(payload["value"], f"{path}.value", slot_schema, issues)
        return

    if "left" not in payload:
        issues.append(ValidationIssue(path=f"{path}.left", message="Condition left operand is required"))
    else:
        _validate_value(payload["left"], f"{path}.left", slot_schema, issues)

    if "right" not in payload:
        issues.append(ValidationIssue(path=f"{path}.right", message="Condition right operand is required"))
    else:
        _validate_value(payload["right"], f"{path}.right", slot_schema, issues)


def _validate_value(
    value: Any,
    path: str,
    slot_schema: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
    param_schema: OperatorParamSchema | None = None,
) -> None:
    if isinstance(value, dict):
        if "$ref" in value:
            ref_value = value["$ref"]
            if not isinstance(ref_value, str) or not ref_value.strip():
                issues.append(ValidationIssue(path=f"{path}.$ref", message="Reference must be a string"))
                return
            _validate_reference(ref_value, path, slot_schema, issues, param_schema)
            return

        if "$expr" in value:
            expr_value = value["$expr"]
            if not isinstance(expr_value, dict):
                issues.append(ValidationIssue(path=f"{path}.$expr", message="Expression must be an object"))
                return
            _validate_expression(expr_value, f"{path}.$expr", slot_schema, issues)
            return

        for key, nested in value.items():
            _validate_value(nested, f"{path}.{key}", slot_schema, issues)
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_value(item, f"{path}[{index}]", slot_schema, issues)


def _validate_reference(
    reference: str,
    path: str,
    slot_schema: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
    param_schema: OperatorParamSchema | None = None,
) -> None:
    if reference == "iteration":
        return

    parts = reference.split(".")
    root = parts[0]
    if root not in {"slots", "metrics", "schema", "vars", "args"}:
        issues.append(
            ValidationIssue(path=path, message=f"Unsupported reference root '{root}'")
        )
        return

    if root in {"slots", "schema"}:
        if len(parts) < 2:
            issues.append(ValidationIssue(path=path, message="Reference must include a slot name"))
            return

        slot_name = parts[1]
        if slot_name not in slot_schema:
            issues.append(
                ValidationIssue(
                    path=path,
                    message=f"Referenced slot '{slot_name}' is not declared in slot_definitions",
                    severity="warning",
                )
            )
            return

        if param_schema is None:
            return

        slot_info = slot_schema[slot_name]
        if param_schema.slot_kinds and slot_info["kind"] not in param_schema.slot_kinds:
            issues.append(
                ValidationIssue(
                    path=path,
                    message=(
                        f"Slot '{slot_name}' has kind '{slot_info['kind']}', expected one of "
                        f"{param_schema.slot_kinds}"
                    ),
                )
            )

        representation = slot_info.get("representation")
        if param_schema.representations and representation not in param_schema.representations:
            issues.append(
                ValidationIssue(
                    path=path,
                    message=(
                        f"Slot '{slot_name}' has representation '{representation}', expected one of "
                        f"{param_schema.representations}"
                    ),
                )
            )


def _validate_expression(
    expression: dict[str, Any],
    path: str,
    slot_schema: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
) -> None:
    operator = expression.get("op")
    if not isinstance(operator, str) or operator not in SUPPORTED_EXPRESSION_OPERATORS:
        issues.append(
            ValidationIssue(
                path=f"{path}.op",
                message=f"Unsupported expression operator '{operator}'",
            )
        )
        return

    if operator == "ref":
        ref_path = expression.get("path")
        if not isinstance(ref_path, str) or not ref_path.strip():
            issues.append(ValidationIssue(path=f"{path}.path", message="Expression ref requires a path"))
            return
        _validate_reference(ref_path, path, slot_schema, issues)
        return

    if operator == "if":
        for key in ("condition", "then", "else"):
            if key not in expression:
                issues.append(ValidationIssue(path=f"{path}.{key}", message=f"Expression if requires '{key}'"))
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "not":
        if "value" not in expression:
            issues.append(ValidationIssue(path=f"{path}.value", message="Expression not requires 'value'"))
            return
        _validate_expression_operand(expression["value"], f"{path}.value", slot_schema, issues)
        return

    if operator in {"and", "or", "add", "mul", "min", "max", "avg"}:
        args = expression.get("args")
        if not isinstance(args, list):
            issues.append(ValidationIssue(path=f"{path}.args", message=f"Expression {operator} requires a list"))
            return
        for index, item in enumerate(args):
            _validate_expression_operand(item, f"{path}.args[{index}]", slot_schema, issues)
        return

    if operator in {"len", "abs"}:
        if "value" not in expression:
            issues.append(ValidationIssue(path=f"{path}.value", message=f"Expression {operator} requires 'value'"))
            return
        _validate_expression_operand(expression["value"], f"{path}.value", slot_schema, issues)
        return

    if operator == "round":
        if "value" not in expression:
            issues.append(ValidationIssue(path=f"{path}.value", message="Expression round requires 'value'"))
        else:
            _validate_expression_operand(expression["value"], f"{path}.value", slot_schema, issues)
        if "digits" in expression:
            _validate_expression_operand(expression["digits"], f"{path}.digits", slot_schema, issues)
        return

    if operator == "get":
        for key in ("source", "key"):
            if key not in expression:
                issues.append(ValidationIssue(path=f"{path}.{key}", message=f"Expression get requires '{key}'"))
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        if "default" in expression:
            _validate_expression_operand(expression["default"], f"{path}.default", slot_schema, issues)
        return

    if operator in {"filter", "map"}:
        if "source" not in expression:
            issues.append(ValidationIssue(path=f"{path}.source", message=f"Expression {operator} requires 'source'"))
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        alias = expression.get("as")
        if alias is not None and (not isinstance(alias, str) or not alias.strip()):
            issues.append(ValidationIssue(path=f"{path}.as", message="Expression alias must be a string"))

        required_key = "where" if operator == "filter" else "value"
        if required_key not in expression:
            issues.append(
                ValidationIssue(
                    path=f"{path}.{required_key}",
                    message=f"Expression {operator} requires '{required_key}'",
                )
            )
        else:
            _validate_expression_operand(expression[required_key], f"{path}.{required_key}", slot_schema, issues)
        return

    if operator == "sort_by":
        if "source" not in expression:
            issues.append(ValidationIssue(path=f"{path}.source", message="Expression sort_by requires 'source'"))
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        alias = expression.get("as")
        if alias is not None and (not isinstance(alias, str) or not alias.strip()):
            issues.append(ValidationIssue(path=f"{path}.as", message="Expression alias must be a string"))

        if "key" not in expression:
            issues.append(ValidationIssue(path=f"{path}.key", message="Expression sort_by requires 'key'"))
        else:
            _validate_expression_operand(expression["key"], f"{path}.key", slot_schema, issues)

        if "descending" in expression:
            _validate_expression_operand(expression["descending"], f"{path}.descending", slot_schema, issues)
        return

    if operator == "group_by":
        if "source" not in expression:
            issues.append(ValidationIssue(path=f"{path}.source", message="Expression group_by requires 'source'"))
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        alias = expression.get("as")
        if alias is not None and (not isinstance(alias, str) or not alias.strip()):
            issues.append(ValidationIssue(path=f"{path}.as", message="Expression alias must be a string"))

        if "key" not in expression:
            issues.append(ValidationIssue(path=f"{path}.key", message="Expression group_by requires 'key'"))
        else:
            _validate_expression_operand(expression["key"], f"{path}.key", slot_schema, issues)

        if "value" in expression:
            _validate_expression_operand(expression["value"], f"{path}.value", slot_schema, issues)
        return

    if operator == "sliding_window":
        if "source" not in expression:
            issues.append(ValidationIssue(path=f"{path}.source", message="Expression sliding_window requires 'source'"))
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        alias = expression.get("as")
        if alias is not None and (not isinstance(alias, str) or not alias.strip()):
            issues.append(ValidationIssue(path=f"{path}.as", message="Expression alias must be a string"))

        if "size" not in expression:
            issues.append(ValidationIssue(path=f"{path}.size", message="Expression sliding_window requires 'size'"))
        else:
            _validate_expression_operand(expression["size"], f"{path}.size", slot_schema, issues)

        if "value" in expression:
            _validate_expression_operand(expression["value"], f"{path}.value", slot_schema, issues)
        return

    if operator == "neighbors_of":
        for key in ("source", "node_index"):
            if key not in expression:
                issues.append(
                    ValidationIssue(
                        path=f"{path}.{key}",
                        message=f"Expression neighbors_of requires '{key}'",
                    )
                )
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "matrix_degrees":
        if "source" not in expression:
            issues.append(
                ValidationIssue(
                    path=f"{path}.source",
                    message="Expression matrix_degrees requires 'source'",
                )
            )
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "connected_components":
        if "source" not in expression:
            issues.append(
                ValidationIssue(
                    path=f"{path}.source",
                    message="Expression connected_components requires 'source'",
                )
            )
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "undirected"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "edge_pairs":
        if "source" not in expression:
            issues.append(
                ValidationIssue(
                    path=f"{path}.source",
                    message="Expression edge_pairs requires 'source'",
                )
            )
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "directed"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "edge_strength_profile":
        if "source" not in expression:
            issues.append(
                ValidationIssue(
                    path=f"{path}.source",
                    message="Expression edge_strength_profile requires 'source'",
                )
            )
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "directed"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "neighborhood_overlap":
        for key in ("source", "left_node_index", "right_node_index"):
            if key not in expression:
                issues.append(
                    ValidationIssue(
                        path=f"{path}.{key}",
                        message=f"Expression neighborhood_overlap requires '{key}'",
                    )
                )
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "reachable_within":
        for key in ("source", "start_node_index", "max_depth"):
            if key not in expression:
                issues.append(
                    ValidationIssue(
                        path=f"{path}.{key}",
                        message=f"Expression reachable_within requires '{key}'",
                    )
                )
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "undirected", "include_start"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "shortest_path":
        for key in ("source", "start_node_index", "target_node_index"):
            if key not in expression:
                issues.append(
                    ValidationIssue(
                        path=f"{path}.{key}",
                        message=f"Expression shortest_path requires '{key}'",
                    )
                )
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "undirected"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "weighted_shortest_path":
        for key in ("source", "start_node_index", "target_node_index"):
            if key not in expression:
                issues.append(
                    ValidationIssue(
                        path=f"{path}.{key}",
                        message=f"Expression weighted_shortest_path requires '{key}'",
                    )
                )
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "undirected", "cost_mode", "cost_power"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "propagate_signal":
        for key in ("source", "seed_nodes", "steps"):
            if key not in expression:
                issues.append(
                    ValidationIssue(
                        path=f"{path}.{key}",
                        message=f"Expression propagate_signal requires '{key}'",
                    )
                )
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)

        for key in (
            "labels",
            "active_value",
            "activation",
            "include_self",
            "undirected",
            "decay",
            "initial_strength",
        ):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "random_walk":
        for key in ("source", "start_node_index", "steps"):
            if key not in expression:
                issues.append(
                    ValidationIssue(
                        path=f"{path}.{key}",
                        message=f"Expression random_walk requires '{key}'",
                    )
                )
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "undirected", "seed"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "flow_profile":
        for key in ("source", "source_nodes", "target_nodes"):
            if key not in expression:
                issues.append(
                    ValidationIssue(
                        path=f"{path}.{key}",
                        message=f"Expression flow_profile requires '{key}'",
                    )
                )
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "undirected"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "triangle_patterns":
        if "source" not in expression:
            issues.append(
                ValidationIssue(
                    path=f"{path}.source",
                    message="Expression triangle_patterns requires 'source'",
                )
            )
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "centrality_profile":
        if "source" not in expression:
            issues.append(
                ValidationIssue(
                    path=f"{path}.source",
                    message="Expression centrality_profile requires 'source'",
                )
            )
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "undirected"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "closeness_profile":
        if "source" not in expression:
            issues.append(
                ValidationIssue(
                    path=f"{path}.source",
                    message="Expression closeness_profile requires 'source'",
                )
            )
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "undirected"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "policy_walk":
        for key in ("source", "start_node_index", "steps"):
            if key not in expression:
                issues.append(
                    ValidationIssue(
                        path=f"{path}.{key}",
                        message=f"Expression policy_walk requires '{key}'",
                    )
                )
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "undirected", "policy"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "weighted_policy_walk":
        for key in ("source", "start_node_index", "steps"):
            if key not in expression:
                issues.append(
                    ValidationIssue(
                        path=f"{path}.{key}",
                        message=f"Expression weighted_policy_walk requires '{key}'",
                    )
                )
                continue
            _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "undirected", "policy", "cost_mode", "cost_power"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "star_patterns":
        if "source" not in expression:
            issues.append(
                ValidationIssue(
                    path=f"{path}.source",
                    message="Expression star_patterns requires 'source'",
                )
            )
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self", "undirected", "min_degree", "max_leaf_degree"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "square_patterns":
        if "source" not in expression:
            issues.append(
                ValidationIssue(
                    path=f"{path}.source",
                    message="Expression square_patterns requires 'source'",
                )
            )
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        for key in ("labels", "active_value", "activation", "include_self"):
            if key in expression:
                _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)
        return

    if operator == "reduce":
        if "source" not in expression:
            issues.append(ValidationIssue(path=f"{path}.source", message="Expression reduce requires 'source'"))
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        for alias_key in ("as", "accumulator_as"):
            alias = expression.get(alias_key)
            if alias is not None and (not isinstance(alias, str) or not alias.strip()):
                issues.append(ValidationIssue(path=f"{path}.{alias_key}", message="Expression alias must be a string"))

        if "initial" not in expression:
            issues.append(ValidationIssue(path=f"{path}.initial", message="Expression reduce requires 'initial'"))
        else:
            _validate_expression_operand(expression["initial"], f"{path}.initial", slot_schema, issues)

        if "value" not in expression:
            issues.append(ValidationIssue(path=f"{path}.value", message="Expression reduce requires 'value'"))
        else:
            _validate_expression_operand(expression["value"], f"{path}.value", slot_schema, issues)
        return

    if operator in {"count", "sum"}:
        if "source" not in expression:
            issues.append(ValidationIssue(path=f"{path}.source", message=f"Expression {operator} requires 'source'"))
        else:
            _validate_expression_operand(expression["source"], f"{path}.source", slot_schema, issues)

        alias = expression.get("as")
        if alias is not None and (not isinstance(alias, str) or not alias.strip()):
            issues.append(ValidationIssue(path=f"{path}.as", message="Expression alias must be a string"))

        if operator == "count" and "where" in expression:
            _validate_expression_operand(expression["where"], f"{path}.where", slot_schema, issues)

        if operator == "sum":
            if "value" not in expression:
                issues.append(ValidationIssue(path=f"{path}.value", message="Expression sum requires 'value'"))
            else:
                _validate_expression_operand(expression["value"], f"{path}.value", slot_schema, issues)
        return

    for key in ("left", "right"):
        if key not in expression:
            issues.append(ValidationIssue(path=f"{path}.{key}", message=f"Expression {operator} requires '{key}'"))
            continue
        _validate_expression_operand(expression[key], f"{path}.{key}", slot_schema, issues)


def _validate_expression_operand(
    operand: Any,
    path: str,
    slot_schema: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
) -> None:
    if isinstance(operand, dict):
        if "$ref" in operand:
            ref_path = operand["$ref"]
            if not isinstance(ref_path, str) or not ref_path.strip():
                issues.append(ValidationIssue(path=f"{path}.$ref", message="Reference must be a string"))
                return
            _validate_reference(ref_path, path, slot_schema, issues)
            return

        if "$expr" in operand:
            expr_value = operand["$expr"]
            if not isinstance(expr_value, dict):
                issues.append(ValidationIssue(path=f"{path}.$expr", message="Expression must be an object"))
                return
            _validate_expression(expr_value, f"{path}.$expr", slot_schema, issues)
            return

        if "op" in operand:
            _validate_expression(operand, path, slot_schema, issues)
            return

        for key, nested in operand.items():
            _validate_expression_operand(nested, f"{path}.{key}", slot_schema, issues)
        return

    if isinstance(operand, list):
        for index, item in enumerate(operand):
            _validate_expression_operand(item, f"{path}[{index}]", slot_schema, issues)
