from __future__ import annotations

from pathlib import Path

from ballista import AlgorithmEngine, load_algorithm_definition_file
from ballista.examples import build_builtin_registry


def main() -> None:
    definition_path = Path(__file__).with_name("astro_definition.json")
    loaded = load_algorithm_definition_file(definition_path, build_builtin_registry())
    result = AlgorithmEngine().run(
        loaded.algorithm,
        initial_slots=loaded.initial_slots,
        slot_schema=loaded.slot_schema,
    )

    best = result.get("best")
    print(f"Algorithm: {loaded.algorithm.name}")
    print(f"Iterations: {result.iteration}")
    print(f"Best position: {best['position']:.4f}")
    print(f"Best score: {best['score']:.4f}")
    print(f"Population size: {result.metrics.get('population_size')}")


if __name__ == "__main__":
    main()
