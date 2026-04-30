from __future__ import annotations

import math
import random
from typing import Any

from .engine import Algorithm
from .models import BallistaContext
from .registry import OperatorParamSchema, OperatorRegistry
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


def _select_top_population(context: BallistaContext, params: dict[str, Any]) -> None:
    population: list[dict[str, float]] = params.get("population", context.get("population", []))
    selection_size = int(params.get("selection_size", 3))
    output_slot = params.get("output_slot", "elite_population")

    if selection_size <= 0:
        raise ValueError("select_top_population expects selection_size > 0")

    elites = [dict(item) for item in sorted(population, key=lambda item: item["score"])[:selection_size]]
    context.set(output_slot, elites)
    context.update_metric("elite_population_size", len(elites))


def _select_population_batch(context: BallistaContext, params: dict[str, Any]) -> None:
    rng = _get_rng(context)
    population: list[dict[str, float]] = params.get("population", context.get("population", []))
    selection_size = int(params.get("selection_size", 3))
    selection_policy = params.get("selection_policy", "top")
    tournament_size = int(params.get("tournament_size", 2))
    output_slot = params.get("output_slot", "selected_population")

    if selection_size <= 0:
        raise ValueError("select_population_batch expects selection_size > 0")
    if tournament_size <= 0:
        raise ValueError("select_population_batch expects tournament_size > 0")
    if not population:
        context.set(output_slot, [])
        context.update_metric("selection_policy", selection_policy)
        context.update_metric("selected_population_size", 0)
        return

    if selection_policy == "top":
        selected = [dict(item) for item in sorted(population, key=lambda item: item["score"])[:selection_size]]
    elif selection_policy == "tournament":
        selected = []
        sample_size = min(tournament_size, len(population))
        for _ in range(selection_size):
            contenders = rng.sample(population, sample_size)
            selected.append(dict(min(contenders, key=lambda item: item["score"])))
    elif selection_policy == "roulette":
        weights = [1.0 / (item["score"] + 1e-6) for item in population]
        selected = [dict(item) for item in rng.choices(population, weights=weights, k=selection_size)]
    elif selection_policy == "rank":
        ranked_population = sorted(population, key=lambda item: item["score"])
        weights = list(range(len(ranked_population), 0, -1))
        selected = [dict(item) for item in rng.choices(ranked_population, weights=weights, k=selection_size)]
    else:
        raise ValueError(f"Unsupported selection_policy '{selection_policy}'")

    context.set(output_slot, selected)
    context.update_metric("selection_policy", selection_policy)
    context.update_metric("selected_population_size", len(selected))


def _mutate_population(context: BallistaContext, params: dict[str, Any]) -> None:
    rng = _get_rng(context)
    population: list[dict[str, float]] = params.get("population", context.get("elite_population", []))
    clones_per_candidate = int(params.get("clones_per_candidate", 2))
    mutation_scale = float(params.get("mutation_scale", 0.45))
    target = params.get("target", context.get("target", 0.0))
    output_slot = params.get("output_slot", "mutated_population")

    if clones_per_candidate <= 0:
        raise ValueError("mutate_population expects clones_per_candidate > 0")

    mutated_population = []
    for candidate in population:
        for _ in range(clones_per_candidate):
            next_position = candidate["position"] + rng.uniform(-mutation_scale, mutation_scale)
            mutated_population.append(
                {
                    "position": next_position,
                    "mass": candidate.get("mass", 1.0),
                    "score": _score({"position": next_position}, target),
                    "origin": "mutation",
                }
            )

    context.set(output_slot, mutated_population)
    context.update_metric("mutated_population_size", len(mutated_population))


