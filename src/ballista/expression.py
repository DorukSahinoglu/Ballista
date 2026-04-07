from __future__ import annotations
from copy import deepcopy
import random
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
    "filter",
    "map",
    "sort_by",
    "group_by",
    "reduce",
    "sliding_window",
    "neighbors_of",
    "matrix_degrees",
    "connected_components",
    "edge_pairs",
    "neighborhood_overlap",
    "reachable_within",
    "shortest_path",
    "propagate_signal",
    "random_walk",
    "flow_profile",
    "triangle_patterns",
    "centrality_profile",
    "closeness_profile",
    "policy_walk",
    "star_patterns",
    "square_patterns",
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

    if operator in {"filter", "map"}:
        source = _eval_operand(expression["source"], context, scope)
        alias = expression.get("as", "item")
        if not isinstance(alias, str) or not alias.strip():
            raise ValueError(f"Expression '{operator}' expects a non-empty alias")
        if not isinstance(source, list):
            raise TypeError(f"Expression '{operator}' expects a list source")

        transformed = []
        for index, item in enumerate(source):
            nested_scope = dict(scope)
            nested_scope[alias] = item
            nested_scope["index"] = index

            if operator == "filter":
                if bool(_eval_operand(expression["where"], context, nested_scope)):
                    transformed.append(deepcopy(item))
                continue

            transformed.append(_eval_operand(expression["value"], context, nested_scope))

        return transformed

    if operator == "sort_by":
        source = _eval_operand(expression["source"], context, scope)
        alias = expression.get("as", "item")
        if not isinstance(alias, str) or not alias.strip():
            raise ValueError("Expression 'sort_by' expects a non-empty alias")
        if not isinstance(source, list):
            raise TypeError("Expression 'sort_by' expects a list source")

        keyed_items: list[tuple[Any, Any]] = []
        for index, item in enumerate(source):
            nested_scope = dict(scope)
            nested_scope[alias] = item
            nested_scope["index"] = index
            sort_key = _eval_operand(expression["key"], context, nested_scope)
            keyed_items.append((sort_key, deepcopy(item)))

        descending = bool(_eval_operand(expression.get("descending", False), context, scope))
        keyed_items.sort(key=lambda pair: pair[0], reverse=descending)
        return [item for _, item in keyed_items]

    if operator == "group_by":
        source = _eval_operand(expression["source"], context, scope)
        alias = expression.get("as", "item")
        if not isinstance(alias, str) or not alias.strip():
            raise ValueError("Expression 'group_by' expects a non-empty alias")
        if not isinstance(source, list):
            raise TypeError("Expression 'group_by' expects a list source")

        groups: dict[str, list[Any]] = {}
        for index, item in enumerate(source):
            nested_scope = dict(scope)
            nested_scope[alias] = item
            nested_scope["index"] = index
            key = str(_eval_operand(expression["key"], context, nested_scope))
            value_spec = expression.get("value")
            value = deepcopy(item) if value_spec is None else _eval_operand(value_spec, context, nested_scope)
            groups.setdefault(key, []).append(value)
        return groups

    if operator == "sliding_window":
        source = _eval_operand(expression["source"], context, scope)
        alias = expression.get("as", "window")
        if not isinstance(alias, str) or not alias.strip():
            raise ValueError("Expression 'sliding_window' expects a non-empty alias")
        if not isinstance(source, list):
            raise TypeError("Expression 'sliding_window' expects a list source")

        size = int(_eval_operand(expression["size"], context, scope))
        if size <= 0:
            raise ValueError("Expression 'sliding_window' expects size > 0")

        windows = []
        if len(source) < size:
            return windows

        value_spec = expression.get("value")
        for index in range(len(source) - size + 1):
            window = deepcopy(source[index : index + size])
            nested_scope = dict(scope)
            nested_scope[alias] = window
            nested_scope["index"] = index
            value = window if value_spec is None else _eval_operand(value_spec, context, nested_scope)
            windows.append(value)
        return windows

    if operator == "neighbors_of":
        matrix = _eval_operand(expression["source"], context, scope)
        node_index = int(_eval_operand(expression["node_index"], context, scope))
        labels = _eval_operand(expression.get("labels"), context, scope)
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))

        _ensure_matrix(matrix, "neighbors_of")
        return _build_neighbor_objects(
            matrix=matrix,
            node_index=node_index,
            labels=labels,
            active_value=active_value,
            include_self=include_self,
        )

    if operator == "matrix_degrees":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))

        _ensure_matrix(matrix, "matrix_degrees")

        degree_view = []
        for node_index in range(len(matrix)):
            neighbors = _build_neighbor_objects(
                matrix=matrix,
                node_index=node_index,
                labels=labels,
                active_value=active_value,
                include_self=include_self,
            )
            degree_view.append(
                {
                    "node_id": node_index,
                    "label": _resolve_label(labels, node_index),
                    "degree": len(neighbors),
                    "neighbors": neighbors,
                }
            )
        return degree_view

    if operator == "connected_components":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))
        undirected = bool(_eval_operand(expression.get("undirected", True), context, scope))

        _ensure_matrix(matrix, "connected_components")
        return _build_connected_components(
            matrix=matrix,
            labels=labels,
            active_value=active_value,
            include_self=include_self,
            undirected=undirected,
        )

    if operator == "edge_pairs":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))
        directed = bool(_eval_operand(expression.get("directed", False), context, scope))

        _ensure_matrix(matrix, "edge_pairs")
        return _build_edge_pairs(
            matrix=matrix,
            labels=labels,
            active_value=active_value,
            include_self=include_self,
            directed=directed,
        )

    if operator == "neighborhood_overlap":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        left_node_index = int(_eval_operand(expression["left_node_index"], context, scope))
        right_node_index = int(_eval_operand(expression["right_node_index"], context, scope))
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))

        _ensure_matrix(matrix, "neighborhood_overlap")
        left_neighbors = _build_neighbor_objects(
            matrix=matrix,
            node_index=left_node_index,
            labels=labels,
            active_value=active_value,
            include_self=include_self,
        )
        right_neighbors = _build_neighbor_objects(
            matrix=matrix,
            node_index=right_node_index,
            labels=labels,
            active_value=active_value,
            include_self=include_self,
        )
        left_ids = {item["node_id"] for item in left_neighbors}
        right_ids = {item["node_id"] for item in right_neighbors}
        shared_ids = sorted(left_ids & right_ids)
        union_size = len(left_ids | right_ids)
        return {
            "left_node_id": left_node_index,
            "left_label": _resolve_label(labels, left_node_index),
            "right_node_id": right_node_index,
            "right_label": _resolve_label(labels, right_node_index),
            "shared_neighbors": [
                {
                    "node_id": node_id,
                    "label": _resolve_label(labels, node_id),
                }
                for node_id in shared_ids
            ],
            "overlap_count": len(shared_ids),
            "jaccard": 0.0 if union_size == 0 else len(shared_ids) / union_size,
        }

    if operator == "reachable_within":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        start_node_index = int(_eval_operand(expression["start_node_index"], context, scope))
        max_depth = int(_eval_operand(expression["max_depth"], context, scope))
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))
        undirected = bool(_eval_operand(expression.get("undirected", True), context, scope))
        include_start = bool(_eval_operand(expression.get("include_start", False), context, scope))

        _ensure_matrix(matrix, "reachable_within")
        return _build_reachable_within(
            matrix=matrix,
            labels=labels,
            start_node_index=start_node_index,
            max_depth=max_depth,
            active_value=active_value,
            include_self=include_self,
            undirected=undirected,
            include_start=include_start,
        )

    if operator == "shortest_path":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        start_node_index = int(_eval_operand(expression["start_node_index"], context, scope))
        target_node_index = int(_eval_operand(expression["target_node_index"], context, scope))
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))
        undirected = bool(_eval_operand(expression.get("undirected", True), context, scope))

        _ensure_matrix(matrix, "shortest_path")
        return _build_shortest_path(
            matrix=matrix,
            labels=labels,
            start_node_index=start_node_index,
            target_node_index=target_node_index,
            active_value=active_value,
            include_self=include_self,
            undirected=undirected,
        )

    if operator == "propagate_signal":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        seed_nodes = _eval_operand(expression["seed_nodes"], context, scope)
        steps = int(_eval_operand(expression["steps"], context, scope))
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))
        undirected = bool(_eval_operand(expression.get("undirected", True), context, scope))
        decay = float(_eval_operand(expression.get("decay", 0.5), context, scope))
        initial_strength = float(_eval_operand(expression.get("initial_strength", 1.0), context, scope))

        _ensure_matrix(matrix, "propagate_signal")
        return _build_signal_profile(
            matrix=matrix,
            labels=labels,
            seed_nodes=seed_nodes,
            steps=steps,
            active_value=active_value,
            include_self=include_self,
            undirected=undirected,
            decay=decay,
            initial_strength=initial_strength,
        )

    if operator == "random_walk":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        start_node_index = int(_eval_operand(expression["start_node_index"], context, scope))
        steps = int(_eval_operand(expression["steps"], context, scope))
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))
        undirected = bool(_eval_operand(expression.get("undirected", True), context, scope))
        seed = int(_eval_operand(expression.get("seed", 0), context, scope))

        _ensure_matrix(matrix, "random_walk")
        return _build_random_walk(
            matrix=matrix,
            labels=labels,
            start_node_index=start_node_index,
            steps=steps,
            active_value=active_value,
            include_self=include_self,
            undirected=undirected,
            seed=seed,
        )

    if operator == "flow_profile":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        source_nodes = _eval_operand(expression["source_nodes"], context, scope)
        target_nodes = _eval_operand(expression["target_nodes"], context, scope)
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))
        undirected = bool(_eval_operand(expression.get("undirected", True), context, scope))

        _ensure_matrix(matrix, "flow_profile")
        return _build_flow_profile(
            matrix=matrix,
            labels=labels,
            source_nodes=source_nodes,
            target_nodes=target_nodes,
            active_value=active_value,
            include_self=include_self,
            undirected=undirected,
        )

    if operator == "triangle_patterns":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))

        _ensure_matrix(matrix, "triangle_patterns")
        return _build_triangle_patterns(
            matrix=matrix,
            labels=labels,
            active_value=active_value,
            include_self=include_self,
        )

    if operator == "centrality_profile":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))
        undirected = bool(_eval_operand(expression.get("undirected", True), context, scope))

        _ensure_matrix(matrix, "centrality_profile")
        return _build_centrality_profile(
            matrix=matrix,
            labels=labels,
            active_value=active_value,
            include_self=include_self,
            undirected=undirected,
        )

    if operator == "closeness_profile":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))
        undirected = bool(_eval_operand(expression.get("undirected", True), context, scope))

        _ensure_matrix(matrix, "closeness_profile")
        return _build_closeness_profile(
            matrix=matrix,
            labels=labels,
            active_value=active_value,
            include_self=include_self,
            undirected=undirected,
        )

    if operator == "policy_walk":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        start_node_index = int(_eval_operand(expression["start_node_index"], context, scope))
        steps = int(_eval_operand(expression["steps"], context, scope))
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))
        undirected = bool(_eval_operand(expression.get("undirected", True), context, scope))
        policy = str(_eval_operand(expression.get("policy", "prefer_unvisited"), context, scope))

        _ensure_matrix(matrix, "policy_walk")
        return _build_policy_walk(
            matrix=matrix,
            labels=labels,
            start_node_index=start_node_index,
            steps=steps,
            active_value=active_value,
            include_self=include_self,
            undirected=undirected,
            policy=policy,
        )

    if operator == "star_patterns":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))
        undirected = bool(_eval_operand(expression.get("undirected", True), context, scope))
        min_degree = int(_eval_operand(expression.get("min_degree", 3), context, scope))
        max_leaf_degree = int(_eval_operand(expression.get("max_leaf_degree", 2), context, scope))

        _ensure_matrix(matrix, "star_patterns")
        return _build_star_patterns(
            matrix=matrix,
            labels=labels,
            active_value=active_value,
            include_self=include_self,
            undirected=undirected,
            min_degree=min_degree,
            max_leaf_degree=max_leaf_degree,
        )

    if operator == "square_patterns":
        matrix = _eval_operand(expression["source"], context, scope)
        labels = _eval_operand(expression.get("labels"), context, scope)
        active_value = _eval_operand(expression.get("active_value", 1), context, scope)
        include_self = bool(_eval_operand(expression.get("include_self", False), context, scope))

        _ensure_matrix(matrix, "square_patterns")
        return _build_square_patterns(
            matrix=matrix,
            labels=labels,
            active_value=active_value,
            include_self=include_self,
        )

    if operator == "reduce":
        source = _eval_operand(expression["source"], context, scope)
        item_alias = expression.get("as", "item")
        accumulator_alias = expression.get("accumulator_as", "acc")
        if not isinstance(item_alias, str) or not item_alias.strip():
            raise ValueError("Expression 'reduce' expects a non-empty item alias")
        if not isinstance(accumulator_alias, str) or not accumulator_alias.strip():
            raise ValueError("Expression 'reduce' expects a non-empty accumulator alias")
        if not isinstance(source, list):
            raise TypeError("Expression 'reduce' expects a list source")

        accumulator = _eval_operand(expression["initial"], context, scope)
        value_spec = expression["value"]

        for index, item in enumerate(source):
            nested_scope = dict(scope)
            nested_scope[item_alias] = item
            nested_scope[accumulator_alias] = accumulator
            nested_scope["index"] = index
            accumulator = _eval_operand(value_spec, context, nested_scope)
        return accumulator

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
    elif root == "args":
        value = context.current_args()
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


