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
                    "name": "next_strategy",
                    "kind": "object",
                    "representation": "execution_hint",
                    "default": {},
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
                                                        "source": {"$ref": "slots.constructed_solution"},
                                                        "as": "item",
                                                        "where": {
                                                            "op": "and",
                                                            "args": [
                                                                {
                                                                    "op": "eq",
                                                                    "left": {
                                                                        "op": "ref",
                                                                        "path": "vars.item.label",
                                                                    },
                                                                    "right": "critical",
                                                                },
                                                                {
                                                                    "op": "gte",
                                                                    "left": {
                                                                        "op": "ref",
                                                                        "path": "vars.item.connection_count",
                                                                    },
                                                                    "right": 3,
                                                                },
                                                            ],
                                                        },
                                                    },
                                                    2.4,
                                                ],
                                            },
                                            {
                                                "op": "div",
                                                "left": {
                                                    "op": "sum",
                                                    "source": {"$ref": "slots.constructed_solution"},
                                                    "as": "item",
                                                    "value": {
                                                        "op": "ref",
                                                        "path": "vars.item.connection_count",
                                                    },
                                                },
                                                "right": {
                                                    "op": "len",
                                                    "value": {"$ref": "slots.constructed_solution"},
                                                },
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
                            "type": "operator",
                            "name": "apply_intensify_strategy",
                            "operator": "apply_intensify_strategy",
                        },
                        "else": {
                            "type": "operator",
                            "name": "apply_diversify_strategy",
                            "operator": "apply_diversify_strategy",
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
        self.assertEqual(result.get("heuristic_score"), 7.433)
        self.assertEqual(result.get("next_strategy")["phase"], "intensify")
        self.assertEqual(result.get_slot_definition("affinity_matrix").kind, "matrix")

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


if __name__ == "__main__":
    unittest.main()
