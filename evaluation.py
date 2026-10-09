
"""
Outbreak of Lies - Evaluation and Experiments Module

Evaluates intervention strategies by running repeated rumour
simulations and comparing their effectiveness.

Strategies:
1. No intervention
2. Random selection
3. Degree centrality
4. Betweenness centrality
5. Greedy influence minimization
"""

from numbers import Integral, Real
from statistics import mean, pstdev

import networkx as nx

from rumor_simulator import simulate_spread
from intervention import select_interventions


DEFAULT_STRATEGIES = [
    "random",
    "degree",
    "betweenness",
    "greedy",
]


def evaluate_strategies(
    graph,
    source,
    k=5,
    strategies=None,
    n_runs=100,
    transmission_prob=0.3,
    max_rounds=50,
    seed=42,
    greedy_runs=30,
    blocked_nodes=None,
):
    """
    Compare intervention strategies over repeated simulations.

    Parameters
    ----------
    graph : networkx.Graph
        Social network used for every strategy.

    source : hashable
        User who starts the rumour.

    k : int
        Number of additional users selected for intervention.

    strategies : list, optional
        Strategies to evaluate. Defaults to random, degree,
        betweenness and greedy.

    n_runs : int
        Number of repeated propagation simulations per strategy.

    transmission_prob : float
        Probability of spreading the rumour across an edge.

    max_rounds : int
        Maximum number of spreading rounds.

    seed : int or None
        Base random seed for reproducibility.

    greedy_runs : int
        Number of simulations used internally by greedy selection
        to estimate the benefit of each candidate.

    blocked_nodes : iterable, optional
        Users already blocked before the additional intervention.

    Returns
    -------
    dict
        summary: Average reach, standard deviation, minimum reach,
                 maximum reach and reduction percentage.

        raw_results: Results of individual simulation runs.

        selected_users: Intervention targets selected in each run.
    """

    # ---------------------------------------------------------
    # 1. Validate inputs
    # ---------------------------------------------------------
    if not isinstance(graph, nx.Graph):
        raise TypeError("graph must be a NetworkX graph.")

    if graph.number_of_nodes() == 0:
        raise ValueError("graph must contain at least one user.")

    if source not in graph:
        raise ValueError("source must exist in the graph.")

    if (
        isinstance(k, bool)
        or not isinstance(k, Integral)
        or k < 0
    ):
        raise ValueError("k must be a non-negative integer.")

    if (
        isinstance(n_runs, bool)
        or not isinstance(n_runs, Integral)
        or n_runs < 1
    ):
        raise ValueError("n_runs must be a positive integer.")

    if (
        isinstance(greedy_runs, bool)
        or not isinstance(greedy_runs, Integral)
        or greedy_runs < 1
    ):
        raise ValueError("greedy_runs must be a positive integer.")

    if (
        isinstance(transmission_prob, bool)
        or not isinstance(transmission_prob, Real)
        or not 0 <= transmission_prob <= 1
    ):
        raise ValueError(
            "transmission_prob must be between 0 and 1."
        )

    if (
        isinstance(max_rounds, bool)
        or not isinstance(max_rounds, Integral)
        or max_rounds < 0
    ):
        raise ValueError(
            "max_rounds must be a non-negative integer."
        )

    if seed is not None and (
        isinstance(seed, bool)
        or not isinstance(seed, Integral)
    ):
        raise ValueError("seed must be an integer or None.")

    if strategies is None:
        strategies = DEFAULT_STRATEGIES.copy()
    else:
        strategies = list(strategies)

    strategies = [strategy.lower().strip() for strategy in strategies]

    allowed = set(DEFAULT_STRATEGIES)

    if len(strategies) != len(set(strategies)):
        raise ValueError("Duplicate strategies are not allowed.")

    invalid = set(strategies) - allowed

    if invalid:
        raise ValueError(
            f"Unknown strategies: {sorted(invalid)}"
        )

    if "greedy" in strategies and source is None:
        raise ValueError("Greedy evaluation requires a source.")

    if source in set(blocked_nodes or []):
        raise ValueError("The rumour source cannot be pre-blocked.")

    base_blocked = set(blocked_nodes or [])
    unknown_blocked = base_blocked - set(graph.nodes)

    if unknown_blocked:
        raise ValueError(
            f"Unknown blocked users: {unknown_blocked!r}"
        )

    # ---------------------------------------------------------
    # 2. Prepare storage
    # ---------------------------------------------------------
    strategies_to_run = ["no_intervention"] + strategies

    raw_results = []
    selected_users = {
        strategy: [] for strategy in strategies_to_run
    }

    # ---------------------------------------------------------
    # 3. Run repeated experiments
    # ---------------------------------------------------------
    for run in range(n_runs):

        # The same propagation seed is used for every strategy
        # within this run, making comparisons more consistent.
        run_seed = (
            seed + run if seed is not None else None
        )

        for strategy in strategies_to_run:

            # No additional intervention is the baseline.
            if strategy == "no_intervention":
                targets = []

            else:
                config = {
                    "source": source,
                    "transmission_prob": transmission_prob,
                    "max_rounds": max_rounds,
                    "seed": run_seed,
                    "blocked_nodes": base_blocked,
                    "n_runs": greedy_runs,
                }

                targets = select_interventions(
                    graph=graph,
                    k=k,
                    strategy=strategy,
                    simulator_config=config,
                )

            # Combine previously blocked users with the newly
            # selected intervention targets.
            all_blocked = base_blocked | set(targets)

            result = simulate_spread(
                graph=graph,
                source=source,
                transmission_prob=transmission_prob,
                blocked_nodes=all_blocked,
                max_rounds=max_rounds,
                seed=run_seed,
            )

            raw_results.append({
                "run": run + 1,
                "strategy": strategy,
                "final_reach": result["final_reach"],
                "reached_fraction": result["reached_fraction"],
                "intervention_count": len(targets),
                "intervention_users": list(targets),
                "spread_history": result["spread_history"],
                "rounds": result["rounds"],
            })

            selected_users[strategy].append(list(targets))

    # ---------------------------------------------------------
    # 4. Calculate summary metrics
    # ---------------------------------------------------------
    baseline_reaches = [
        row["final_reach"]
        for row in raw_results
        if row["strategy"] == "no_intervention"
    ]

    baseline_average = mean(baseline_reaches)

    summary = {}

    for strategy in strategies_to_run:

        reaches = [
            row["final_reach"]
            for row in raw_results
            if row["strategy"] == strategy
        ]

        average_reach = mean(reaches)

        if baseline_average > 0:
            reduction_percent = (
                (baseline_average - average_reach)
                / baseline_average
            ) * 100
        else:
            reduction_percent = 0.0

        summary[strategy] = {
            "average_reach": average_reach,
            "std_reach": pstdev(reaches),
            "min_reach": min(reaches),
            "max_reach": max(reaches),
            "reduction_percent": reduction_percent,
        }

    # ---------------------------------------------------------
    # 5. Return all evaluation results
    # ---------------------------------------------------------
    return {
        "summary": summary,
        "raw_results": raw_results,
        "selected_users": selected_users,
        "settings": {
            "total_users": graph.number_of_nodes(),
            "source": source,
            "intervention_budget": k,
            "n_runs": n_runs,
            "transmission_prob": transmission_prob,
            "max_rounds": max_rounds,
            "seed": seed,
        },
    }