def _ensure_matrix(matrix: Any, operator: str) -> None:
    if not isinstance(matrix, list) or any(not isinstance(row, list) for row in matrix):
        raise TypeError(f"Expression '{operator}' expects a matrix source")


def _resolve_label(labels: Any, node_index: int) -> Any:
    if isinstance(labels, dict):
        return deepcopy(labels.get(str(node_index), labels.get(node_index)))

    if isinstance(labels, list):
        return deepcopy(labels[node_index])

    return None


def _build_neighbor_objects(
    matrix: list[list[Any]],
    node_index: int,
    labels: Any,
    active_value: Any,
    include_self: bool,
) -> list[dict[str, Any]]:
    if node_index < 0 or node_index >= len(matrix):
        raise IndexError(f"Node index '{node_index}' is out of range for matrix")

    neighbors = []
    for target_index, edge_value in enumerate(matrix[node_index]):
        if edge_value != active_value:
            continue
        if not include_self and target_index == node_index:
            continue
        neighbors.append(
            {
                "node_id": target_index,
                "label": _resolve_label(labels, target_index),
                "edge_value": deepcopy(edge_value),
            }
        )
    return neighbors


def _build_edge_pairs(
    matrix: list[list[Any]],
    labels: Any,
    active_value: Any,
    include_self: bool,
    directed: bool,
) -> list[dict[str, Any]]:
    edges = []
    seen_pairs: set[tuple[int, int]] = set()

    for source_index, row in enumerate(matrix):
        for target_index, edge_value in enumerate(row):
            if edge_value != active_value:
                continue
            if not include_self and source_index == target_index:
                continue

            pair_key = (source_index, target_index)
            if not directed:
                pair_key = tuple(sorted(pair_key))
                if pair_key in seen_pairs:
                    continue

            seen_pairs.add(pair_key)
            edges.append(
                {
                    "source_id": source_index,
                    "source_label": _resolve_label(labels, source_index),
                    "target_id": target_index,
                    "target_label": _resolve_label(labels, target_index),
                    "edge_value": deepcopy(edge_value),
                }
            )

    return edges


