from __future__ import annotations

import random
from typing import Any

from .engine import Algorithm
from .models import BallistaContext
from .registry import OperatorRegistry
from .nodes import LoopNode, PythonNode, SequenceNode


def _score(candidate: dict[str, float], target: float) -> float:
    return abs(candidate["position"] - target)


def _get_rng(context: BallistaContext) -> random.Random:
    rng = context.get("rng")
    if rng is None:
        rng = random.Random(context.get("rng_seed", 0))
        context.set("rng", rng)
    return rng


def _initialize_population(context: BallistaContext, params: dict[str, Any]) -> None:
    rng = _get_rng(context)
    target = params.get("target", context.get("target", 0.0))
    population_size = params.get("population_size", context.get("population_size", 8))

    population = []
    for _ in range(population_size):
        position = rng.uniform(-12.0, 12.0)
        population.append(
            {
                "position": position,
                "mass": 1.0,
                "score": _score({"position": position}, target),
            }
        )

    best = min(population, key=lambda item: item["score"])
    context.set("population", population)
    context.set("best", dict(best))
    context.update_metric("best_score", best["score"])


def _apply_attraction(context: BallistaContext, params: dict[str, Any]) -> None:
    rng = _get_rng(context)
    population: list[dict[str, float]] = context.get("population", [])
    best = min(population, key=lambda item: item["score"])
    edge_weight = params.get("edge_weight", context.get("edge_weight", 0.35))

    updated_population = []
    for candidate in population:
        pull = (best["position"] - candidate["position"]) * edge_weight * best["mass"]
        jitter = rng.uniform(-0.15, 0.15)
        next_position = candidate["position"] + pull + jitter
        updated_population.append(
            {
                "position": next_position,
                "mass": candidate["mass"],
                "score": _score({"position": next_position}, context.get("target", 0.0)),
            }
        )

    context.set("population", updated_population)


def _merge_close_candidates(context: BallistaContext, params: dict[str, Any]) -> None:
    population: list[dict[str, float]] = sorted(
        context.get("population", []),
        key=lambda item: item["position"],
    )
    merge_distance = params.get("merge_distance", context.get("merge_distance", 0.9))

    if not population:
        return

    merged: list[dict[str, float]] = [population[0]]
    for candidate in population[1:]:
        previous = merged[-1]
        if abs(candidate["position"] - previous["position"]) <= merge_distance:
            total_mass = previous["mass"] + candidate["mass"]
            weighted_position = (
                (previous["position"] * previous["mass"])
                + (candidate["position"] * candidate["mass"])
            ) / total_mass
            merged[-1] = {
                "position": weighted_position,
                "mass": total_mass,
                "score": _score({"position": weighted_position}, context.get("target", 0.0)),
            }
            continue

        merged.append(candidate)

    context.set("population", merged)


def _local_search(context: BallistaContext, params: dict[str, Any]) -> None:
    rng = _get_rng(context)
    population: list[dict[str, float]] = context.get("population", [])
    target = context.get("target", 0.0)

    if not population:
        return

    best_index = min(range(len(population)), key=lambda index: population[index]["score"])
    best = population[best_index]

    step = params.get("local_search_step", context.get("local_search_step", 0.45))
    direction = -1.0 if best["position"] > target else 1.0
    candidate_position = best["position"] + (direction * step) + rng.uniform(-0.05, 0.05)
    candidate_score = _score({"position": candidate_position}, target)

    if candidate_score < best["score"]:
        population[best_index] = {
            "position": candidate_position,
            "mass": best["mass"],
            "score": candidate_score,
        }

    context.set("population", population)


def _update_best(context: BallistaContext, params: dict[str, Any]) -> None:
    del params
    population: list[dict[str, float]] = context.get("population", [])
    best = min(population, key=lambda item: item["score"])
    current_best = context.get("best")

    if current_best is None or best["score"] < current_best["score"]:
        context.set("best", dict(best))

    context.update_metric("best_score", context.get("best")["score"])
    context.update_metric("population_size", len(population))


def _should_stop(context: BallistaContext) -> bool:
    return context.metrics.get("best_score", 999.0) <= context.get("target_score", 0.1)


