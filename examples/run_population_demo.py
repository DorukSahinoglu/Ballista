from __future__ import annotations

from pathlib import Path

from ballista import AlgorithmEngine, load_algorithm_definition_file
from ballista.examples import build_builtin_registry


def main() -> None:
    definition_path = Path(__file__).with_name("population_search_definition.json")
    loaded = load_algorithm_definition_file(definition_path, build_builtin_registry())
    result = AlgorithmEngine().run(
        loaded.algorithm,
        initial_slots=loaded.initial_slots,
        slot_schema=loaded.slot_schema,
    )

    best = result.get("best", {})
    summary = result.get("population_summary", {})
    print(f"Algorithm: {loaded.algorithm.name}")
    print(f"Iterations: {result.iteration}")
    print(f"Population size: {summary.get('population_size')}")
    print(f"Best score: {summary.get('best_score')}")
    print(f"Average score: {summary.get('avg_score')}")
    print(f"Diversity span: {summary.get('diversity_span')}")
    print(f"Selection policy: {result.metrics.get('selection_policy')}")
    print(f"Recombination policy: {result.metrics.get('recombination_policy')}")
    print(f"Acceptance policy: {result.metrics.get('acceptance_policy')}")
    print(f"Restart mode: {result.metrics.get('restart_mode')}")
    print(f"Selected size: {len(result.get('selected_population', []))}")
    print(f"Recombined size: {len(result.get('recombined_population', []))}")
    print(f"Elite size: {len(result.get('elite_population', []))}")
    print(f"Mutated size: {len(result.get('mutated_population', []))}")
    print(f"Accepted size: {len(result.get('accepted_population', []))}")
    print(f"Best candidate: {best}")


if __name__ == "__main__":
    main()