def _recombine_population(context: BallistaContext, params: dict[str, Any]) -> None:
    rng = _get_rng(context)
    parents: list[dict[str, float]] = params.get("parents", context.get("selected_population", []))
    offspring_count = int(params.get("offspring_count", max(len(parents), 0)))
    pairing_policy = params.get("pairing_policy", "sequential")
    recombination_policy = params.get("recombination_policy", "blend")
    blend_bias = float(params.get("blend_bias", 0.5))
    directional_scale = float(params.get("directional_scale", 0.35))
    jitter_scale = float(params.get("jitter_scale", 0.15))
    target = params.get("target", context.get("target", 0.0))
    output_slot = params.get("output_slot", "recombined_population")

    if offspring_count < 0:
        raise ValueError("recombine_population expects offspring_count >= 0")
    if len(parents) < 2 or offspring_count == 0:
        context.set(output_slot, [])
        context.update_metric("recombined_population_size", 0)
        return

    if not 0.0 <= blend_bias <= 1.0:
        raise ValueError("recombine_population expects 0 <= blend_bias <= 1")
    if directional_scale < 0.0:
        raise ValueError("recombine_population expects directional_scale >= 0")

    offspring = []
    ordered_parents = list(parents)
    if pairing_policy == "random":
        rng.shuffle(ordered_parents)
    elif pairing_policy != "sequential":
        raise ValueError(f"Unsupported pairing_policy '{pairing_policy}'")

    for index in range(offspring_count):
        if pairing_policy == "random":
            left_parent, right_parent = rng.sample(parents, 2)
        else:
            left_parent = ordered_parents[index % len(ordered_parents)]
            right_parent = ordered_parents[(index + 1) % len(ordered_parents)]

        if recombination_policy == "blend":
            alpha = min(max(blend_bias + rng.uniform(-0.12, 0.12), 0.0), 1.0)
            next_position = (
                (left_parent["position"] * alpha)
                + (right_parent["position"] * (1.0 - alpha))
                + rng.uniform(-jitter_scale, jitter_scale)
            )
        elif recombination_policy == "midpoint":
            midpoint = (left_parent["position"] + right_parent["position"]) / 2.0
            next_position = midpoint + rng.uniform(-jitter_scale, jitter_scale)
        elif recombination_policy == "directional":
            if left_parent["score"] <= right_parent["score"]:
                anchor = left_parent
                peer = right_parent
            else:
                anchor = right_parent
                peer = left_parent
            drift = (anchor["position"] - peer["position"]) * directional_scale
            next_position = anchor["position"] + drift + rng.uniform(-jitter_scale, jitter_scale)
        else:
            raise ValueError(f"Unsupported recombination_policy '{recombination_policy}'")

        offspring.append(
            {
                "position": next_position,
                "mass": (left_parent.get("mass", 1.0) + right_parent.get("mass", 1.0)) / 2.0,
                "score": _score({"position": next_position}, target),
                "origin": "recombination",
                "parents": [left_parent["position"], right_parent["position"]],
                "recombination_policy": recombination_policy,
            }
        )

    context.set(output_slot, offspring)
    context.update_metric("recombination_policy", recombination_policy)
    context.update_metric("recombined_population_size", len(offspring))


def _restart_population(context: BallistaContext, params: dict[str, Any]) -> None:
    rng = _get_rng(context)
    elites: list[dict[str, float]] = [dict(item) for item in params.get("elites", context.get("elite_population", []))]
    candidates: list[dict[str, float]] = [
        dict(item) for item in params.get("candidates", context.get("mutated_population", []))
    ]
    target_population_size = int(params.get("target_population_size", context.get("population_size", 8)))
    target = params.get("target", context.get("target", 0.0))
    min_position = float(params.get("min_position", -12.0))
    max_position = float(params.get("max_position", 12.0))
    restart_mode = params.get("restart_mode", "elite_biased")
    output_slot = params.get("output_slot", "population")

    if target_population_size <= 0:
        raise ValueError("restart_population expects target_population_size > 0")
    if min_position >= max_position:
        raise ValueError("restart_population expects min_position < max_position")

    combined_population = sorted(elites + candidates, key=lambda item: item["score"])[:target_population_size]

    while len(combined_population) < target_population_size:
        if restart_mode == "uniform" or not combined_population:
            next_position = rng.uniform(min_position, max_position)
        else:
            anchor = rng.choice(combined_population)
            span = max((max_position - min_position) * 0.2, 0.1)
            next_position = anchor["position"] + rng.uniform(-span, span)
            next_position = max(min_position, min(max_position, next_position))

        combined_population.append(
            {
                "position": next_position,
                "mass": 1.0,
                "score": _score({"position": next_position}, target),
                "origin": "restart",
            }
        )

    context.set(output_slot, combined_population[:target_population_size])
    context.update_metric("restart_mode", restart_mode)
    context.update_metric("population_size", len(combined_population[:target_population_size]))


