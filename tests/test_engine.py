from __future__ import annotations

import unittest

from ballista import (
    Algorithm,
    AlgorithmEngine,
    LoopNode,
    PythonNode,
    SequenceNode,
    SlotDefinition,
    assert_valid_algorithm_definition,
    build_editor_contract,
    export_registry_contract,
    find_compatible_slots,
    load_algorithm_definition,
    validate_algorithm_definition,
)
from ballista.examples import build_astro_demo, build_builtin_registry


class EngineTests(unittest.TestCase):
    def test_loop_node_stops_at_max_iterations(self) -> None:
        def increment(context, params) -> None:
            del params
            context.set("counter", context.get("counter", 0) + 1)

        algorithm = Algorithm(
            name="counter",
            root=LoopNode(
                name="loop",
                body=SequenceNode.from_iterable(
                    "body",
                    [
                        PythonNode(
                            name="increment",
                            handler=increment,
                            message="counter incremented",
                        )
                    ],
                ),
                max_iterations=3,
            ),
        )

        result = AlgorithmEngine().run(algorithm)
        self.assertEqual(result.get("counter"), 3)
        self.assertEqual(result.iteration, 3)

    def test_astro_demo_produces_reasonable_best_candidate(self) -> None:
        algorithm, initial_slots = build_astro_demo(seed=11)
        result = AlgorithmEngine().run(algorithm, initial_slots=initial_slots)

        best = result.get("best")
        self.assertIsNotNone(best)
        self.assertLess(best["score"], 1.0)
        self.assertGreater(len(result.history), 0)

    def test_definition_loader_builds_algorithm_from_data(self) -> None:
        definition = {
            "name": "simple_definition",
            "initial_slots": {"rng_seed": 3, "target": 1.0, "population_size": 4},
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "initialize_population",
                        "operator": "initialize_population",
                    }
                ],
            },
        }

        loaded = load_algorithm_definition(definition, build_builtin_registry())
        result = AlgorithmEngine().run(
            loaded.algorithm,
            initial_slots=loaded.initial_slots,
            slot_schema=loaded.slot_schema,
        )

        self.assertEqual(loaded.algorithm.name, "simple_definition")
        self.assertEqual(len(result.get("population")), 4)
        self.assertIn("best_score", result.metrics)

    def test_definition_supports_slot_schema_and_condition_branching(self) -> None:
        definition = {
            "name": "conditional_matrix_definition",
            "slot_definitions": [
                {
                    "name": "affinity_matrix",
                    "kind": "matrix",
                    "representation": "binary",
                    "default": [
                        [1, 1, 1],
                        [0, 1, 0],
                        [1, 1, 1],
                    ],
                },
                {
                    "name": "node_labels",
                    "kind": "mapping",
                    "representation": "tag_map",
                    "default": {"0": "entry", "1": "support", "2": "critical"},
                },
                {
                    "name": "constructed_solution",
                    "kind": "object_collection",
                    "representation": "labeled_graph_view",
                    "default": [],
                },
                {
                    "name": "search_mode",
                    "kind": "scalar",
                    "representation": "strategy_label",
                    "default": "unknown",
                },
                {
                    "name": "heuristic_score",
                    "kind": "scalar",
                    "representation": "formula_score",
                    "default": 0,
                },
                {
                    "name": "priority_nodes",
                    "kind": "object_collection",
                    "representation": "priority_subset",
                    "default": [],
                },
                {
                    "name": "next_strategy",
                    "kind": "object",
                    "representation": "execution_hint",
                    "default": {},
                },
            ],
            "subgraphs": [
                {
                    "name": "strategy_block",
                    "node": {
                        "type": "operator",
                        "name": "materialize_strategy_object",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "next_strategy",
                            "value": {
                                "phase": {"$ref": "args.phase"},
                                "primary_weight": {"$ref": "args.primary_weight"},
                                "bias": {"$ref": "args.bias"},
                            },
                        },
                    },
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "construct_labeled_solution",
                        "operator": "construct_labeled_solution",
                        "params": {
                            "matrix": {"$ref": "slots.affinity_matrix"},
                            "labels": {"$ref": "slots.node_labels"},
                            "output_slot": "constructed_solution",
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_priority_nodes",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "priority_nodes",
                            "value": {
                                "$expr": {
                                    "op": "map",
                                    "source": {
                                        "op": "filter",
                                        "source": {"$ref": "slots.constructed_solution"},
                                        "as": "item",
                                        "where": {
                                            "op": "gte",
                                            "left": {
                                                "op": "ref",
                                                "path": "vars.item.connection_count",
                                            },
                                            "right": 2,
                                        },
                                    },
                                    "as": "item",
                                    "value": {
                                        "node_id": {
                                            "op": "ref",
                                            "path": "vars.item.node_id",
                                        },
                                        "label": {
                                            "op": "ref",
                                            "path": "vars.item.label",
                                        },
                                        "strength": {
                                            "op": "mul",
                                            "args": [
                                                {
                                                    "op": "ref",
                                                    "path": "vars.item.connection_count",
                                                },
                                                1.1,
                                            ],
                                        },
                                    },
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_heuristic_score",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "heuristic_score",
                            "value": {
                                "$expr": {
                                    "op": "round",
                                    "value": {
                                        "op": "add",
                                        "args": [
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {"op": "ref", "path": "metrics.dense_rows"},
                                                    1.35,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "count",
                                                        "source": {"$ref": "slots.priority_nodes"},
                                                        "as": "item",
                                                        "where": {
                                                            "op": "eq",
                                                            "left": {
                                                                "op": "ref",
                                                                "path": "vars.item.label",
                                                            },
                                                            "right": "critical",
                                                        },
                                                    },
                                                    2.4,
                                                ],
                                            },
                                            {
                                                "op": "if",
                                                "condition": {
                                                    "op": "gt",
                                                    "left": {
                                                        "op": "len",
                                                        "value": {"$ref": "slots.priority_nodes"},
                                                    },
                                                    "right": 0,
                                                },
                                                "then": {
                                                    "op": "div",
                                                    "left": {
                                                        "op": "sum",
                                                        "source": {"$ref": "slots.priority_nodes"},
                                                        "as": "item",
                                                        "value": {
                                                            "op": "ref",
                                                            "path": "vars.item.strength",
                                                        },
                                                    },
                                                    "right": {
                                                        "op": "len",
                                                        "value": {"$ref": "slots.priority_nodes"},
                                                    },
                                                },
                                                "else": 0,
                                            },
                                        ],
                                    },
                                    "digits": 3,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_search_mode",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "search_mode",
                            "value": {
                                "$expr": {
                                    "op": "if",
                                    "condition": {
                                        "op": "gte",
                                        "left": {"op": "ref", "path": "slots.heuristic_score"},
                                        "right": 7.0,
                                    },
                                    "then": "intensify",
                                    "else": "diversify",
                                }
                            },
                        },
                    },
                    {
                        "type": "condition",
                        "name": "select_branch",
                        "condition": {
                            "expression": {
                                "op": "eq",
                                "left": {"op": "ref", "path": "slots.search_mode"},
                                "right": "intensify",
                            },
                        },
                        "then": {
                            "type": "subgraph",
                            "name": "run_strategy_block_for_intensify",
                            "ref": "strategy_block",
                            "params": {
                                "phase": "intensify",
                                "primary_weight": 0.9,
                                "bias": "very_high",
                            },
                        },
                        "else": {
                            "type": "subgraph",
                            "name": "run_strategy_block_for_diversify",
                            "ref": "strategy_block",
                            "params": {
                                "phase": "diversify",
                                "primary_weight": 0.6,
                                "bias": "medium",
                            },
                        },
                    },
                ],
            },
        }

        loaded = load_algorithm_definition(definition, build_builtin_registry())
        result = AlgorithmEngine().run(
            loaded.algorithm,
            initial_slots=loaded.initial_slots,
            slot_schema=loaded.slot_schema,
        )

        self.assertIsInstance(loaded.slot_schema["affinity_matrix"], SlotDefinition)
        self.assertEqual(loaded.slot_schema["affinity_matrix"].representation, "binary")
        self.assertEqual(result.get("search_mode"), "intensify")
        self.assertEqual(result.get("heuristic_score"), 8.4)
        self.assertEqual(len(result.get("priority_nodes")), 2)
        self.assertEqual(result.get("priority_nodes")[1]["label"], "critical")
        self.assertEqual(result.get("next_strategy")["phase"], "intensify")
        self.assertEqual(result.get("next_strategy")["primary_weight"], 0.9)
        self.assertEqual(result.get_slot_definition("affinity_matrix").kind, "matrix")

    def test_validator_reports_unknown_subgraph_reference(self) -> None:
        invalid_definition = {
            "name": "invalid_subgraph_definition",
            "root": {
                "type": "subgraph",
                "name": "missing_block",
                "ref": "does_not_exist",
            },
        }

        issues = validate_algorithm_definition(invalid_definition, build_builtin_registry())
        self.assertTrue(any("Unknown subgraph reference" in issue.message for issue in issues))

    def test_validator_reports_incompatible_slot_kind_for_operator_param(self) -> None:
        invalid_definition = {
            "name": "invalid_matrix_flow",
            "slot_definitions": [
                {
                    "name": "affinity_matrix",
                    "kind": "mapping",
                    "representation": "tag_map",
                    "default": {"0": [1, 0, 1]},
                },
                {
                    "name": "node_labels",
                    "kind": "mapping",
                    "representation": "tag_map",
                    "default": {"0": "critical"},
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "construct_labeled_solution",
                        "operator": "construct_labeled_solution",
                        "params": {
                            "matrix": {"$ref": "slots.affinity_matrix"},
                            "labels": {"$ref": "slots.node_labels"},
                        },
                    }
                ],
            },
        }

        issues = validate_algorithm_definition(invalid_definition, build_builtin_registry())
        self.assertTrue(any("expected one of ['matrix']" in issue.message for issue in issues))

        with self.assertRaises(ValueError):
            assert_valid_algorithm_definition(invalid_definition, build_builtin_registry())

    def test_validator_reports_unknown_expression_operator(self) -> None:
        invalid_definition = {
            "name": "invalid_expression_definition",
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_value",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "foo",
                            "value": {"$expr": {"op": "mystery", "left": 1, "right": 2}},
                        },
                    }
                ],
            },
        }

        issues = validate_algorithm_definition(invalid_definition, build_builtin_registry())
        self.assertTrue(any("Unsupported expression operator" in issue.message for issue in issues))

    def test_editor_contract_lists_compatible_slots_for_operator(self) -> None:
        definition = {
            "name": "contract_definition",
            "slot_definitions": [
                {
                    "name": "affinity_matrix",
                    "kind": "matrix",
                    "representation": "binary",
                },
                {
                    "name": "node_labels",
                    "kind": "mapping",
                    "representation": "tag_map",
                },
                {
                    "name": "constructed_solution",
                    "kind": "object_collection",
                    "representation": "labeled_graph_view",
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [],
            },
        }

        registry = build_builtin_registry()
        loaded = load_algorithm_definition(definition, registry)
        contract = build_editor_contract(registry, loaded.slot_schema)

        compatible_slots = contract["compatibility"]["construct_labeled_solution"]["matrix"][
            "compatible_slots"
        ]
        self.assertEqual(compatible_slots[0]["name"], "affinity_matrix")
        self.assertEqual(contract["supported_node_types"], ["operator", "sequence", "loop", "condition", "subgraph"])

    def test_find_compatible_slots_filters_by_kind(self) -> None:
        registry = build_builtin_registry()
        operator_spec = registry.get_operator_spec("construct_labeled_solution")
        matrix_param = operator_spec.params["matrix"]
        slot_schema = {
            "affinity_matrix": SlotDefinition(name="affinity_matrix", kind="matrix", representation="binary"),
            "node_labels": SlotDefinition(name="node_labels", kind="mapping", representation="tag_map"),
        }

        compatible = find_compatible_slots(matrix_param, slot_schema)
        self.assertEqual([item.name for item in compatible], ["affinity_matrix"])

    def test_export_registry_contract_contains_operator_schema(self) -> None:
        contract = export_registry_contract(build_builtin_registry())
        operator_names = [item["name"] for item in contract["operators"]]
        self.assertIn("construct_labeled_solution", operator_names)
        self.assertIn("supported_expression_operators", contract)


if __name__ == "__main__":
    unittest.main()
