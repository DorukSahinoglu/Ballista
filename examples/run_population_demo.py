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
    print(f"Problem family: {result.get('problem_family')}")
    print(f"Schedule progress: {result.get('schedule_progress')}")
    print(f"Phase label: {result.get('phase_label')}")
    print(f"Regime label: {result.get('regime_label')}")
    print(f"Mutation scale: {result.get('mutation_scale')}")
    print(f"Directional scale: {result.get('directional_scale')}")
    print(f"Restart mode slot: {result.get('restart_mode')}")
    print(f"Minimum distance: {result.get('minimum_distance')}")
    print(f"Annealing temperature: {result.get('annealing_temperature')}")
    print(f"Selection policy slot: {result.get('selection_policy')}")
    print(f"Acceptance policy slot: {result.get('acceptance_policy')}")
    print(f"Response mode: {result.get('response_mode')}")
    print(f"Response history: {result.get('response_history')}")
    print(f"Selection policy history: {result.get('selection_policy_history')}")
    print(f"Acceptance policy history: {result.get('acceptance_policy_history')}")
    print(f"Restart mode history: {result.get('restart_mode_history')}")
    print(f"Phase history: {result.get('phase_history')}")
    print(f"Regime history: {result.get('regime_history')}")
    print(f"Response usage profile: {result.get('response_usage_profile')}")
    print(f"Selection policy usage profile: {result.get('selection_policy_usage_profile')}")
    print(f"Response credit profile: {result.get('response_credit_profile')}")
    print(f"Response blame profile: {result.get('response_blame_profile')}")
    print(f"Delayed response credit profile: {result.get('delayed_response_credit_profile')}")
    print(f"Delayed response blame profile: {result.get('delayed_response_blame_profile')}")
    print(f"Current regime response balance profile: {result.get('current_regime_response_balance_profile')}")
    print(f"Current regime response family balance profile: {result.get('current_regime_response_family_balance_profile')}")
    print(f"Online library weight profile: {result.get('online_library_weight_profile')}")
    print(f"Online exploration signal: {result.get('online_exploration_signal')}")
    print(f"Exploration quota: {result.get('exploration_quota')}")
    print(f"Best score outcome history: {result.get('best_score_outcome_history')}")
    print(f"Response outcome events: {result.get('response_outcome_events')}")
    print(f"Response effectiveness profile: {result.get('response_effectiveness_profile')}")
    print(f"Phase response effectiveness profile: {result.get('phase_response_effectiveness_profile')}")
    print(f"Regime response effectiveness profile: {result.get('regime_response_effectiveness_profile')}")
    print(f"Mixed response library: {result.get('mixed_response_library')}")
    print(f"Active response library: {result.get('active_response_library')}")
    print(f"Response candidates: {result.get('response_candidates')}")
    print(f"Selected response candidate: {result.get('selected_response_candidate')}")
    print(f"Best score trend: {result.get('best_score_trend')}")
    print(f"Diversity trend: {result.get('diversity_trend')}")
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