def _accept_population_candidates(context: BallistaContext, params: dict[str, Any]) -> None:
    rng = _get_rng(context)
    current_population: list[dict[str, float]] = [
        dict(item) for item in params.get("current_population", context.get("population", []))
    ]
    candidates: list[dict[str, float]] = [
        dict(item) for item in params.get("candidates", context.get("mutated_population", []))
    ]
    acceptance_policy = params.get("acceptance_policy", "best")
    acceptance_threshold = float(params.get("acceptance_threshold", float("inf")))
    annealing_temperature = float(params.get("annealing_temperature", 0.25))
    minimum_distance = float(params.get("minimum_distance", 0.0))
    target_population_size = int(
        params.get("target_population_size", max(len(current_population), len(candidates), 0))
    )
    output_slot = params.get("output_slot", "accepted_population")

    if target_population_size < 0:
        raise ValueError("accept_population_candidates expects target_population_size >= 0")

    if acceptance_policy == "best":
        accepted = sorted(current_population + candidates, key=lambda item: item["score"])[:target_population_size]
    elif acceptance_policy == "improving":
        accepted = sorted(current_population, key=lambda item: item["score"])[:target_population_size]
        for candidate in sorted(candidates, key=lambda item: item["score"]):
            if not accepted:
                accepted.append(candidate)
                continue
            if candidate["score"] < accepted[-1]["score"]:
                accepted[-1] = candidate
                accepted.sort(key=lambda item: item["score"])
        accepted = accepted[:target_population_size]
    elif acceptance_policy == "threshold":
        threshold_accepted = [item for item in candidates if item["score"] <= acceptance_threshold]
        accepted = sorted(current_population + threshold_accepted, key=lambda item: item["score"])[:target_population_size]
    elif acceptance_policy == "annealed":
        accepted = sorted(current_population, key=lambda item: item["score"])[:target_population_size]
        for candidate in sorted(candidates, key=lambda item: item["score"]):
            if len(accepted) < target_population_size:
                accepted.append(candidate)
                accepted.sort(key=lambda item: item["score"])
                continue
            if not accepted:
                accepted.append(candidate)
                continue
            worst_score = accepted[-1]["score"]
            delta = candidate["score"] - worst_score
            should_accept = delta <= 0
            if not should_accept:
                temperature = max(annealing_temperature, 1e-6)
                acceptance_probability = math.exp(-delta / temperature)
                should_accept = rng.random() <= acceptance_probability
            if should_accept:
                accepted[-1] = candidate
                accepted.sort(key=lambda item: item["score"])
        accepted = accepted[:target_population_size]
    elif acceptance_policy == "diversity_guarded":
        accepted = []
        combined = sorted(current_population + candidates, key=lambda item: item["score"])
        for candidate in combined:
            if len(accepted) >= target_population_size:
                break
            if all(
                abs(candidate["position"] - existing["position"]) >= minimum_distance
                for existing in accepted
            ):
                accepted.append(candidate)
        if len(accepted) < target_population_size:
            for candidate in combined:
                if len(accepted) >= target_population_size:
                    break
                if candidate not in accepted:
                    accepted.append(candidate)
    else:
        raise ValueError(f"Unsupported acceptance_policy '{acceptance_policy}'")

    context.set(output_slot, accepted)
    context.update_metric("acceptance_policy", acceptance_policy)
    context.update_metric("accepted_population_size", len(accepted))


def _summarize_population(context: BallistaContext, params: dict[str, Any]) -> None:
    population: list[dict[str, float]] = params.get("population", context.get("population", []))
    output_slot = params.get("output_slot", "population_summary")
    best_output_slot = params.get("best_output_slot", "best")

    if not population:
        summary = {
            "population_size": 0,
            "best_score": None,
            "worst_score": None,
            "avg_score": None,
            "diversity_span": 0.0,
        }
        context.set(output_slot, summary)
        return

    best = min(population, key=lambda item: item["score"])
    worst = max(population, key=lambda item: item["score"])
    avg_score = sum(item["score"] for item in population) / len(population)
    diversity_span = max(item["position"] for item in population) - min(item["position"] for item in population)

    current_best = context.get(best_output_slot)
    if current_best is None or best["score"] < current_best["score"]:
        context.set(best_output_slot, dict(best))

    summary = {
        "population_size": len(population),
        "best_score": round(best["score"], 6),
        "worst_score": round(worst["score"], 6),
        "avg_score": round(avg_score, 6),
        "diversity_span": round(diversity_span, 6),
    }
    context.set(output_slot, summary)
    context.update_metric("best_score", context.get(best_output_slot)["score"])
    context.update_metric("population_size", len(population))
    context.update_metric("avg_population_score", summary["avg_score"])
    context.update_metric("population_diversity_span", summary["diversity_span"])


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


def _set_slot_value(context: BallistaContext, params: dict[str, Any]) -> None:
    context.set(params["slot"], params.get("value"))


