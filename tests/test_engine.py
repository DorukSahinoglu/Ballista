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
                    "name": "degree_view",
                    "kind": "object_collection",
                    "representation": "graph_degree_profile",
                    "default": [],
                },
                {
                    "name": "critical_neighbors",
                    "kind": "object_collection",
                    "representation": "neighbor_subset",
                    "default": [],
                },
                {
                    "name": "connected_components",
                    "kind": "object_collection",
                    "representation": "component_view",
                    "default": [],
                },
                {
                    "name": "edge_pairs",
                    "kind": "object_collection",
                    "representation": "edge_pair_view",
                    "default": [],
                },
                {
                    "name": "critical_entry_overlap",
                    "kind": "object",
                    "representation": "overlap_profile",
                    "default": {},
                },
                {
                    "name": "critical_reach",
                    "kind": "object_collection",
                    "representation": "multi_hop_reach",
                    "default": [],
                },
                {
                    "name": "entry_to_explorer_path",
                    "kind": "object",
                    "representation": "path_profile",
                    "default": {},
                },
                {
                    "name": "critical_signal_profile",
                    "kind": "object_collection",
                    "representation": "signal_profile",
                    "default": [],
                },
                {
                    "name": "critical_random_walk",
                    "kind": "object",
                    "representation": "walk_profile",
                    "default": {},
                },
                {
                    "name": "entry_flow_profile",
                    "kind": "object",
                    "representation": "flow_profile",
                    "default": {},
                },
                {
                    "name": "triangle_patterns",
                    "kind": "object_collection",
                    "representation": "triangle_pattern",
                    "default": [],
                },
                {
                    "name": "centrality_profile",
                    "kind": "object_collection",
                    "representation": "centrality_profile",
                    "default": [],
                },
                {
                    "name": "critical_policy_walk",
                    "kind": "object",
                    "representation": "policy_walk_profile",
                    "default": {},
                },
                {
                    "name": "closeness_profile",
                    "kind": "object_collection",
                    "representation": "closeness_profile",
                    "default": [],
                },
                {
                    "name": "square_patterns",
                    "kind": "object_collection",
                    "representation": "square_pattern",
                    "default": [],
                },
                {
                    "name": "star_patterns",
                    "kind": "object_collection",
                    "representation": "star_pattern",
                    "default": [],
                },
                {
                    "name": "ranked_priority_nodes",
                    "kind": "object_collection",
                    "representation": "ranked_subset",
                    "default": [],
                },
                {
                    "name": "priority_groups",
                    "kind": "mapping",
                    "representation": "grouped_subset",
                    "default": {},
                },
                {
                    "name": "priority_summary",
                    "kind": "object",
                    "representation": "reduced_summary",
                    "default": {},
                },
                {
                    "name": "window_profiles",
                    "kind": "object_collection",
                    "representation": "window_profile",
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
                        "name": "set_degree_view",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "degree_view",
                            "value": {
                                "$expr": {
                                    "op": "matrix_degrees",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "active_value": 1,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_critical_neighbors",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "critical_neighbors",
                            "value": {
                                "$expr": {
                                    "op": "neighbors_of",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "node_index": 2,
                                    "active_value": 1,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_connected_components",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "connected_components",
                            "value": {
                                "$expr": {
                                    "op": "connected_components",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "active_value": 1,
                                    "undirected": True,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_edge_pairs",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "edge_pairs",
                            "value": {
                                "$expr": {
                                    "op": "edge_pairs",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "active_value": 1,
                                    "directed": False,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_critical_entry_overlap",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "critical_entry_overlap",
                            "value": {
                                "$expr": {
                                    "op": "neighborhood_overlap",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "left_node_index": 2,
                                    "right_node_index": 0,
                                    "active_value": 1,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_critical_reach",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "critical_reach",
                            "value": {
                                "$expr": {
                                    "op": "reachable_within",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "start_node_index": 2,
                                    "max_depth": 2,
                                    "active_value": 1,
                                    "undirected": True,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_entry_to_explorer_path",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "entry_to_explorer_path",
                            "value": {
                                "$expr": {
                                    "op": "shortest_path",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "start_node_index": 0,
                                    "target_node_index": 2,
                                    "active_value": 1,
                                    "undirected": True,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_critical_signal_profile",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "critical_signal_profile",
                            "value": {
                                "$expr": {
                                    "op": "propagate_signal",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "seed_nodes": [2],
                                    "steps": 2,
                                    "active_value": 1,
                                    "undirected": True,
                                    "decay": 0.55,
                                    "initial_strength": 1.0,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_critical_random_walk",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "critical_random_walk",
                            "value": {
                                "$expr": {
                                    "op": "random_walk",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "start_node_index": 2,
                                    "steps": 4,
                                    "active_value": 1,
                                    "undirected": True,
                                    "seed": 17,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_entry_flow_profile",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "entry_flow_profile",
                            "value": {
                                "$expr": {
                                    "op": "flow_profile",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "source_nodes": [0],
                                    "target_nodes": [1, 2],
                                    "active_value": 1,
                                    "undirected": True,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_triangle_patterns",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "triangle_patterns",
                            "value": {
                                "$expr": {
                                    "op": "triangle_patterns",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "active_value": 1,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_centrality_profile",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "centrality_profile",
                            "value": {
                                "$expr": {
                                    "op": "centrality_profile",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "active_value": 1,
                                    "undirected": True,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_closeness_profile",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "closeness_profile",
                            "value": {
                                "$expr": {
                                    "op": "closeness_profile",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "active_value": 1,
                                    "undirected": True,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_critical_policy_walk",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "critical_policy_walk",
                            "value": {
                                "$expr": {
                                    "op": "policy_walk",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "start_node_index": 2,
                                    "steps": 4,
                                    "active_value": 1,
                                    "undirected": True,
                                    "policy": "prefer_central",
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_square_patterns",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "square_patterns",
                            "value": {
                                "$expr": {
                                    "op": "square_patterns",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "active_value": 1,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_star_patterns",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "star_patterns",
                            "value": {
                                "$expr": {
                                    "op": "star_patterns",
                                    "source": {"$ref": "slots.affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "active_value": 1,
                                    "undirected": True,
                                    "min_degree": 3,
                                    "max_leaf_degree": 3,
                                }
                            },
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
                        "name": "set_priority_groups",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "priority_groups",
                            "value": {
                                "$expr": {
                                    "op": "group_by",
                                    "source": {"$ref": "slots.priority_nodes"},
                                    "as": "item",
                                    "key": {
                                        "op": "ref",
                                        "path": "vars.item.label",
                                    },
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_ranked_priority_nodes",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "ranked_priority_nodes",
                            "value": {
                                "$expr": {
                                    "op": "sort_by",
                                    "source": {"$ref": "slots.priority_nodes"},
                                    "as": "item",
                                    "key": {
                                        "op": "ref",
                                        "path": "vars.item.strength",
                                    },
                                    "descending": True,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_priority_summary",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "priority_summary",
                            "value": {
                                "$expr": {
                                    "op": "reduce",
                                    "source": {"$ref": "slots.priority_nodes"},
                                    "as": "item",
                                    "accumulator_as": "acc",
                                    "initial": {
                                        "total_strength": 0,
                                        "critical_count": 0,
                                        "total_nodes": 0,
                                        "avg_strength": 0,
                                    },
                                    "value": {
                                        "total_strength": {
                                            "op": "add",
                                            "args": [
                                                {"op": "ref", "path": "vars.acc.total_strength"},
                                                {"op": "ref", "path": "vars.item.strength"},
                                            ],
                                        },
                                        "critical_count": {
                                            "op": "add",
                                            "args": [
                                                {"op": "ref", "path": "vars.acc.critical_count"},
                                                {
                                                    "op": "if",
                                                    "condition": {
                                                        "op": "eq",
                                                        "left": {
                                                            "op": "ref",
                                                            "path": "vars.item.label",
                                                        },
                                                        "right": "critical",
                                                    },
                                                    "then": 1,
                                                    "else": 0,
                                                },
                                            ],
                                        },
                                        "total_nodes": {
                                            "op": "add",
                                            "args": [
                                                {"op": "ref", "path": "vars.acc.total_nodes"},
                                                1,
                                            ],
                                        },
                                        "avg_strength": {
                                            "op": "div",
                                            "left": {
                                                "op": "add",
                                                "args": [
                                                    {"op": "ref", "path": "vars.acc.total_strength"},
                                                    {"op": "ref", "path": "vars.item.strength"},
                                                ],
                                            },
                                            "right": {
                                                "op": "add",
                                                "args": [
                                                    {"op": "ref", "path": "vars.acc.total_nodes"},
                                                    1,
                                                ],
                                            },
                                        },
                                    },
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_window_profiles",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "window_profiles",
                            "value": {
                                "$expr": {
                                    "op": "sliding_window",
                                    "source": {"$ref": "slots.ranked_priority_nodes"},
                                    "size": 2,
                                    "as": "window",
                                    "value": {
                                        "labels": {
                                            "op": "map",
                                            "source": {"op": "ref", "path": "vars.window"},
                                            "as": "item",
                                            "value": {
                                                "op": "ref",
                                                "path": "vars.item.label",
                                            },
                                        },
                                        "combined_strength": {
                                            "op": "sum",
                                            "source": {"op": "ref", "path": "vars.window"},
                                            "as": "item",
                                            "value": {
                                                "op": "ref",
                                                "path": "vars.item.strength",
                                            },
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
                                                    {"op": "ref", "path": "slots.priority_summary.critical_count"},
                                                    2.4,
                                                ],
                                            },
                                            {"op": "ref", "path": "slots.priority_summary.avg_strength"},
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "reduce",
                                                        "source": {"$ref": "slots.connected_components"},
                                                        "as": "item",
                                                        "accumulator_as": "acc",
                                                        "initial": 0,
                                                        "value": {
                                                            "op": "if",
                                                            "condition": {
                                                                "op": "gt",
                                                                "left": {
                                                                    "op": "ref",
                                                                    "path": "vars.item.size",
                                                                },
                                                                "right": {
                                                                    "op": "ref",
                                                                    "path": "vars.acc",
                                                                },
                                                            },
                                                            "then": {
                                                                "op": "ref",
                                                                "path": "vars.item.size",
                                                            },
                                                            "else": {
                                                                "op": "ref",
                                                                "path": "vars.acc",
                                                            },
                                                        },
                                                    },
                                                    0.5,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "len",
                                                        "value": {"$ref": "slots.critical_neighbors"},
                                                    },
                                                    0.8,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "ref",
                                                        "path": "slots.critical_entry_overlap.overlap_count",
                                                    },
                                                    0.7,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "len",
                                                        "value": {"$ref": "slots.critical_reach"},
                                                    },
                                                    0.4,
                                                ],
                                            },
                                            {
                                                "op": "if",
                                                "condition": {
                                                    "op": "ref",
                                                    "path": "slots.entry_to_explorer_path.reachable",
                                                },
                                                "then": 1.2,
                                                "else": 0,
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "sum",
                                                        "source": {"$ref": "slots.critical_signal_profile"},
                                                        "as": "item",
                                                        "value": {
                                                            "op": "ref",
                                                            "path": "vars.item.score",
                                                        },
                                                    },
                                                    0.3,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "ref",
                                                        "path": "slots.closeness_profile.0.score",
                                                    },
                                                    0.85,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "len",
                                                        "value": {"$ref": "slots.square_patterns"},
                                                    },
                                                    0.65,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "ref",
                                                        "path": "slots.centrality_profile.0.score",
                                                    },
                                                    0.75,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "ref",
                                                        "path": "slots.critical_policy_walk.unique_visits",
                                                    },
                                                    0.35,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "len",
                                                        "value": {"$ref": "slots.star_patterns"},
                                                    },
                                                    0.5,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "len",
                                                        "value": {"$ref": "slots.critical_random_walk.trace"},
                                                    },
                                                    0.25,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "ref",
                                                        "path": "slots.entry_flow_profile.successful_path_count",
                                                    },
                                                    0.6,
                                                ],
                                            },
                                            {
                                                "op": "mul",
                                                "args": [
                                                    {
                                                        "op": "len",
                                                        "value": {"$ref": "slots.triangle_patterns"},
                                                    },
                                                    0.9,
                                                ],
                                            },
                                            {
                                                "op": "if",
                                                "condition": {
                                                    "op": "gt",
                                                    "left": {
                                                        "op": "len",
                                                        "value": {"$ref": "slots.window_profiles"},
                                                    },
                                                    "right": 0,
                                                },
                                                "then": {
                                                    "op": "div",
                                                    "left": {
                                                        "op": "sum",
                                                        "source": {"$ref": "slots.window_profiles"},
                                                        "as": "item",
                                                        "value": {
                                                            "op": "ref",
                                                            "path": "vars.item.combined_strength",
                                                        },
                                                    },
                                                    "right": {
                                                        "op": "len",
                                                        "value": {"$ref": "slots.window_profiles"},
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
        self.assertEqual(result.get("heuristic_score"), 27.793)
        self.assertEqual(len(result.get("degree_view")), 3)
        self.assertEqual(result.get("degree_view")[0]["degree"], 2)
        self.assertEqual(result.get("degree_view")[2]["label"], "critical")
        self.assertEqual(len(result.get("critical_neighbors")), 2)
        self.assertEqual(result.get("critical_neighbors")[0]["label"], "entry")
        self.assertEqual(len(result.get("connected_components")), 1)
        self.assertEqual(result.get("connected_components")[0]["size"], 3)
        self.assertEqual(len(result.get("edge_pairs")), 3)
        self.assertEqual(result.get("critical_entry_overlap")["overlap_count"], 1)
        self.assertEqual(len(result.get("critical_reach")), 2)
        self.assertEqual(result.get("critical_reach")[0]["depth"], 1)
        self.assertTrue(result.get("entry_to_explorer_path")["reachable"])
        self.assertEqual(result.get("entry_to_explorer_path")["length"], 1)
        self.assertEqual(result.get("critical_signal_profile")[0]["label"], "critical")
        self.assertEqual(len(result.get("critical_random_walk")["trace"]), 5)
        self.assertEqual(result.get("entry_flow_profile")["successful_path_count"], 2)
        self.assertEqual(len(result.get("triangle_patterns")), 1)
        self.assertEqual(result.get("centrality_profile")[0]["score"], 1.0)
        self.assertAlmostEqual(result.get("closeness_profile")[0]["score"], 1.0)
        self.assertEqual(result.get("critical_policy_walk")["unique_visits"], 3)
        self.assertEqual(len(result.get("square_patterns")), 0)
        self.assertEqual(len(result.get("star_patterns")), 0)
        self.assertEqual(len(result.get("priority_nodes")), 2)
        self.assertEqual(sorted(result.get("priority_groups").keys()), ["critical", "entry"])
        self.assertAlmostEqual(result.get("ranked_priority_nodes")[0]["strength"], 3.3)
        self.assertEqual(result.get("priority_summary")["critical_count"], 1)
        self.assertAlmostEqual(result.get("priority_summary")["avg_strength"], 3.3)
        self.assertEqual(result.get("window_profiles")[0]["labels"], ["entry", "critical"])
        self.assertEqual(result.get("priority_nodes")[1]["label"], "critical")
        self.assertEqual(result.get("next_strategy")["phase"], "intensify")
        self.assertEqual(result.get("next_strategy")["primary_weight"], 0.9)
        self.assertEqual(result.get_slot_definition("affinity_matrix").kind, "matrix")

    def test_graph_expressions_support_weighted_activation_rules(self) -> None:
        definition = {
            "name": "weighted_activation_definition",
            "slot_definitions": [
                {
                    "name": "weighted_affinity_matrix",
                    "kind": "matrix",
                    "representation": "weighted",
                    "default": [
                        [0.0, 0.85, 0.15],
                        [0.2, 0.0, 0.92],
                        [0.88, 0.74, 0.0],
                    ],
                },
                {
                    "name": "node_labels",
                    "kind": "mapping",
                    "representation": "tag_map",
                    "default": {"0": "entry", "1": "support", "2": "critical"},
                },
                {
                    "name": "weighted_band_neighbors",
                    "kind": "object_collection",
                    "representation": "weighted_neighbor_subset",
                    "default": [],
                },
                {
                    "name": "weighted_degree_view",
                    "kind": "object_collection",
                    "representation": "weighted_degree_profile",
                    "default": [],
                },
                {
                    "name": "activated_weighted_edges",
                    "kind": "object_collection",
                    "representation": "activated_edge_pairs",
                    "default": [],
                },
                {
                    "name": "weighted_path",
                    "kind": "object",
                    "representation": "weighted_path_profile",
                    "default": {},
                },
                {
                    "name": "weighted_cost_path",
                    "kind": "object",
                    "representation": "weighted_cost_path_profile",
                    "default": {},
                },
                {
                    "name": "weighted_edge_strengths",
                    "kind": "object_collection",
                    "representation": "weighted_edge_strength_profile",
                    "default": [],
                },
                {
                    "name": "weighted_policy_walk",
                    "kind": "object",
                    "representation": "weighted_policy_walk_profile",
                    "default": {},
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_weighted_band_neighbors",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "weighted_band_neighbors",
                            "value": {
                                "$expr": {
                                    "op": "neighbors_of",
                                    "source": {"$ref": "slots.weighted_affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "node_index": 2,
                                    "activation": {
                                        "mode": "between",
                                        "min_value": 0.7,
                                        "max_value": 0.9,
                                    },
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_weighted_degree_view",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "weighted_degree_view",
                            "value": {
                                "$expr": {
                                    "op": "matrix_degrees",
                                    "source": {"$ref": "slots.weighted_affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "activation": {"mode": "gte", "value": 0.75},
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_activated_weighted_edges",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "activated_weighted_edges",
                            "value": {
                                "$expr": {
                                    "op": "edge_pairs",
                                    "source": {"$ref": "slots.weighted_affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "activation": {"mode": "gte", "value": 0.75},
                                    "directed": False,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_weighted_path",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "weighted_path",
                            "value": {
                                "$expr": {
                                    "op": "shortest_path",
                                    "source": {"$ref": "slots.weighted_affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "start_node_index": 0,
                                    "target_node_index": 2,
                                    "activation": {"mode": "gte", "value": 0.85},
                                    "undirected": True,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_weighted_cost_path",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "weighted_cost_path",
                            "value": {
                                "$expr": {
                                    "op": "weighted_shortest_path",
                                    "source": {"$ref": "slots.weighted_affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "start_node_index": 0,
                                    "target_node_index": 2,
                                    "activation": {"mode": "nonzero"},
                                    "undirected": False,
                                    "cost_mode": "inverse_weight",
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_weighted_edge_strengths",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "weighted_edge_strengths",
                            "value": {
                                "$expr": {
                                    "op": "edge_strength_profile",
                                    "source": {"$ref": "slots.weighted_affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "activation": {"mode": "nonzero"},
                                    "directed": False,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_weighted_policy_walk",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "weighted_policy_walk",
                            "value": {
                                "$expr": {
                                    "op": "weighted_policy_walk",
                                    "source": {"$ref": "slots.weighted_affinity_matrix"},
                                    "labels": {"$ref": "slots.node_labels"},
                                    "start_node_index": 0,
                                    "steps": 3,
                                    "activation": {"mode": "nonzero"},
                                    "undirected": False,
                                    "policy": "prefer_strongest",
                                    "cost_mode": "inverse_weight",
                                }
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

        self.assertEqual(len(result.get("weighted_band_neighbors")), 2)
        self.assertEqual(result.get("weighted_band_neighbors")[0]["label"], "entry")
        self.assertAlmostEqual(result.get("weighted_band_neighbors")[0]["edge_value"], 0.88)
        self.assertEqual(result.get("weighted_band_neighbors")[1]["label"], "support")
        self.assertEqual(len(result.get("weighted_degree_view")), 3)
        self.assertEqual(result.get("weighted_degree_view")[0]["degree"], 1)
        self.assertAlmostEqual(result.get("weighted_degree_view")[0]["total_edge_weight"], 0.85)
        self.assertAlmostEqual(result.get("weighted_degree_view")[1]["avg_edge_weight"], 0.92)
        self.assertEqual(len(result.get("activated_weighted_edges")), 3)
        self.assertTrue(result.get("weighted_path")["reachable"])
        self.assertEqual(result.get("weighted_path")["length"], 1)
        self.assertTrue(result.get("weighted_cost_path")["reachable"])
        self.assertEqual(result.get("weighted_cost_path")["node_ids"], [0, 1, 2])
        self.assertAlmostEqual(result.get("weighted_cost_path")["total_cost"], 2.263427, places=6)
        self.assertEqual(len(result.get("weighted_cost_path")["edge_costs"]), 2)
        self.assertEqual(result.get("weighted_edge_strengths")[0]["strength"], 0.92)
        self.assertEqual(result.get("weighted_edge_strengths")[0]["source_id"], 1)
        self.assertEqual([item["node_id"] for item in result.get("weighted_policy_walk")["trace"]], [0, 1, 2, 0])
        self.assertAlmostEqual(result.get("weighted_policy_walk")["total_cost"], 3.399791, places=6)
        self.assertEqual(result.get("weighted_policy_walk")["unique_visits"], 3)

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
        self.assertIn("reduce", contract["supported_expression_operators"])
        self.assertIn("matrix_degrees", contract["supported_expression_operators"])
        self.assertIn("connected_components", contract["supported_expression_operators"])
        self.assertIn("shortest_path", contract["supported_expression_operators"])
        self.assertIn("flow_profile", contract["supported_expression_operators"])
        self.assertIn("centrality_profile", contract["supported_expression_operators"])
        self.assertIn("closeness_profile", contract["supported_expression_operators"])
        self.assertIn("edge_strength_profile", contract["supported_expression_operators"])
        self.assertIn("weighted_policy_walk", contract["supported_expression_operators"])
        self.assertIn("weighted_shortest_path", contract["supported_expression_operators"])


if __name__ == "__main__":
    unittest.main()