def _build_connected_components(
    matrix: list[list[Any]],
    labels: Any,
    active_value: Any,
    include_self: bool,
    undirected: bool,
) -> list[dict[str, Any]]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=undirected,
    )
    visited: set[int] = set()
    components = []

    for node_index in range(len(matrix)):
        if node_index in visited:
            continue

        stack = [node_index]
        component_nodes = []
        visited.add(node_index)

        while stack:
            current = stack.pop()
            component_nodes.append(current)
            for neighbor_index in sorted(adjacency[current]):
                if neighbor_index in visited:
                    continue
                visited.add(neighbor_index)
                stack.append(neighbor_index)

        component_nodes.sort()
        components.append(
            {
                "component_id": len(components),
                "node_ids": component_nodes,
                "labels": [_resolve_label(labels, index) for index in component_nodes],
                "size": len(component_nodes),
            }
        )

    return components


def _build_adjacency(
    matrix: list[list[Any]],
    active_value: Any,
    include_self: bool,
    undirected: bool,
) -> dict[int, set[int]]:
    adjacency = {index: set() for index in range(len(matrix))}
    for source_index, row in enumerate(matrix):
        for target_index, edge_value in enumerate(row):
            if edge_value != active_value:
                continue
            if not include_self and source_index == target_index:
                continue
            adjacency[source_index].add(target_index)
            if undirected:
                adjacency[target_index].add(source_index)
    return adjacency