def build_builtin_registry() -> OperatorRegistry:
    registry = OperatorRegistry()
    registry.register_operator(
        "initialize_population",
        _initialize_population,
        params=[
            OperatorParamSchema(name="target"),
            OperatorParamSchema(name="population_size"),
        ],
    )
    registry.register_operator(
        "apply_attraction",
        _apply_attraction,
        params=[OperatorParamSchema(name="edge_weight")],
    )
    registry.register_operator(
        "merge_close_candidates",
        _merge_close_candidates,
        params=[OperatorParamSchema(name="merge_distance")],
    )
    registry.register_operator(
        "local_search",
        _local_search,
        params=[OperatorParamSchema(name="local_search_step")],
    )
    registry.register_operator("update_best", _update_best)
    registry.register_operator(
        "select_top_population",
        _select_top_population,
        params=[
            OperatorParamSchema(name="population", slot_kinds=["object_collection"]),
            OperatorParamSchema(name="selection_size"),
            OperatorParamSchema(name="output_slot"),
        ],
    )
    registry.register_operator(
        "mutate_population",
        _mutate_population,
        params=[
            OperatorParamSchema(name="population", slot_kinds=["object_collection"]),
            OperatorParamSchema(name="clones_per_candidate"),
            OperatorParamSchema(name="mutation_scale"),
            OperatorParamSchema(name="target"),
            OperatorParamSchema(name="output_slot"),
        ],
    )
    registry.register_operator(
        "select_population_batch",
        _select_population_batch,
        params=[
            OperatorParamSchema(name="population", slot_kinds=["object_collection"]),
            OperatorParamSchema(name="selection_size"),
            OperatorParamSchema(name="selection_policy"),
            OperatorParamSchema(name="tournament_size"),
            OperatorParamSchema(name="output_slot"),
        ],
    )
    registry.register_operator(
        "recombine_population",
        _recombine_population,
        params=[
            OperatorParamSchema(name="parents", slot_kinds=["object_collection"]),
            OperatorParamSchema(name="offspring_count"),
            OperatorParamSchema(name="pairing_policy"),
            OperatorParamSchema(name="recombination_policy"),
            OperatorParamSchema(name="blend_bias"),
            OperatorParamSchema(name="directional_scale"),
            OperatorParamSchema(name="jitter_scale"),
            OperatorParamSchema(name="target"),
            OperatorParamSchema(name="output_slot"),
        ],
    )
    registry.register_operator(
        "restart_population",
        _restart_population,
        params=[
            OperatorParamSchema(name="elites", slot_kinds=["object_collection"]),
            OperatorParamSchema(name="candidates", slot_kinds=["object_collection"]),
            OperatorParamSchema(name="target_population_size"),
            OperatorParamSchema(name="target"),
            OperatorParamSchema(name="min_position"),
            OperatorParamSchema(name="max_position"),
            OperatorParamSchema(name="restart_mode"),
            OperatorParamSchema(name="output_slot"),
        ],
    )
    registry.register_operator(
        "accept_population_candidates",
        _accept_population_candidates,
        params=[
            OperatorParamSchema(name="current_population", slot_kinds=["object_collection"]),
            OperatorParamSchema(name="candidates", slot_kinds=["object_collection"]),
            OperatorParamSchema(name="acceptance_policy"),
            OperatorParamSchema(name="acceptance_threshold"),
            OperatorParamSchema(name="annealing_temperature"),
            OperatorParamSchema(name="minimum_distance"),
            OperatorParamSchema(name="target_population_size"),
            OperatorParamSchema(name="output_slot"),
        ],
    )
    registry.register_operator(
        "summarize_population",
        _summarize_population,
        params=[
            OperatorParamSchema(name="population", slot_kinds=["object_collection"]),
            OperatorParamSchema(name="output_slot"),
            OperatorParamSchema(name="best_output_slot"),
        ],
    )
    registry.register_operator(
        "construct_labeled_solution",
        _construct_labeled_solution,
        params=[
            OperatorParamSchema(
                name="matrix",
                required=True,
                slot_kinds=["matrix"],
            ),
            OperatorParamSchema(
                name="labels",
                required=True,
                slot_kinds=["mapping"],
            ),
            OperatorParamSchema(name="active_value"),
            OperatorParamSchema(name="output_slot"),
        ],
    )
    registry.register_operator(
        "decide_search_mode",
        _decide_search_mode,
        params=[
            OperatorParamSchema(
                name="solution",
                required=True,
                slot_kinds=["object_collection"],
            ),
            OperatorParamSchema(name="critical_label"),
            OperatorParamSchema(name="critical_threshold"),
            OperatorParamSchema(name="dense_rows_threshold"),
            OperatorParamSchema(name="output_slot"),
        ],
    )
    registry.register_operator(
        "apply_intensify_strategy",
        _apply_intensify_strategy,
        params=[
            OperatorParamSchema(name="local_search_weight"),
            OperatorParamSchema(name="merge_bias"),
            OperatorParamSchema(name="output_slot"),
        ],
    )
    registry.register_operator(
        "apply_diversify_strategy",
        _apply_diversify_strategy,
        params=[
            OperatorParamSchema(name="shake_strength"),
            OperatorParamSchema(name="restart_bias"),
            OperatorParamSchema(name="output_slot"),
        ],
    )
    registry.register_operator(
        "set_slot_value",
        _set_slot_value,
        params=[
            OperatorParamSchema(name="slot", required=True),
            OperatorParamSchema(name="value", required=True),
        ],
    )
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
