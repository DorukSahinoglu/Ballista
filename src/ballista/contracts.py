from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .expression import SUPPORTED_EXPRESSION_OPERATORS
from .models import SlotDefinition
from .registry import OperatorParamSchema, OperatorRegistry, OperatorSpec

SUPPORTED_NODE_TYPES = ["operator", "sequence", "loop", "condition", "subgraph"]
SUPPORTED_REFERENCE_ROOTS = ["slots", "metrics", "schema", "iteration", "args", "vars"]
EXPRESSION_OPERATOR_CATEGORIES = {
    "references_and_logic": {
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
        "assoc",
    },
    "math_and_scoring": {
        "sum",
        "weighted_sum",
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
        "clamp",
        "lerp",
    },
    "history_and_learning": {
        "metric_history",
        "slot_history",
        "trend_profile",
        "frequency_map",
        "pairwise_deltas",
    },
    "collection_transforms": {
        "merge_objects",
        "filter",
        "map",
        "sort_by",
        "group_by",
        "reduce",
        "sliding_window",
        "count",
        "max_by",
        "min_by",
        "concat",
    },
    "graph_and_matrix": {
        "neighbors_of",
        "matrix_degrees",
        "connected_components",
        "edge_pairs",
        "edge_strength_profile",
        "neighborhood_overlap",
        "reachable_within",
        "shortest_path",
        "weighted_shortest_path",
        "propagate_signal",
        "random_walk",
        "flow_profile",
        "triangle_patterns",
        "centrality_profile",
        "closeness_profile",
        "policy_walk",
        "weighted_policy_walk",
        "star_patterns",
        "square_patterns",
    },
}
AUTHORING_STARTER_TEMPLATES = [
    {
        "name": "simple_operator_step",
        "label": "Simple Operator Step",
        "node_type": "operator",
        "template": {
            "type": "operator",
            "name": "set_value",
            "operator": "set_slot_value",
            "params": {"slot": "", "value": None},
        },
    },
    {
        "name": "formula_assignment",
        "label": "Formula Assignment",
        "node_type": "operator",
        "template": {
            "type": "operator",
            "name": "set_formula_value",
            "operator": "set_slot_value",
            "params": {"slot": "", "value": {"$expr": {"op": "add", "args": [0, 0]}}},
        },
    },
    {
        "name": "condition_branch",
        "label": "Condition Branch",
        "node_type": "condition",
        "template": {
            "type": "condition",
            "name": "branch_on_signal",
            "condition": {
                "kind": "comparison",
                "operator": "eq",
                "left": {"$ref": "slots.search_mode"},
                "right": "intensify",
            },
            "then": {"type": "sequence", "name": "then_branch", "steps": []},
            "else": {"type": "sequence", "name": "else_branch", "steps": []},
        },
    },
    {
        "name": "iterative_loop",
        "label": "Iterative Loop",
        "node_type": "loop",
        "template": {
            "type": "loop",
            "name": "main_loop",
            "max_iterations": 10,
            "body": {"type": "sequence", "name": "loop_body", "steps": []},
        },
    },
    {
        "name": "reusable_subgraph",
        "label": "Reusable Subgraph",
        "node_type": "subgraph",
        "template": {
            "type": "subgraph",
            "name": "call_reusable_block",
            "ref": "custom_block",
            "params": {},
        },
    },
]


@dataclass(slots=True)
class CompatibleSlot:
    name: str
    kind: str
    representation: str | None


def export_registry_contract(registry: OperatorRegistry) -> dict[str, Any]:
    return {
        "operators": [_operator_spec_to_contract(spec) for spec in registry.operators.values()],
        "stop_conditions": sorted(registry.stop_conditions.keys()),
        "supported_node_types": list(SUPPORTED_NODE_TYPES),
        "supported_reference_roots": list(SUPPORTED_REFERENCE_ROOTS),
        "supported_expression_operators": sorted(SUPPORTED_EXPRESSION_OPERATORS),
    }