def _build_reachable_within(
    matrix: list[list[Any]],
    labels: Any,
    start_node_index: int,
    max_depth: int,
    active_value: Any,
    include_self: bool,
    undirected: bool,
    include_start: bool,
) -> list[dict[str, Any]]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=undirected,
    )
    _validate_node_index(start_node_index, matrix)

    if max_depth < 0:
        raise ValueError("reachable_within expects max_depth >= 0")

    visited_depths = {start_node_index: 0}
    queue: list[tuple[int, int]] = [(start_node_index, 0)]

    while queue:
        node_index, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        for neighbor_index in sorted(adjacency[node_index]):
            next_depth = depth + 1
            if neighbor_index in visited_depths and visited_depths[neighbor_index] <= next_depth:
                continue
            visited_depths[neighbor_index] = next_depth
            queue.append((neighbor_index, next_depth))

    reachable = []
    for node_index, depth in sorted(visited_depths.items(), key=lambda item: (item[1], item[0])):
        if not include_start and node_index == start_node_index:
            continue
        reachable.append(
            {
                "node_id": node_index,
                "label": _resolve_label(labels, node_index),
                "depth": depth,
            }
        )
    return reachable


def _build_shortest_path(
    matrix: list[list[Any]],
    labels: Any,
    start_node_index: int,
    target_node_index: int,
    active_value: Any,
    include_self: bool,
    undirected: bool,
) -> dict[str, Any]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=undirected,
    )
    _validate_node_index(start_node_index, matrix)
    _validate_node_index(target_node_index, matrix)

    path_node_ids = _find_shortest_path_node_ids(adjacency, start_node_index, target_node_index)
    if path_node_ids is None:
        return {
            "start_node_id": start_node_index,
            "start_label": _resolve_label(labels, start_node_index),
            "target_node_id": target_node_index,
            "target_label": _resolve_label(labels, target_node_index),
            "reachable": False,
            "length": None,
            "node_ids": [],
            "labels": [],
        }

    return {
        "start_node_id": start_node_index,
        "start_label": _resolve_label(labels, start_node_index),
        "target_node_id": target_node_index,
        "target_label": _resolve_label(labels, target_node_index),
        "reachable": True,
        "length": len(path_node_ids) - 1,
        "node_ids": path_node_ids,
        "labels": [_resolve_label(labels, index) for index in path_node_ids],
    }


