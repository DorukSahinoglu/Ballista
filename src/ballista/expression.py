from __future__ import annotations
from copy import deepcopy
from typing import Any

from .models import BallistaContext

SUPPORTED_EXPRESSION_OPERATORS = {
    "ref",
    "if",
    "eq",
    "neq",
    "gt",
    "gte",
    "lt",
    "lte",
    "and",
    "or",
    "not",
    "contains",
    "in",
    "len",
    "get",
    "count",
    "sum",
    "add",
    "sub",
    "mul",
    "div",
    "pow",
    "mod",
    "abs",
    "min",
    "max",
    "avg",
    "round",
}


def evaluate_expression(
    expression: dict[str, Any],
    context: BallistaContext,
    scope: dict[str, Any] | None = None,
) -> Any:
    operator = expression.get("op")
    if not isinstance(operator, str) or operator not in SUPPORTED_EXPRESSION_OPERATORS:
        raise ValueError(f"Unsupported expression operator '{operator}'")

    scope = dict(scope or {})

    if operator == "ref":
        path = expression.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Expression 'ref' requires a non-empty path")
        return resolve_reference(path, context, scope)

    if operator == "if":
        condition = _eval_operand(expression["condition"], context, scope)
        branch_key = "then" if condition else "else"
        return _eval_operand(expression[branch_key], context, scope)

    if operator == "not":
        return not bool(_eval_operand(expression["value"], context, scope))

    if operator in {"and", "or"}:
        args = expression.get("args", [])
        if not isinstance(args, list):
            raise ValueError(f"Expression '{operator}' expects a list of args")
        values = [bool(_eval_operand(arg, context, scope)) for arg in args]
        return all(values) if operator == "and" else any(values)

    if operator == "len":
        return len(_eval_operand(expression["value"], context, scope))

    if operator == "abs":
        return abs(_eval_operand(expression["value"], context, scope))

    if operator == "round":
        value = _eval_operand(expression["value"], context, scope)
        digits = _eval_operand(expression.get("digits", 0), context, scope)
        return round(value, digits)

    if operator == "get":
        source = _eval_operand(expression["source"], context, scope)
        key = _eval_operand(expression["key"], context, scope)
        default = _eval_operand(expression.get("default"), context, scope)
        if isinstance(source, dict):
            return deepcopy(source.get(key, default))
        if isinstance(source, list):
            return deepcopy(source[int(key)])
        return deepcopy(getattr(source, key, default))

    if operator in {"count", "sum"}:
        source = _eval_operand(expression["source"], context, scope)
        alias = expression.get("as", "item")
        if not isinstance(alias, str) or not alias.strip():
            raise ValueError(f"Expression '{operator}' expects a non-empty alias")
        if not isinstance(source, list):
            raise TypeError(f"Expression '{operator}' expects a list source")

        if operator == "count":
            where = expression.get("where")
            if where is None:
                return len(source)

            total = 0
            for index, item in enumerate(source):
                nested_scope = dict(scope)
                nested_scope[alias] = item
                nested_scope["index"] = index
                if bool(_eval_operand(where, context, nested_scope)):
                    total += 1
            return total

        total = 0
        value_expr = expression.get("value")
        for index, item in enumerate(source):
            nested_scope = dict(scope)
            nested_scope[alias] = item
            nested_scope["index"] = index
            total += _eval_operand(value_expr, context, nested_scope)
        return total

    if operator in {"add", "mul", "min", "max", "avg"}:
        args = expression.get("args", [])
        if not isinstance(args, list):
            raise ValueError(f"Expression '{operator}' expects a list of args")
        values = [_eval_operand(arg, context, scope) for arg in args]
        if operator == "add":
            return sum(values)
        if operator == "mul":
            result = 1
            for value in values:
                result *= value
            return result
        if operator == "min":
            return min(values)
        if operator == "max":
            return max(values)
        return sum(values) / len(values)

    left = _eval_operand(expression["left"], context, scope)
    right = _eval_operand(expression["right"], context, scope)

    operations = {
        "eq": lambda a, b: a == b,
        "neq": lambda a, b: a != b,
        "gt": lambda a, b: a > b,
        "gte": lambda a, b: a >= b,
        "lt": lambda a, b: a < b,
        "lte": lambda a, b: a <= b,
        "contains": lambda a, b: b in a,
        "in": lambda a, b: a in b,
        "sub": lambda a, b: a - b,
        "div": lambda a, b: a / b,
        "pow": lambda a, b: a**b,
        "mod": lambda a, b: a % b,
    }
    return operations[operator](left, right)


def resolve_reference(
    reference: str,
    context: BallistaContext,
    scope: dict[str, Any] | None = None,
) -> Any:
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
    elif root == "vars":
        value = dict(scope or {})
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


def _eval_operand(
    operand: Any,
    context: BallistaContext,
    scope: dict[str, Any],
) -> Any:
    if isinstance(operand, dict):
        if "$ref" in operand:
            path = operand["$ref"]
            if not isinstance(path, str):
                raise ValueError("Reference path must be a string")
            return resolve_reference(path, context, scope)

        if "$expr" in operand:
            expression = operand["$expr"]
            if not isinstance(expression, dict):
                raise ValueError("$expr payload must be an object")
            return evaluate_expression(expression, context, scope)

        if "op" in operand:
            return evaluate_expression(operand, context, scope)

        return {key: _eval_operand(value, context, scope) for key, value in operand.items()}

    if isinstance(operand, list):
        return [_eval_operand(item, context, scope) for item in operand]

    return deepcopy(operand)