def print_evaluation_report(results):
    """Print a readable comparison of all strategies."""

    summary = results["summary"]

    print("\n" + "=" * 80)
    print("OUTBREAK OF LIES - EVALUATION REPORT")
    print("=" * 80)

    print(f"Network users: {results['settings']['total_users']}")
    print(f"Intervention budget: {results['settings']['intervention_budget']}")
    print(f"Simulation runs: {results['settings']['n_runs']}")

    print("\nStrategy comparison")
    print("-" * 80)

    print(
        f"{'Strategy':<22}"
        f"{'Avg Reach':>12}"
        f"{'Std Dev':>12}"
        f"{'Min':>8}"
        f"{'Max':>8}"
        f"{'Reduction %':>15}"
    )

    print("-" * 80)

    for strategy, metrics in summary.items():
        print(
            f"{strategy:<22}"
            f"{metrics['average_reach']:>12.2f}"
            f"{metrics['std_reach']:>12.2f}"
            f"{metrics['min_reach']:>8}"
            f"{metrics['max_reach']:>8}"
            f"{metrics['reduction_percent']:>14.2f}%"
        )

    intervention_strategies = [
        strategy
        for strategy in summary
        if strategy != "no_intervention"
    ]

    if intervention_strategies:
        best_strategy = min(
            intervention_strategies,
            key=lambda strategy: summary[strategy]["average_reach"],
        )

        print("-" * 80)
        print(f"Best observed strategy: {best_strategy}")
        print(
            "Average users reached: "
            f"{summary[best_strategy]['average_reach']:.2f}"
        )
        print(
            "Reduction versus baseline: "
            f"{summary[best_strategy]['reduction_percent']:.2f}%"
        )

    print("=" * 80)