def _build_signal_profile(
    matrix: list[list[Any]],
    labels: Any,
    seed_nodes: Any,
    steps: int,
    active_value: Any,
    include_self: bool,
    undirected: bool,
    decay: float,
    initial_strength: float,
) -> list[dict[str, Any]]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=undirected,
    )
    normalized_seed_nodes = _normalize_seed_nodes(seed_nodes)
    scores = {node_index: 0.0 for node_index in range(len(matrix))}
    frontier: dict[int, float] = {}

    for node_index in normalized_seed_nodes:
        _validate_node_index(node_index, matrix)
        scores[node_index] += initial_strength
        frontier[node_index] = frontier.get(node_index, 0.0) + initial_strength

    if steps < 0:
        raise ValueError("propagate_signal expects steps >= 0")

    for _ in range(steps):
        next_frontier: dict[int, float] = {}
        for node_index, current_score in frontier.items():
            propagated_score = current_score * decay
            if propagated_score == 0:
                continue
            for neighbor_index in adjacency[node_index]:
                next_frontier[neighbor_index] = next_frontier.get(neighbor_index, 0.0) + propagated_score
        for node_index, propagated_score in next_frontier.items():
            scores[node_index] += propagated_score
        frontier = next_frontier

    profile = []
    for node_index, score in sorted(scores.items(), key=lambda item: (-item[1], item[0])):
        if score == 0:
            continue
        profile.append(
            {
                "node_id": node_index,
                "label": _resolve_label(labels, node_index),
                "score": round(score, 6),
            }
        )
    return profile


