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

    def test_population_search_operators_support_selection_mutation_and_restart(self) -> None:
        definition = {
            "name": "population_search_definition",
            "initial_slots": {
                "rng_seed": 17,
                "target": 2.75,
                "target_score": 0.05,
                "population_size": 8,
            },
            "slot_definitions": [
                {
                    "name": "population",
                    "kind": "object_collection",
                    "representation": "candidate_population",
                    "default": [],
                },
                {
                    "name": "elite_population",
                    "kind": "object_collection",
                    "representation": "elite_population",
                    "default": [],
                },
                {
                    "name": "mutated_population",
                    "kind": "object_collection",
                    "representation": "mutated_population",
                    "default": [],
                },
                {
                    "name": "population_summary",
                    "kind": "object",
                    "representation": "population_summary",
                    "default": {},
                },
                {
                    "name": "best",
                    "kind": "object",
                    "representation": "best_candidate",
                    "default": None,
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "initialize_population",
                        "operator": "initialize_population",
                        "params": {"population_size": 8, "target": {"$ref": "slots.target"}},
                    },
                    {
                        "type": "operator",
                        "name": "summarize_initial_population",
                        "operator": "summarize_population",
                        "params": {
                            "population": {"$ref": "slots.population"},
                            "output_slot": "population_summary",
                            "best_output_slot": "best",
                        },
                    },
                    {
                        "type": "loop",
                        "name": "optimization_loop",
                        "max_iterations": 4,
                        "body": {
                            "type": "sequence",
                            "name": "population_iteration",
                            "steps": [
                                {
                                    "type": "operator",
                                    "name": "select_top_population",
                                    "operator": "select_top_population",
                                    "params": {
                                        "population": {"$ref": "slots.population"},
                                        "selection_size": 3,
                                        "output_slot": "elite_population",
                                    },
                                },
                                {
                                    "type": "operator",
                                    "name": "mutate_population",
                                    "operator": "mutate_population",
                                    "params": {
                                        "population": {"$ref": "slots.elite_population"},
                                        "clones_per_candidate": 2,
                                        "mutation_scale": 0.55,
                                        "target": {"$ref": "slots.target"},
                                        "output_slot": "mutated_population",
                                    },
                                },
                                {
                                    "type": "operator",
                                    "name": "restart_population",
                                    "operator": "restart_population",
                                    "params": {
                                        "elites": {"$ref": "slots.elite_population"},
                                        "candidates": {"$ref": "slots.mutated_population"},
                                        "target_population_size": 8,
                                        "target": {"$ref": "slots.target"},
                                        "min_position": -8.0,
                                        "max_position": 8.0,
                                        "restart_mode": "elite_biased",
                                        "output_slot": "population",
                                    },
                                },
                                {
                                    "type": "operator",
                                    "name": "summarize_population",
                                    "operator": "summarize_population",
                                    "params": {
                                        "population": {"$ref": "slots.population"},
                                        "output_slot": "population_summary",
                                        "best_output_slot": "best",
                                    },
                                },
                            ],
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

        self.assertEqual(len(result.get("population")), 8)
        self.assertEqual(len(result.get("elite_population")), 3)
        self.assertEqual(len(result.get("mutated_population")), 6)
        self.assertEqual(result.get("population_summary")["population_size"], 8)
        self.assertLess(result.get("population_summary")["best_score"], 1.0)
        self.assertEqual(result.metrics.get("elite_population_size"), 3)
        self.assertEqual(result.metrics.get("mutated_population_size"), 6)
        self.assertEqual(result.metrics.get("restart_mode"), "elite_biased")
        self.assertEqual(result.metrics.get("population_size"), 8)
        self.assertEqual(result.get("best")["score"], result.metrics.get("best_score"))

    def test_population_operators_support_selection_recombination_and_acceptance(self) -> None:
        definition = {
            "name": "selection_recombination_definition",
            "initial_slots": {
                "rng_seed": 19,
                "target": 1.5,
                "population_size": 6,
            },
            "slot_definitions": [
                {
                    "name": "population",
                    "kind": "object_collection",
                    "representation": "candidate_population",
                    "default": [],
                },
                {
                    "name": "selected_population",
                    "kind": "object_collection",
                    "representation": "selected_population",
                    "default": [],
                },
                {
                    "name": "recombined_population",
                    "kind": "object_collection",
                    "representation": "recombined_population",
                    "default": [],
                },
                {
                    "name": "mutated_population",
                    "kind": "object_collection",
                    "representation": "mutated_population",
                    "default": [],
                },
                {
                    "name": "accepted_population",
                    "kind": "object_collection",
                    "representation": "accepted_population",
                    "default": [],
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "initialize_population",
                        "operator": "initialize_population",
                        "params": {"population_size": 6, "target": {"$ref": "slots.target"}},
                    },
                    {
                        "type": "operator",
                        "name": "select_population_batch",
                        "operator": "select_population_batch",
                        "params": {
                            "population": {"$ref": "slots.population"},
                            "selection_size": 3,
                            "selection_policy": "tournament",
                            "tournament_size": 3,
                            "output_slot": "selected_population",
                        },
                    },
                    {
                        "type": "operator",
                        "name": "recombine_population",
                        "operator": "recombine_population",
                        "params": {
                            "parents": {"$ref": "slots.selected_population"},
                            "offspring_count": 4,
                            "pairing_policy": "random",
                            "blend_bias": 0.5,
                            "jitter_scale": 0.1,
                            "target": {"$ref": "slots.target"},
                            "output_slot": "recombined_population",
                        },
                    },
                    {
                        "type": "operator",
                        "name": "mutate_population",
                        "operator": "mutate_population",
                        "params": {
                            "population": {"$ref": "slots.recombined_population"},
                            "clones_per_candidate": 1,
                            "mutation_scale": 0.2,
                            "target": {"$ref": "slots.target"},
                            "output_slot": "mutated_population",
                        },
                    },
                    {
                        "type": "operator",
                        "name": "accept_population_candidates",
                        "operator": "accept_population_candidates",
                        "params": {
                            "current_population": {"$ref": "slots.population"},
                            "candidates": {"$ref": "slots.mutated_population"},
                            "acceptance_policy": "best",
                            "target_population_size": 5,
                            "output_slot": "accepted_population",
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

        self.assertEqual(len(result.get("selected_population")), 3)
        self.assertEqual(len(result.get("recombined_population")), 4)
        self.assertEqual(len(result.get("mutated_population")), 4)
        self.assertEqual(len(result.get("accepted_population")), 5)
        self.assertEqual(result.metrics.get("selection_policy"), "tournament")
        self.assertEqual(result.metrics.get("recombined_population_size"), 4)
        self.assertEqual(result.metrics.get("mutated_population_size"), 4)
        self.assertEqual(result.metrics.get("acceptance_policy"), "best")
        self.assertEqual(result.metrics.get("accepted_population_size"), 5)
        accepted_scores = [item["score"] for item in result.get("accepted_population")]
        self.assertEqual(accepted_scores, sorted(accepted_scores))

    def test_population_operators_support_directional_recombination_and_diversity_acceptance(self) -> None:
        definition = {
            "name": "directional_population_definition",
            "initial_slots": {
                "target": 0.0,
                "population": [
                    {"position": 0.0, "mass": 1.0, "score": 0.0},
                    {"position": 1.0, "mass": 1.0, "score": 1.0},
                    {"position": 2.0, "mass": 1.0, "score": 2.0},
                ],
            },
            "slot_definitions": [
                {
                    "name": "population",
                    "kind": "object_collection",
                    "representation": "candidate_population",
                    "default": [],
                },
                {
                    "name": "selected_population",
                    "kind": "object_collection",
                    "representation": "selected_population",
                    "default": [],
                },
                {
                    "name": "recombined_population",
                    "kind": "object_collection",
                    "representation": "recombined_population",
                    "default": [],
                },
                {
                    "name": "accepted_population",
                    "kind": "object_collection",
                    "representation": "accepted_population",
                    "default": [],
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "select_population_batch",
                        "operator": "select_population_batch",
                        "params": {
                            "population": {"$ref": "slots.population"},
                            "selection_size": 3,
                            "selection_policy": "top",
                            "output_slot": "selected_population",
                        },
                    },
                    {
                        "type": "operator",
                        "name": "recombine_population",
                        "operator": "recombine_population",
                        "params": {
                            "parents": {"$ref": "slots.selected_population"},
                            "offspring_count": 3,
                            "pairing_policy": "sequential",
                            "recombination_policy": "directional",
                            "directional_scale": 0.5,
                            "jitter_scale": 0.0,
                            "target": {"$ref": "slots.target"},
                            "output_slot": "recombined_population",
                        },
                    },
                    {
                        "type": "operator",
                        "name": "accept_population_candidates",
                        "operator": "accept_population_candidates",
                        "params": {
                            "current_population": {"$ref": "slots.population"},
                            "candidates": {"$ref": "slots.recombined_population"},
                            "acceptance_policy": "diversity_guarded",
                            "minimum_distance": 0.4,
                            "target_population_size": 3,
                            "output_slot": "accepted_population",
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

        recombined = result.get("recombined_population")
        accepted = result.get("accepted_population")

        self.assertEqual([round(item["position"], 3) for item in recombined], [-0.5, 0.5, -1.0])
        self.assertTrue(all(item["recombination_policy"] == "directional" for item in recombined))
        self.assertEqual(len(accepted), 3)
        self.assertEqual(result.metrics.get("recombination_policy"), "directional")
        self.assertEqual(result.metrics.get("acceptance_policy"), "diversity_guarded")
        for left_index, left in enumerate(accepted):
            for right in accepted[left_index + 1 :]:
                self.assertGreaterEqual(abs(left["position"] - right["position"]), 0.4)

    def test_population_operators_support_scheduled_params_and_annealed_acceptance(self) -> None:
        definition = {
            "name": "scheduled_population_definition",
            "initial_slots": {
                "target": 0.0,
                "population": [
                    {"position": 0.0, "mass": 1.0, "score": 0.0},
                    {"position": 1.0, "mass": 1.0, "score": 1.0},
                    {"position": 2.0, "mass": 1.0, "score": 2.0},
                ],
            },
            "slot_definitions": [
                {
                    "name": "population",
                    "kind": "object_collection",
                    "representation": "candidate_population",
                    "default": [],
                },
                {
                    "name": "selected_population",
                    "kind": "object_collection",
                    "representation": "selected_population",
                    "default": [],
                },
                {
                    "name": "recombined_population",
                    "kind": "object_collection",
                    "representation": "recombined_population",
                    "default": [],
                },
                {
                    "name": "accepted_population",
                    "kind": "object_collection",
                    "representation": "accepted_population",
                    "default": [],
                },
                {
                    "name": "schedule_progress",
                    "kind": "scalar",
                    "representation": "schedule_progress",
                    "default": 0.0,
                },
                {
                    "name": "directional_scale",
                    "kind": "scalar",
                    "representation": "directional_scale",
                    "default": 0.0,
                },
                {
                    "name": "annealing_temperature",
                    "kind": "scalar",
                    "representation": "annealing_temperature",
                    "default": 0.0,
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_schedule_progress",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "schedule_progress",
                            "value": {
                                "$expr": {
                                    "op": "clamp",
                                    "value": 0.4,
                                    "min_value": 0.0,
                                    "max_value": 1.0,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_directional_scale",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "directional_scale",
                            "value": {
                                "$expr": {
                                    "op": "lerp",
                                    "start": 0.2,
                                    "end": 0.5,
                                    "t": {"$ref": "slots.schedule_progress"},
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_annealing_temperature",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "annealing_temperature",
                            "value": {
                                "$expr": {
                                    "op": "lerp",
                                    "start": 0.05,
                                    "end": 0.000001,
                                    "t": 1.0,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "select_population_batch",
                        "operator": "select_population_batch",
                        "params": {
                            "population": {"$ref": "slots.population"},
                            "selection_size": 3,
                            "selection_policy": "top",
                            "output_slot": "selected_population",
                        },
                    },
                    {
                        "type": "operator",
                        "name": "recombine_population",
                        "operator": "recombine_population",
                        "params": {
                            "parents": {"$ref": "slots.selected_population"},
                            "offspring_count": 3,
                            "pairing_policy": "sequential",
                            "recombination_policy": "directional",
                            "directional_scale": {"$ref": "slots.directional_scale"},
                            "jitter_scale": 0.0,
                            "target": {"$ref": "slots.target"},
                            "output_slot": "recombined_population",
                        },
                    },
                    {
                        "type": "operator",
                        "name": "accept_population_candidates",
                        "operator": "accept_population_candidates",
                        "params": {
                            "current_population": {"$ref": "slots.population"},
                            "candidates": {"$ref": "slots.recombined_population"},
                            "acceptance_policy": "annealed",
                            "annealing_temperature": {"$ref": "slots.annealing_temperature"},
                            "target_population_size": 2,
                            "output_slot": "accepted_population",
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

        self.assertAlmostEqual(result.get("schedule_progress"), 0.4)
        self.assertAlmostEqual(result.get("directional_scale"), 0.32, places=6)
        self.assertAlmostEqual(result.get("annealing_temperature"), 0.000001, places=6)
        self.assertEqual([round(item["position"], 2) for item in result.get("recombined_population")], [-0.32, 0.68, -0.64])
        self.assertEqual([round(item["score"], 2) for item in result.get("accepted_population")], [0.0, 0.32])
        self.assertEqual(result.metrics.get("acceptance_policy"), "annealed")

    def test_population_operators_support_rank_selection_policy(self) -> None:
        definition = {
            "name": "rank_selection_definition",
            "initial_slots": {
                "rng_seed": 23,
                "target": 0.0,
                "population": [
                    {"position": 0.0, "mass": 1.0, "score": 0.0},
                    {"position": 1.0, "mass": 1.0, "score": 1.0},
                    {"position": 2.0, "mass": 1.0, "score": 2.0},
                    {"position": 3.0, "mass": 1.0, "score": 3.0},
                ],
            },
            "slot_definitions": [
                {
                    "name": "population",
                    "kind": "object_collection",
                    "representation": "candidate_population",
                    "default": [],
                },
                {
                    "name": "selected_population",
                    "kind": "object_collection",
                    "representation": "selected_population",
                    "default": [],
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "select_population_batch",
                        "operator": "select_population_batch",
                        "params": {
                            "population": {"$ref": "slots.population"},
                            "selection_size": 5,
                            "selection_policy": "rank",
                            "output_slot": "selected_population",
                        },
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

        self.assertEqual(len(result.get("selected_population")), 5)
        self.assertEqual(result.metrics.get("selection_policy"), "rank")
        self.assertTrue(all(item["position"] in {0.0, 1.0, 2.0, 3.0} for item in result.get("selected_population")))

    def test_expression_supports_metric_history_and_trend_profile(self) -> None:
        definition = {
            "name": "trend_memory_definition",
            "initial_slots": {
                "population": [
                    {"position": 0.0, "mass": 1.0, "score": 0.6},
                    {"position": 1.0, "mass": 1.0, "score": 0.9},
                ]
            },
            "slot_definitions": [
                {
                    "name": "population",
                    "kind": "object_collection",
                    "representation": "candidate_population",
                    "default": [],
                },
                {
                    "name": "population_summary",
                    "kind": "object",
                    "representation": "population_summary",
                    "default": {},
                },
                {
                    "name": "best",
                    "kind": "object",
                    "representation": "best_candidate",
                    "default": None,
                },
                {
                    "name": "best_score_history",
                    "kind": "object_collection",
                    "representation": "metric_history",
                    "default": [],
                },
                {
                    "name": "best_score_trend",
                    "kind": "object",
                    "representation": "trend_profile",
                    "default": {},
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "summarize_initial_population",
                        "operator": "summarize_population",
                        "params": {
                            "population": {"$ref": "slots.population"},
                            "output_slot": "population_summary",
                            "best_output_slot": "best",
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_population",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "population",
                            "value": [
                                {"position": 0.0, "mass": 1.0, "score": 0.4},
                                {"position": 1.0, "mass": 1.0, "score": 0.7},
                            ],
                        },
                    },
                    {
                        "type": "operator",
                        "name": "summarize_population",
                        "operator": "summarize_population",
                        "params": {
                            "population": {"$ref": "slots.population"},
                            "output_slot": "population_summary",
                            "best_output_slot": "best",
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_best_score_history",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "best_score_history",
                            "value": {
                                "$expr": {
                                    "op": "metric_history",
                                    "metric": "best_score",
                                    "nodes": ["summarize_initial_population", "summarize_population"],
                                    "window": 3,
                                }
                            },
                        },
                    },
                    {
                        "type": "operator",
                        "name": "set_best_score_trend",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "best_score_trend",
                            "value": {
                                "$expr": {
                                    "op": "trend_profile",
                                    "metric": "best_score",
                                    "nodes": ["summarize_initial_population", "summarize_population"],
                                    "window": 3,
                                    "preference": "decrease",
                                    "tolerance": 0.001,
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

        self.assertEqual(result.get("best_score_history"), [0.6, 0.4, 0.4])
        self.assertEqual(result.get("best_score_trend")["values"], [0.6, 0.4, 0.4])
        self.assertEqual(result.get("best_score_trend")["stagnation_steps"], 1)
        self.assertFalse(result.get("best_score_trend")["is_improving"])
        self.assertAlmostEqual(result.get("best_score_trend")["avg_delta"], -0.1, places=6)

    def test_condition_and_subgraph_support_memory_driven_population_response(self) -> None:
        definition = {
            "name": "memory_response_definition",
            "slot_definitions": [
                {
                    "name": "best_score_trend",
                    "kind": "object",
                    "representation": "trend_profile",
                    "default": {"stagnation_steps": 0},
                },
                {
                    "name": "selection_policy",
                    "kind": "scalar",
                    "representation": "selection_policy",
                    "default": "rank",
                },
                {
                    "name": "acceptance_policy",
                    "kind": "scalar",
                    "representation": "acceptance_policy",
                    "default": "annealed",
                },
                {
                    "name": "restart_mode",
                    "kind": "scalar",
                    "representation": "restart_mode",
                    "default": "elite_biased",
                },
                {
                    "name": "response_mode",
                    "kind": "scalar",
                    "representation": "response_mode",
                    "default": "neutral",
                },
            ],
            "subgraphs": [
                {
                    "name": "response_block",
                    "node": {
                        "type": "sequence",
                        "name": "response_block_sequence",
                        "steps": [
                            {
                                "type": "operator",
                                "name": "set_response_mode",
                                "operator": "set_slot_value",
                                "params": {
                                    "slot": "response_mode",
                                    "value": {"$ref": "args.response_mode"},
                                },
                            },
                            {
                                "type": "operator",
                                "name": "set_response_selection",
                                "operator": "set_slot_value",
                                "params": {
                                    "slot": "selection_policy",
                                    "value": {"$ref": "args.selection_policy"},
                                },
                            },
                            {
                                "type": "operator",
                                "name": "set_response_acceptance",
                                "operator": "set_slot_value",
                                "params": {
                                    "slot": "acceptance_policy",
                                    "value": {"$ref": "args.acceptance_policy"},
                                },
                            },
                            {
                                "type": "operator",
                                "name": "set_response_restart",
                                "operator": "set_slot_value",
                                "params": {
                                    "slot": "restart_mode",
                                    "value": {"$ref": "args.restart_mode"},
                                },
                            },
                        ],
                    },
                }
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_best_score_trend",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "best_score_trend",
                            "value": {"stagnation_steps": 3},
                        },
                    },
                    {
                        "type": "condition",
                        "name": "run_memory_response_block",
                        "condition": {
                            "expression": {
                                "op": "gte",
                                "left": {"op": "ref", "path": "slots.best_score_trend.stagnation_steps"},
                                "right": 2,
                            }
                        },
                        "then": {
                            "type": "subgraph",
                            "name": "activate_diversify_response",
                            "ref": "response_block",
                            "params": {
                                "response_mode": "diversify_response",
                                "selection_policy": "roulette",
                                "acceptance_policy": "diversity_guarded",
                                "restart_mode": "uniform",
                            },
                        },
                        "else": {
                            "type": "subgraph",
                            "name": "activate_intensify_response",
                            "ref": "response_block",
                            "params": {
                                "response_mode": "intensify_response",
                                "selection_policy": "tournament",
                                "acceptance_policy": "annealed",
                                "restart_mode": "elite_biased",
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

        self.assertEqual(result.get("response_mode"), "diversify_response")
        self.assertEqual(result.get("selection_policy"), "roulette")
        self.assertEqual(result.get("acceptance_policy"), "diversity_guarded")
        self.assertEqual(result.get("restart_mode"), "uniform")

    def test_expression_supports_slot_history(self) -> None:
        definition = {
            "name": "slot_history_definition",
            "slot_definitions": [
                {
                    "name": "response_mode",
                    "kind": "scalar",
                    "representation": "response_mode",
                    "default": "neutral",
                },
                {
                    "name": "response_history",
                    "kind": "object_collection",
                    "representation": "response_history",
                    "default": [],
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_response_mode_first",
                        "operator": "set_slot_value",
                        "snapshot_keys": ["response_mode"],
                        "params": {"slot": "response_mode", "value": "diversify_response"},
                    },
                    {
                        "type": "operator",
                        "name": "set_response_mode_second",
                        "operator": "set_slot_value",
                        "snapshot_keys": ["response_mode"],
                        "params": {"slot": "response_mode", "value": "stability_response"},
                    },
                    {
                        "type": "operator",
                        "name": "set_response_history",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "response_history",
                            "value": {
                                "$expr": {
                                    "op": "slot_history",
                                    "slot": "response_mode",
                                    "nodes": ["set_response_mode_first", "set_response_mode_second"],
                                    "window": 3,
                                    "include_current": True,
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

        self.assertEqual(
            result.get("response_history"),
            ["diversify_response", "stability_response", "stability_response"],
        )

    def test_expression_supports_max_by_for_response_arbitration(self) -> None:
        definition = {
            "name": "response_arbitration_definition",
            "slot_definitions": [
                {
                    "name": "response_candidates",
                    "kind": "object_collection",
                    "representation": "response_candidates",
                    "default": [],
                },
                {
                    "name": "selected_response_candidate",
                    "kind": "object",
                    "representation": "selected_response_candidate",
                    "default": {},
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_response_candidates",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "response_candidates",
                            "value": [
                                {"response_mode": "intensify_response", "score": 1.2},
                                {"response_mode": "diversify_response", "score": 2.4},
                                {"response_mode": "stability_response", "score": 1.8},
                            ],
                        },
                    },
                    {
                        "type": "operator",
                        "name": "select_response_candidate",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "selected_response_candidate",
                            "value": {
                                "$expr": {
                                    "op": "max_by",
                                    "source": {"$ref": "slots.response_candidates"},
                                    "as": "item",
                                    "value": {"op": "ref", "path": "vars.item.score"},
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

        self.assertEqual(result.get("selected_response_candidate")["response_mode"], "diversify_response")
        self.assertEqual(result.get("selected_response_candidate")["score"], 2.4)

    def test_expression_supports_merge_objects_for_response_library_materialization(self) -> None:
        definition = {
            "name": "merge_objects_definition",
            "slot_definitions": [
                {
                    "name": "response_library",
                    "kind": "object_collection",
                    "representation": "response_library",
                    "default": [{"response_mode": "intensify_response", "selection_policy": "rank"}],
                },
                {
                    "name": "response_candidates",
                    "kind": "object_collection",
                    "representation": "response_candidates",
                    "default": [],
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_response_candidates",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "response_candidates",
                            "value": {
                                "$expr": {
                                    "op": "map",
                                    "source": {"$ref": "slots.response_library"},
                                    "as": "item",
                                    "value": {
                                        "$expr": {
                                            "op": "merge_objects",
                                            "objects": [
                                                {"$ref": "vars.item"},
                                                {"score": 2.2, "restart_mode": "elite_biased"},
                                            ],
                                        }
                                    },
                                }
                            },
                        },
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

        self.assertEqual(
            result.get("response_candidates")[0],
            {
                "response_mode": "intensify_response",
                "selection_policy": "rank",
                "score": 2.2,
                "restart_mode": "elite_biased",
            },
        )

    def test_expression_supports_weighted_sum_for_response_scoring(self) -> None:
        definition = {
            "name": "weighted_sum_definition",
            "slot_definitions": [
                {
                    "name": "response_score",
                    "kind": "scalar",
                    "representation": "response_score",
                    "default": 0.0,
                }
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_response_score",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "response_score",
                            "value": {
                                "$expr": {
                                    "op": "weighted_sum",
                                    "terms": [
                                        {"value": 1, "weight": 2.0},
                                        {"value": 1, "weight": 0.4, "enabled": False},
                                        {
                                            "value": {
                                                "$expr": {
                                                    "op": "if",
                                                    "condition": True,
                                                    "then": 1,
                                                    "else": 0,
                                                }
                                            },
                                            "weight": 0.2,
                                        },
                                    ],
                                }
                            },
                        },
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

        self.assertEqual(result.get("response_score"), 2.2)

    def test_expression_supports_frequency_map_for_usage_profiles(self) -> None:
        definition = {
            "name": "frequency_map_definition",
            "slot_definitions": [
                {
                    "name": "response_history",
                    "kind": "object_collection",
                    "representation": "response_history",
                    "default": ["diversify_response", "stability_response", "diversify_response"],
                },
                {
                    "name": "response_usage_profile",
                    "kind": "mapping",
                    "representation": "usage_profile",
                    "default": {},
                },
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_usage_profile",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "response_usage_profile",
                            "value": {
                                "$expr": {
                                    "op": "frequency_map",
                                    "source": {"$ref": "slots.response_history"},
                                    "as": "item",
                                }
                            },
                        },
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

        self.assertEqual(
            result.get("response_usage_profile"),
            {"diversify_response": 2, "stability_response": 1},
        )

    def test_expression_supports_pairwise_deltas_for_outcome_history(self) -> None:
        definition = {
            "name": "pairwise_deltas_definition",
            "slot_definitions": [
                {
                    "name": "outcomes",
                    "kind": "object_collection",
                    "representation": "outcome_history",
                    "default": [],
                }
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_outcomes",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "outcomes",
                            "value": {
                                "$expr": {
                                    "op": "pairwise_deltas",
                                    "source": [1.2, 0.9, 0.75, 0.8],
                                    "preference": "decrease",
                                }
                            },
                        },
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

        self.assertEqual(result.get("outcomes"), [0.29999999999999993, 0.15000000000000002, -0.050000000000000044])

    def test_expression_get_uses_default_for_out_of_range_list_index(self) -> None:
        definition = {
            "name": "get_list_default_definition",
            "slot_definitions": [
                {
                    "name": "value",
                    "kind": "scalar",
                    "representation": "defaulted_value",
                    "default": 0,
                }
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_value",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "value",
                            "value": {
                                "$expr": {
                                    "op": "get",
                                    "source": [1, 2],
                                    "key": 5,
                                    "default": 9,
                                }
                            },
                        },
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

        self.assertEqual(result.get("value"), 9)

    def test_expression_supports_concat_for_phase_response_keys(self) -> None:
        definition = {
            "name": "concat_definition",
            "slot_definitions": [
                {
                    "name": "key",
                    "kind": "scalar",
                    "representation": "composite_key",
                    "default": "",
                }
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_key",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "key",
                            "value": {
                                "$expr": {
                                    "op": "concat",
                                    "args": ["early", "intensify_response"],
                                    "separator": "::",
                                }
                            },
                        },
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

        self.assertEqual(result.get("key"), "early::intensify_response")

    def test_expression_supports_assoc_for_effectiveness_aggregation(self) -> None:
        definition = {
            "name": "assoc_definition",
            "slot_definitions": [
                {
                    "name": "profile",
                    "kind": "mapping",
                    "representation": "effectiveness_profile",
                    "default": {},
                }
            ],
            "root": {
                "type": "sequence",
                "name": "root_sequence",
                "steps": [
                    {
                        "type": "operator",
                        "name": "set_profile",
                        "operator": "set_slot_value",
                        "params": {
                            "slot": "profile",
                            "value": {
                                "$expr": {
                                    "op": "reduce",
                                    "source": [
                                        {"response_mode": "intensify_response", "improvement": 0.4},
                                        {"response_mode": "intensify_response", "improvement": 0.2},
                                    ],
                                    "as": "event",
                                    "accumulator_as": "acc",
                                    "initial": {},
                                    "value": {
                                        "op": "assoc",
                                        "source": {"op": "ref", "path": "vars.acc"},
                                        "key": {"op": "ref", "path": "vars.event.response_mode"},
                                        "value": {
                                            "$expr": {
                                                "op": "merge_objects",
                                                "objects": [
                                                    {
                                                        "$expr": {
                                                            "op": "get",
                                                            "source": {"op": "ref", "path": "vars.acc"},
                                                            "key": {"op": "ref", "path": "vars.event.response_mode"},
                                                            "default": {
                                                                "count": 0,
                                                                "total_improvement": 0.0,
                                                            },
                                                        }
                                                    },
                                                    {
                                                        "count": {
                                                            "$expr": {
                                                                "op": "add",
                                                                "args": [
                                                                    {
                                                                        "$expr": {
                                                                            "op": "get",
                                                                            "source": {
                                                                                "$expr": {
                                                                                    "op": "get",
                                                                                    "source": {"op": "ref", "path": "vars.acc"},
                                                                                    "key": {"op": "ref", "path": "vars.event.response_mode"},
                                                                                    "default": {
                                                                                        "count": 0,
                                                                                        "total_improvement": 0.0,
                                                                                    },
                                                                                }
                                                                            },
                                                                            "key": "count",
                                                                            "default": 0,
                                                                        }
                                                                    },
                                                                    1,
                                                                ],
                                                            }
                                                        },
                                                        "total_improvement": {
                                                            "$expr": {
                                                                "op": "add",
                                                                "args": [
                                                                    {
                                                                        "$expr": {
                                                                            "op": "get",
                                                                            "source": {
                                                                                "$expr": {
                                                                                    "op": "get",
                                                                                    "source": {"op": "ref", "path": "vars.acc"},
                                                                                    "key": {"op": "ref", "path": "vars.event.response_mode"},
                                                                                    "default": {
                                                                                        "count": 0,
                                                                                        "total_improvement": 0.0,
                                                                                    },
                                                                                }
                                                                            },
                                                                            "key": "total_improvement",
                                                                            "default": 0.0,
                                                                        }
                                                                    },
                                                                    {"op": "ref", "path": "vars.event.improvement"},
                                                                ],
                                                            }
                                                        },
                                                    },
                                                ],
                                            }
                                        },
                                    },
                                }
                            },
                        },
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

        self.assertEqual(
            result.get("profile"),
            {"intensify_response": {"count": 2, "total_improvement": 0.6000000000000001}},
        )

    def test_condition_and_subgraph_support_stability_response_after_repeated_diversify(self) -> None:
        definition = {
            "name": "stability_response_definition",
            "slot_definitions": [
                {
                    "name": "response_mode",
                    "kind": "scalar",
                    "representation": "response_mode",
                    "default": "diversify_response",
                },
                {
                    "name": "response_history",
                    "kind": "object_collection",
                    "representation": "response_history",
                    "default": ["diversify_response", "diversify_response"],
                },
                {
                    "name": "selection_policy",
                    "kind": "scalar",
                    "representation": "selection_policy",
                    "default": "roulette",
                },
                {
                    "name": "acceptance_policy",
                    "kind": "scalar",
                    "representation": "acceptance_policy",
                    "default": "diversity_guarded",
                },
                {
                    "name": "restart_mode",
                    "kind": "scalar",
                    "representation": "restart_mode",
                    "default": "uniform",
                },
                {
                    "name": "minimum_distance",
                    "kind": "scalar",
                    "representation": "minimum_distance",
                    "default": 0.45,
                },
                {
                    "name": "mutation_scale",
                    "kind": "scalar",
                    "representation": "mutation_scale",
                    "default": 0.32,
                },
                {
                    "name": "directional_scale",
                    "kind": "scalar",
                    "representation": "directional_scale",
                    "default": 0.28,
                },
            ],
            "subgraphs": [
                {
                    "name": "response_block",
                    "node": {
                        "type": "sequence",
                        "name": "response_block_sequence",
                        "steps": [
                            {
                                "type": "operator",
                                "name": "set_response_mode",
                                "operator": "set_slot_value",
                                "params": {"slot": "response_mode", "value": {"$ref": "args.response_mode"}},
                            },
                            {
                                "type": "operator",
                                "name": "set_response_selection",
                                "operator": "set_slot_value",
                                "params": {"slot": "selection_policy", "value": {"$ref": "args.selection_policy"}},
                            },
                            {
                                "type": "operator",
                                "name": "set_response_acceptance",
                                "operator": "set_slot_value",
                                "params": {"slot": "acceptance_policy", "value": {"$ref": "args.acceptance_policy"}},
                            },
                            {
                                "type": "operator",
                                "name": "set_response_restart",
                                "operator": "set_slot_value",
                                "params": {"slot": "restart_mode", "value": {"$ref": "args.restart_mode"}},
                            },
                        ],
                    },
                }
            ],
            "root": {
                "type": "condition",
                "name": "stabilize_after_repeated_diversify",
                "condition": {
                    "expression": {
                        "op": "gte",
                        "left": {
                            "op": "count",
                            "source": {"$ref": "slots.response_history"},
                            "as": "item",
                            "where": {
                                "op": "eq",
                                "left": {"op": "ref", "path": "vars.item"},
                                "right": "diversify_response",
                            },
                        },
                        "right": 2,
                    }
                },
                "then": {
                    "type": "subgraph",
                    "name": "activate_stability_response",
                    "ref": "response_block",
                    "params": {
                        "response_mode": "stability_response",
                        "selection_policy": "rank",
                        "acceptance_policy": "diversity_guarded",
                        "restart_mode": "elite_biased",
                    },
                },
            },
        }

        loaded = load_algorithm_definition(definition, build_builtin_registry())
        result = AlgorithmEngine().run(
            loaded.algorithm,
            initial_slots=loaded.initial_slots,
            slot_schema=loaded.slot_schema,
        )

        self.assertEqual(result.get("response_mode"), "stability_response")
        self.assertEqual(result.get("selection_policy"), "rank")
        self.assertEqual(result.get("acceptance_policy"), "diversity_guarded")
        self.assertEqual(result.get("restart_mode"), "elite_biased")

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
        self.assertIn("select_top_population", operator_names)
        self.assertIn("select_population_batch", operator_names)
        self.assertIn("mutate_population", operator_names)
        self.assertIn("recombine_population", operator_names)
        self.assertIn("restart_population", operator_names)
        self.assertIn("accept_population_candidates", operator_names)
        self.assertIn("summarize_population", operator_names)
        self.assertIn("supported_expression_operators", contract)
        self.assertIn("reduce", contract["supported_expression_operators"])
        self.assertIn("clamp", contract["supported_expression_operators"])
        self.assertIn("lerp", contract["supported_expression_operators"])
        self.assertIn("metric_history", contract["supported_expression_operators"])
        self.assertIn("slot_history", contract["supported_expression_operators"])
        self.assertIn("trend_profile", contract["supported_expression_operators"])
        self.assertIn("merge_objects", contract["supported_expression_operators"])
        self.assertIn("weighted_sum", contract["supported_expression_operators"])
        self.assertIn("frequency_map", contract["supported_expression_operators"])
        self.assertIn("pairwise_deltas", contract["supported_expression_operators"])
        self.assertIn("assoc", contract["supported_expression_operators"])
        self.assertIn("concat", contract["supported_expression_operators"])
        self.assertIn("max_by", contract["supported_expression_operators"])
        self.assertIn("min_by", contract["supported_expression_operators"])
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