def _construct_labeled_solution(context: BallistaContext, params: dict[str, Any]) -> None:
    matrix = params.get("matrix", [])
    labels = params.get("labels", {})
    active_value = params.get("active_value", 1)
    output_slot = params.get("output_slot", "constructed_solution")

    constructed_solution = []
    for row_index, row in enumerate(matrix):
        active_targets = [index for index, value in enumerate(row) if value == active_value]
        label_key = str(row_index)
        constructed_solution.append(
            {
                "node_id": row_index,
                "label": labels.get(label_key, f"node_{row_index}"),
                "active_targets": active_targets,
                "connection_count": len(active_targets),
            }
        )

    context.set(output_slot, constructed_solution)
    context.update_metric(
        "dense_rows",
        sum(item["connection_count"] >= 2 for item in constructed_solution),
    )
    context.update_metric("matrix_rows", len(matrix))


def _decide_search_mode(context: BallistaContext, params: dict[str, Any]) -> None:
    solution = params.get("solution", context.get("constructed_solution", []))
    critical_label = params.get("critical_label", "critical")
    critical_threshold = params.get("critical_threshold", 2)
    dense_rows_threshold = params.get("dense_rows_threshold", 2)
    output_slot = params.get("output_slot", "search_mode")

    has_critical_cluster = any(
        item["label"] == critical_label and item["connection_count"] >= critical_threshold
        for item in solution
    )
    dense_rows = context.metrics.get("dense_rows", 0)
    mode = "intensify" if has_critical_cluster or dense_rows >= dense_rows_threshold else "diversify"

    context.set(output_slot, mode)
    context.update_metric("critical_cluster_detected", has_critical_cluster)


def _apply_intensify_strategy(context: BallistaContext, params: dict[str, Any]) -> None:
    strategy = {
        "phase": "intensify",
        "local_search_weight": params.get("local_search_weight", 0.85),
        "merge_bias": params.get("merge_bias", "high"),
    }
    context.set(params.get("output_slot", "next_strategy"), strategy)


def _apply_diversify_strategy(context: BallistaContext, params: dict[str, Any]) -> None:
    strategy = {
        "phase": "diversify",
        "shake_strength": params.get("shake_strength", 0.55),
        "restart_bias": params.get("restart_bias", "medium"),
    }
    context.set(params.get("output_slot", "next_strategy"), strategy)


def build_builtin_registry() -> OperatorRegistry:
    registry = OperatorRegistry()
    registry.register_operator("initialize_population", _initialize_population)
    registry.register_operator("apply_attraction", _apply_attraction)
    registry.register_operator("merge_close_candidates", _merge_close_candidates)
    registry.register_operator("local_search", _local_search)
    registry.register_operator("update_best", _update_best)
    registry.register_operator("construct_labeled_solution", _construct_labeled_solution)
    registry.register_operator("decide_search_mode", _decide_search_mode)
    registry.register_operator("apply_intensify_strategy", _apply_intensify_strategy)
    registry.register_operator("apply_diversify_strategy", _apply_diversify_strategy)
    registry.register_stop_condition("target_score_reached", _should_stop)
    return registry


def build_astro_demo(seed: int = 7) -> tuple[Algorithm, dict[str, Any]]:
    setup = PythonNode(
        name="initialize_population",
        handler=_initialize_population,
        message="initial population created",
        snapshot_keys=["population", "best"],
    )
    iteration_body = SequenceNode.from_iterable(
        "astro_iteration",
        [
            PythonNode(
                name="apply_attraction",
                handler=_apply_attraction,
                message="population pulled toward the strongest body",
                snapshot_keys=["population"],
            ),
            PythonNode(
                name="merge_close_candidates",
                handler=_merge_close_candidates,
                message="nearby bodies merged into heavier candidates",
                snapshot_keys=["population"],
            ),
            PythonNode(
                name="local_search",
                handler=_local_search,
                message="best candidate refined with local search",
                snapshot_keys=["population"],
            ),
            PythonNode(
                name="update_best",
                handler=_update_best,
                message="best candidate updated",
                snapshot_keys=["best"],
            ),
        ],
    )
    root = SequenceNode.from_iterable(
        "astro_algorithm",
        [
            setup,
            LoopNode(
                name="optimization_loop",
                body=iteration_body,
                max_iterations=20,
                stop_condition=_should_stop,
            ),
        ],
    )

    return (
        Algorithm(
            name="astro_demo",
            root=root,
            description="Toy attraction-and-merge metaheuristic prototype",
        ),
        {
            "rng_seed": seed,
            "target": 3.5,
            "target_score": 0.1,
            "population_size": 10,
            "edge_weight": 0.24,
            "merge_distance": 0.8,
            "local_search_step": 0.3,
        },
    )
