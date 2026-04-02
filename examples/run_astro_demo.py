from __future__ import annotations

from ballista import AlgorithmEngine
from ballista.examples import build_astro_demo


def main() -> None:
    algorithm, initial_slots = build_astro_demo()
    result = AlgorithmEngine().run(algorithm, initial_slots=initial_slots)

    best = result.get("best")
    print(f"Algorithm: {algorithm.name}")
    print(f"Iterations: {result.iteration}")
    print(f"Best position: {best['position']:.4f}")
    print(f"Best score: {best['score']:.4f}")
    print(f"Population size: {result.metrics.get('population_size')}")
    print("")
    print("Recent history:")
    for record in result.history[-5:]:
        print(f"- iter={record.iteration} node={record.node} message={record.message}")


if __name__ == "__main__":
    main()
