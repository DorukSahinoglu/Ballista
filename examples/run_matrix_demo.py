from __future__ import annotations

from pathlib import Path

from ballista import AlgorithmEngine, load_algorithm_definition_file
from ballista.examples import build_builtin_registry


def main() -> None:
    definition_path = Path(__file__).with_name("labeled_matrix_definition.json")
    loaded = load_algorithm_definition_file(definition_path, build_builtin_registry())
    result = AlgorithmEngine().run(
        loaded.algorithm,
        initial_slots=loaded.initial_slots,
        slot_schema=loaded.slot_schema,
    )

    print(f"Algorithm: {loaded.algorithm.name}")
    print("Slot schema:")
    for slot_name, definition in loaded.slot_schema.items():
        print(
            f"- {slot_name}: kind={definition.kind} "
            f"representation={definition.representation}"
        )

    print("")
    print(f"Search mode: {result.get('search_mode')}")
    print(f"Heuristic score: {result.get('heuristic_score')}")
    print(f"Priority nodes: {len(result.get('priority_nodes', []))}")
    print(f"Next strategy: {result.get('next_strategy')}")
    print(f"Dense rows: {result.metrics.get('dense_rows')}")


if __name__ == "__main__":
    main()
