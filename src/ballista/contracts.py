from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .expression import SUPPORTED_EXPRESSION_OPERATORS
from .models import SlotDefinition
from .registry import OperatorParamSchema, OperatorRegistry, OperatorSpec

SUPPORTED_NODE_TYPES = ["operator", "sequence", "loop", "condition", "subgraph"]
SUPPORTED_REFERENCE_ROOTS = ["slots", "metrics", "schema", "iteration", "args", "vars"]


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