def _validate_node_index(node_index: int, matrix: list[list[Any]]) -> None:
    if node_index < 0 or node_index >= len(matrix):
        raise IndexError(f"Node index '{node_index}' is out of range for matrix")


def _normalize_seed_nodes(seed_nodes: Any) -> list[int]:
    if isinstance(seed_nodes, list):
        return [int(item) for item in seed_nodes]
    return [int(seed_nodes)]


def _build_random_walk(
    matrix: list[list[Any]],
    labels: Any,
    start_node_index: int,
    steps: int,
    active_value: Any,
    include_self: bool,
    undirected: bool,
    seed: int,
) -> dict[str, Any]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=undirected,
    )
    _validate_node_index(start_node_index, matrix)
    if steps < 0:
        raise ValueError("random_walk expects steps >= 0")

    rng = random.Random(seed)
    current = start_node_index
    trace = [current]
    visit_counts = {current: 1}
    stopped_early = False

    for _ in range(steps):
        neighbors = sorted(adjacency[current])
        if not neighbors:
            stopped_early = True
            break
        current = rng.choice(neighbors)
        trace.append(current)
        visit_counts[current] = visit_counts.get(current, 0) + 1

    return {
        "start_node_id": start_node_index,
        "start_label": _resolve_label(labels, start_node_index),
        "trace": [
            {"node_id": node_index, "label": _resolve_label(labels, node_index)}
            for node_index in trace
        ],
        "visit_counts": [
            {
                "node_id": node_index,
                "label": _resolve_label(labels, node_index),
                "count": count,
            }
            for node_index, count in sorted(visit_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "stopped_early": stopped_early,
    }


def _build_flow_profile(
    matrix: list[list[Any]],
    labels: Any,
    source_nodes: Any,
    target_nodes: Any,
    active_value: Any,
    include_self: bool,
    undirected: bool,
) -> dict[str, Any]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=undirected,
    )
    normalized_sources = _normalize_seed_nodes(source_nodes)
    normalized_targets = _normalize_seed_nodes(target_nodes)
    node_loads: dict[int, int] = {}
    edge_loads: dict[tuple[int, int], int] = {}
    path_summaries = []
    successful_path_count = 0

    for source_node in normalized_sources:
        _validate_node_index(source_node, matrix)
        for target_node in normalized_targets:
            _validate_node_index(target_node, matrix)
            path_node_ids = _find_shortest_path_node_ids(adjacency, source_node, target_node)
            if path_node_ids is None:
                path_summaries.append(
                    {
                        "source_id": source_node,
                        "source_label": _resolve_label(labels, source_node),
                        "target_id": target_node,
                        "target_label": _resolve_label(labels, target_node),
                        "reachable": False,
                        "length": None,
                        "node_ids": [],
                    }
                )
                continue

            successful_path_count += 1
            for node_index in path_node_ids:
                node_loads[node_index] = node_loads.get(node_index, 0) + 1
            for left_node, right_node in zip(path_node_ids, path_node_ids[1:]):
                edge_key = (left_node, right_node) if not undirected else tuple(sorted((left_node, right_node)))
                edge_loads[edge_key] = edge_loads.get(edge_key, 0) + 1

            path_summaries.append(
                {
                    "source_id": source_node,
                    "source_label": _resolve_label(labels, source_node),
                    "target_id": target_node,
                    "target_label": _resolve_label(labels, target_node),
                    "reachable": True,
                    "length": len(path_node_ids) - 1,
                    "node_ids": path_node_ids,
                }
            )

    return {
        "pair_count": len(normalized_sources) * len(normalized_targets),
        "successful_path_count": successful_path_count,
        "paths": path_summaries,
        "node_loads": [
            {
                "node_id": node_index,
                "label": _resolve_label(labels, node_index),
                "load": load,
            }
            for node_index, load in sorted(node_loads.items(), key=lambda item: (-item[1], item[0]))
        ],
        "edge_loads": [
            {
                "source_id": edge_key[0],
                "source_label": _resolve_label(labels, edge_key[0]),
                "target_id": edge_key[1],
                "target_label": _resolve_label(labels, edge_key[1]),
                "load": load,
            }
            for edge_key, load in sorted(edge_loads.items(), key=lambda item: (-item[1], item[0]))
        ],
    }


def _build_triangle_patterns(
    matrix: list[list[Any]],
    labels: Any,
    active_value: Any,
    include_self: bool,
) -> list[dict[str, Any]]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=True,
    )
    triangles = []
    node_count = len(matrix)
    for first in range(node_count):
        for second in range(first + 1, node_count):
            if second not in adjacency[first]:
                continue
            for third in range(second + 1, node_count):
                if third in adjacency[first] and third in adjacency[second]:
                    node_ids = [first, second, third]
                    triangles.append(
                        {
                            "node_ids": node_ids,
                            "labels": [_resolve_label(labels, node_index) for node_index in node_ids],
                        }
                    )
    return triangles


