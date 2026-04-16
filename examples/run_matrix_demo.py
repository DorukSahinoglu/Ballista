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
    print(f"Degree view entries: {len(result.get('degree_view', []))}")
    print(f"Critical neighbors: {len(result.get('critical_neighbors', []))}")
    print(f"Connected components: {len(result.get('connected_components', []))}")
    print(f"Edge pairs: {len(result.get('edge_pairs', []))}")
    print(f"Critical reach entries: {len(result.get('critical_reach', []))}")
    print(f"Critical signal profile: {len(result.get('critical_signal_profile', []))}")
    print(f"Random walk trace length: {len(result.get('critical_random_walk', {}).get('trace', []))}")
    print(f"Flow successful paths: {result.get('entry_flow_profile', {}).get('successful_path_count')}")
    print(f"Triangle patterns: {len(result.get('triangle_patterns', []))}")
    print(f"Centrality entries: {len(result.get('centrality_profile', []))}")
    print(f"Closeness entries: {len(result.get('closeness_profile', []))}")
    print(f"Policy walk unique visits: {result.get('critical_policy_walk', {}).get('unique_visits')}")
    print(f"Square patterns: {len(result.get('square_patterns', []))}")
    print(f"Star patterns: {len(result.get('star_patterns', []))}")
    print(f"Weighted band neighbors: {len(result.get('weighted_band_neighbors', []))}")
    print(f"Weighted degree entries: {len(result.get('weighted_degree_view', []))}")
    print(f"Activated weighted edges: {len(result.get('activated_weighted_edges', []))}")
    print(f"Weighted cost path reachable: {result.get('weighted_cost_path', {}).get('reachable')}")
    print(f"Weighted edge strengths: {len(result.get('weighted_edge_strengths', []))}")
    print(f"Weighted policy walk unique visits: {result.get('weighted_policy_walk', {}).get('unique_visits')}")
    print(f"Priority nodes: {len(result.get('priority_nodes', []))}")
    print(f"Priority groups: {list(result.get('priority_groups', {}).keys())}")
    print(f"Priority summary: {result.get('priority_summary')}")
    print(f"Window profiles: {len(result.get('window_profiles', []))}")
    ranked = result.get("ranked_priority_nodes", [])
    degree_view = result.get("degree_view", [])
    components = result.get("connected_components", [])
    top_degree = max(degree_view, key=lambda item: item["degree"]) if degree_view else None
    print(f"Top priority node: {ranked[0]['label'] if ranked else 'none'}")
    print(f"Top degree node: {top_degree['label'] if top_degree else 'none'}")
    print(f"Largest component size: {max((item['size'] for item in components), default=0)}")
    print(f"Critical-entry overlap: {result.get('critical_entry_overlap')}")
    print(f"Entry-explorer path: {result.get('entry_to_explorer_path')}")
    print(f"Critical random walk: {result.get('critical_random_walk')}")
    print(f"Entry flow profile: {result.get('entry_flow_profile')}")
    print(f"Centrality profile: {result.get('centrality_profile')}")
    print(f"Closeness profile: {result.get('closeness_profile')}")
    print(f"Critical policy walk: {result.get('critical_policy_walk')}")
    print(f"Weighted band neighbors detail: {result.get('weighted_band_neighbors')}")
    print(f"Weighted degree view: {result.get('weighted_degree_view')}")
    print(f"Activated weighted edges detail: {result.get('activated_weighted_edges')}")
    print(f"Weighted entry-explorer path: {result.get('weighted_entry_to_explorer_path')}")
    print(f"Weighted cost path: {result.get('weighted_cost_path')}")
    print(f"Weighted edge strengths detail: {result.get('weighted_edge_strengths')}")
    print(f"Weighted policy walk: {result.get('weighted_policy_walk')}")
    print(f"Next strategy: {result.get('next_strategy')}")
    print(f"Dense rows: {result.metrics.get('dense_rows')}")


if __name__ == "__main__":
    main()