def build_editor_contract(
    registry: OperatorRegistry,
    slot_schema: dict[str, SlotDefinition],
) -> dict[str, Any]:
    base = export_registry_contract(registry)
    base["slot_schema"] = [
        {
            "name": definition.name,
            "kind": definition.kind,
            "representation": definition.representation,
            "metadata": definition.metadata,
        }
        for definition in slot_schema.values()
    ]
    base["compatibility"] = {
        spec.name: _operator_compatibility(spec, slot_schema)
        for spec in registry.operators.values()
    }
    base["authoring"] = {
        "expression_categories": _build_expression_categories(),
        "operator_categories": _build_operator_categories(registry),
        "slot_groups": _build_slot_groups(slot_schema),
        "starter_templates": list(AUTHORING_STARTER_TEMPLATES),
    }
    return base


def find_compatible_slots(
    param_schema: OperatorParamSchema,
    slot_schema: dict[str, SlotDefinition],
) -> list[CompatibleSlot]:
    compatible: list[CompatibleSlot] = []
    for definition in slot_schema.values():
        if param_schema.slot_kinds and definition.kind not in param_schema.slot_kinds:
            continue
        if param_schema.representations and definition.representation not in param_schema.representations:
            continue
        compatible.append(
            CompatibleSlot(
                name=definition.name,
                kind=definition.kind,
                representation=definition.representation,
            )
        )
    return compatible


def _operator_spec_to_contract(spec: OperatorSpec) -> dict[str, Any]:
    return {
        "name": spec.name,
        "description": spec.description,
        "params": [
            {
                "name": param.name,
                "required": param.required,
                "description": param.description,
                "slot_kinds": list(param.slot_kinds),
                "representations": list(param.representations),
            }
            for param in spec.params.values()
        ],
    }


def _operator_compatibility(
    spec: OperatorSpec,
    slot_schema: dict[str, SlotDefinition],
) -> dict[str, Any]:
    compatibility: dict[str, Any] = {}
    for param in spec.params.values():
        compatibility[param.name] = {
            "required": param.required,
            "accepts_any_slot": not param.slot_kinds and not param.representations,
            "compatible_slots": [asdict(item) for item in find_compatible_slots(param, slot_schema)],
        }
    return compatibility


def _build_expression_categories() -> list[dict[str, Any]]:
    categorized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for category_name, operators in EXPRESSION_OPERATOR_CATEGORIES.items():
        names = sorted(operators)
        seen.update(names)
        categorized.append({"name": category_name, "operators": names})

    uncategorized = sorted(SUPPORTED_EXPRESSION_OPERATORS - seen)
    if uncategorized:
        categorized.append({"name": "other", "operators": uncategorized})
    return categorized


def _build_operator_categories(registry: OperatorRegistry) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {
        "core_slots": [],
        "graph_and_matrix": [],
        "population_search": [],
        "constructive_search": [],
        "analysis_and_memory": [],
    }
    for spec in registry.operators.values():
        grouped[_infer_operator_category(spec.name)].append(spec.name)

    return [
        {"name": category, "operators": sorted(names)}
        for category, names in grouped.items()
        if names
    ]


def _build_slot_groups(slot_schema: dict[str, SlotDefinition]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for definition in slot_schema.values():
        grouped.setdefault(definition.kind, []).append(
            {
                "name": definition.name,
                "representation": definition.representation,
                "metadata": definition.metadata,
            }
        )

    return [
        {"kind": kind, "slots": sorted(slots, key=lambda item: item["name"])}
        for kind, slots in sorted(grouped.items())
    ]


def _infer_operator_category(name: str) -> str:
    if name.startswith(("set_", "update_")):
        return "core_slots"
    if any(token in name for token in ("population", "selection", "mutation", "recombine", "accept", "restart")):
        return "population_search"
    if any(token in name for token in ("matrix", "graph", "neighbor", "path", "flow", "signal", "walk")):
        return "graph_and_matrix"
    if any(token in name for token in ("summary", "credit", "blame", "profile", "history")):
        return "analysis_and_memory"
    return "constructive_search"