def _find_shortest_path_node_ids(
    adjacency: dict[int, set[int]],
    start_node_index: int,
    target_node_index: int,
) -> list[int] | None:
    queue = [start_node_index]
    parents = {start_node_index: None}

    while queue:
        node_index = queue.pop(0)
        if node_index == target_node_index:
            break
        for neighbor_index in sorted(adjacency[node_index]):
            if neighbor_index in parents:
                continue
            parents[neighbor_index] = node_index
            queue.append(neighbor_index)

    if target_node_index not in parents:
        return None

    path_node_ids = []
    cursor = target_node_index
    while cursor is not None:
        path_node_ids.append(cursor)
        cursor = parents[cursor]
    path_node_ids.reverse()
    return path_node_ids


def _build_centrality_profile(
    matrix: list[list[Any]],
    labels: Any,
    active_value: Any,
    include_self: bool,
    undirected: bool,
) -> list[dict[str, Any]]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=undirected,
    )
    denominator = max(len(matrix) - 1, 1)
    profile = []

    for node_index in range(len(matrix)):
        degree = len(adjacency[node_index])
        profile.append(
            {
                "node_id": node_index,
                "label": _resolve_label(labels, node_index),
                "degree": degree,
                "score": round(degree / denominator, 6),
            }
        )

    profile.sort(key=lambda item: (-item["score"], item["node_id"]))
    return profile


def _build_closeness_profile(
    matrix: list[list[Any]],
    labels: Any,
    active_value: Any,
    include_self: bool,
    undirected: bool,
) -> list[dict[str, Any]]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=undirected,
    )
    profile = []
    node_count = len(matrix)

    for node_index in range(node_count):
        distances = _breadth_first_distances(adjacency, node_index)
        reachable_distances = [distance for target, distance in distances.items() if target != node_index]
        total_distance = sum(reachable_distances)
        reachable_count = len(reachable_distances)
        score = 0.0
        if total_distance > 0 and reachable_count > 0:
            score = reachable_count / total_distance
        profile.append(
            {
                "node_id": node_index,
                "label": _resolve_label(labels, node_index),
                "reachable_count": reachable_count,
                "score": round(score, 6),
            }
        )

    profile.sort(key=lambda item: (-item["score"], item["node_id"]))
    return profile


