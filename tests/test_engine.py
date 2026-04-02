from __future__ import annotations

import unittest

from ballista import (
    Algorithm,
    AlgorithmEngine,
    LoopNode,
    PythonNode,
    SequenceNode,
    SlotDefinition,
    load_algorithm_definition,
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
                        "name": "decide_search_mode",
                        "operator": "decide_search_mode",
                        "params": {
                            "solution": {"$ref": "slots.constructed_solution"},
                            "critical_label": "critical",
                            "critical_threshold": 3,
                            "dense_rows_threshold": 2,
                            "output_slot": "search_mode",
                        },
                    },
                    {
                        "type": "condition",
                        "name": "select_branch",
                        "condition": {
                            "operator": "equals",
                            "left": {"$ref": "slots.search_mode"},
                            "right": "intensify",
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
        self.assertEqual(result.get("next_strategy")["phase"], "intensify")
        self.assertEqual(result.get_slot_definition("affinity_matrix").kind, "matrix")


if __name__ == "__main__":
    unittest.main()