def _build_policy_walk(
    matrix: list[list[Any]],
    labels: Any,
    start_node_index: int,
    steps: int,
    active_value: Any,
    include_self: bool,
    undirected: bool,
    policy: str,
) -> dict[str, Any]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=undirected,
    )
    _validate_node_index(start_node_index, matrix)
    if steps < 0:
        raise ValueError("policy_walk expects steps >= 0")

    supported_policies = {
        "prefer_unvisited",
        "prefer_high_degree",
        "prefer_low_degree",
        "prefer_central",
    }
    if policy not in supported_policies:
        raise ValueError(f"Unsupported policy_walk policy '{policy}'")

    current = start_node_index
    trace = [current]
    visit_counts = {current: 1}
    stopped_early = False

    for _ in range(steps):
        neighbors = sorted(adjacency[current])
        if not neighbors:
            stopped_early = True
            break

        current = _select_policy_walk_neighbor(
            neighbors=neighbors,
            adjacency=adjacency,
            visit_counts=visit_counts,
            policy=policy,
            closeness_scores=_build_closeness_score_map(adjacency),
        )
        trace.append(current)
        visit_counts[current] = visit_counts.get(current, 0) + 1

    return {
        "start_node_id": start_node_index,
        "start_label": _resolve_label(labels, start_node_index),
        "policy": policy,
        "trace": [
            {"node_id": node_index, "label": _resolve_label(labels, node_index)}
            for node_index in trace
        ],
        "visit_counts": [
            {
                "node_id": node_index,
                "label": _resolve_label(labels, node_index),
                "count": count,
            }
            for node_index, count in sorted(visit_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "unique_visits": len(visit_counts),
        "stopped_early": stopped_early,
    }


def _select_policy_walk_neighbor(
    neighbors: list[int],
    adjacency: dict[int, set[int]],
    visit_counts: dict[int, int],
    policy: str,
    closeness_scores: dict[int, float],
) -> int:
    if policy == "prefer_central":
        return min(
            neighbors,
            key=lambda item: (
                -closeness_scores.get(item, 0.0),
                visit_counts.get(item, 0),
                -len(adjacency[item]),
                item,
            ),
        )

    if policy == "prefer_high_degree":
        return min(neighbors, key=lambda item: (-len(adjacency[item]), visit_counts.get(item, 0), item))

    if policy == "prefer_low_degree":
        return min(neighbors, key=lambda item: (len(adjacency[item]), visit_counts.get(item, 0), item))

    return min(
        neighbors,
        key=lambda item: (
            visit_counts.get(item, 0) > 0,
            visit_counts.get(item, 0),
            -len(adjacency[item]),
            item,
        ),
    )


def _build_star_patterns(
    matrix: list[list[Any]],
    labels: Any,
    active_value: Any,
    include_self: bool,
    undirected: bool,
    min_degree: int,
    max_leaf_degree: int,
) -> list[dict[str, Any]]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=undirected,
    )
    patterns = []

    for node_index in range(len(matrix)):
        degree = len(adjacency[node_index])
        if degree < min_degree:
            continue

        leaf_ids = [
            neighbor_index
            for neighbor_index in sorted(adjacency[node_index])
            if len(adjacency[neighbor_index]) <= max_leaf_degree
        ]
        if len(leaf_ids) < min_degree:
            continue

        patterns.append(
            {
                "center_id": node_index,
                "center_label": _resolve_label(labels, node_index),
                "degree": degree,
                "leaf_ids": leaf_ids,
                "leaf_labels": [_resolve_label(labels, leaf_id) for leaf_id in leaf_ids],
                "size": 1 + len(leaf_ids),
            }
        )

    return patterns


def _build_square_patterns(
    matrix: list[list[Any]],
    labels: Any,
    active_value: Any,
    include_self: bool,
) -> list[dict[str, Any]]:
    adjacency = _build_adjacency(
        matrix=matrix,
        active_value=active_value,
        include_self=include_self,
        undirected=True,
    )
    seen: set[tuple[int, int, int, int]] = set()
    patterns = []
    node_count = len(matrix)

    for first in range(node_count):
        for second in adjacency[first]:
            if second <= first:
                continue
            for third in adjacency[second]:
                if third in {first, second}:
                    continue
                for fourth in adjacency[third]:
                    if fourth in {first, second, third}:
                        continue
                    if first not in adjacency[fourth]:
                        continue
                    node_ids = tuple(sorted((first, second, third, fourth)))
                    if node_ids in seen:
                        continue
                    seen.add(node_ids)
                    patterns.append(
                        {
                            "node_ids": list(node_ids),
                            "labels": [_resolve_label(labels, node_index) for node_index in node_ids],
                        }
                    )

    patterns.sort(key=lambda item: item["node_ids"])
    return patterns


def _breadth_first_distances(
    adjacency: dict[int, set[int]],
    start_node_index: int,
) -> dict[int, int]:
    distances = {start_node_index: 0}
    queue: list[int] = [start_node_index]

    while queue:
        node_index = queue.pop(0)
        for neighbor_index in sorted(adjacency[node_index]):
            if neighbor_index in distances:
                continue
            distances[neighbor_index] = distances[node_index] + 1
            queue.append(neighbor_index)

    return distances


def _build_closeness_score_map(adjacency: dict[int, set[int]]) -> dict[int, float]:
    scores = {}
    for node_index in adjacency:
        distances = _breadth_first_distances(adjacency, node_index)
        reachable_distances = [distance for target, distance in distances.items() if target != node_index]
        total_distance = sum(reachable_distances)
        reachable_count = len(reachable_distances)
        scores[node_index] = 0.0 if total_distance == 0 or reachable_count == 0 else reachable_count / total_distance
    return scores
