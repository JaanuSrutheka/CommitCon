
"""
Outbreak of Lies - Intervention Selection Module

Strategies:
1. random       - Randomly select users.
2. degree       - Select users with the most connections.
3. betweenness  - Select users that bridge different parts of the network.
4. greedy       - Repeatedly select the user that minimizes estimated
                  rumour reach when added to the selected set.

This module selects intervention targets. The actual rumour propagation
is handled by rumor_simulator.py.
"""

import random
from numbers import Integral, Real

import networkx as nx

from rumor_simulator import simulate_spread


VALID_STRATEGIES = {
    "random",
    "degree",
    "betweenness",
    "greedy",
}


def select_interventions(
    graph,
    k,
    strategy,
    simulator_config=None,
):
    """
    Select users for intervention.

    Parameters
    ----------
    graph : networkx.Graph
        The social network.

    k : int
        Number of users to select.

    strategy : str
        "random", "degree", "betweenness", or "greedy".

    simulator_config : dict, optional
        Configuration for the rumour simulator.

        Supported keys:
            source: Starting user ID (required for greedy).
            transmission_prob: Probability of transmission (default 0.3).
            max_rounds: Maximum simulation rounds (default 50).
            seed: Random seed (default 42).
            n_runs: Repetitions per greedy candidate (default 30).
            blocked_nodes: Users already blocked (default None).

    Returns
    -------
    list
        Selected user IDs.
    """

    # ---------------------------------------------------------
    # 1. Validate inputs
    # ---------------------------------------------------------
    if not isinstance(graph, nx.Graph):
        raise TypeError("graph must be a NetworkX graph.")

    if graph.number_of_nodes() == 0:
        raise ValueError("graph must contain at least one user.")

    if (
        isinstance(k, bool)
        or not isinstance(k, Integral)
        or k < 0
    ):
        raise ValueError("k must be a non-negative integer.")

    if not isinstance(strategy, str):
        raise TypeError("strategy must be a string.")

    strategy = strategy.lower().strip()

    if strategy not in VALID_STRATEGIES:
        raise ValueError(
            f"Unknown strategy {strategy!r}. "
            f"Choose from {sorted(VALID_STRATEGIES)}."
        )

    config = dict(simulator_config or {})

    source = config.get("source")
    seed = config.get("seed", 42)

    if seed is not None and (
        isinstance(seed, bool)
        or not isinstance(seed, Integral)
    ):
        raise ValueError("seed must be an integer or None.")

    # ---------------------------------------------------------
    # 2. Validate existing blocked users
    # ---------------------------------------------------------
    try:
        already_blocked = set(config.get("blocked_nodes") or [])
    except TypeError as exc:
        raise TypeError(
            "blocked_nodes must be an iterable of user IDs."
        ) from exc

    unknown_blocked = already_blocked - set(graph.nodes)

    if unknown_blocked:
        raise ValueError(
            f"Unknown blocked users: {unknown_blocked!r}"
        )

    # ---------------------------------------------------------
    # 3. Prepare eligible candidates
    # ---------------------------------------------------------
    # The source is excluded so greedy selection cannot achieve
    # a trivial zero-spread result simply by blocking the source.
    # This assumes the source is not an available intervention target.
    candidates = sorted(
        (
            node
            for node in graph.nodes
            if node not in already_blocked and node != source
        ),
        key=str,
    )

    if k > len(candidates):
        raise ValueError(
            f"Cannot select {k} users. "
            f"Only {len(candidates)} eligible users are available."
        )

    if k == 0:
        return []

    # ---------------------------------------------------------
    # 4. Random selection
    # ---------------------------------------------------------
    if strategy == "random":
        rng = random.Random(seed)
        return rng.sample(candidates, k)

    # ---------------------------------------------------------
    # 5. Degree centrality strategy
    # ---------------------------------------------------------
    if strategy == "degree":
        degree_scores = dict(graph.degree())

        candidates.sort(
            key=lambda node: (
                -degree_scores[node],
                str(node),
            )
        )

        return candidates[:k]

    # ---------------------------------------------------------
    # 6. Betweenness centrality strategy
    # ---------------------------------------------------------
    if strategy == "betweenness":
        scores = nx.betweenness_centrality(graph)

        candidates.sort(
            key=lambda node: (
                -scores[node],
                str(node),
            )
        )

        return candidates[:k]

    # ---------------------------------------------------------
    # 7. Greedy influence minimization
    # ---------------------------------------------------------
    if source is None:
        raise ValueError(
            "simulator_config must include 'source' for greedy."
        )

    if source not in graph:
        raise ValueError("source must exist in the graph.")

    if source in already_blocked:
        raise ValueError(
            "The source is already blocked. "
            "Choose an unblocked source for this experiment."
        )

    transmission_prob = config.get("transmission_prob", 0.3)
    max_rounds = config.get("max_rounds", 50)
    n_runs = config.get("n_runs", 30)

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

    if (
        isinstance(n_runs, bool)
        or not isinstance(n_runs, Integral)
        or n_runs < 1
    ):
        raise ValueError("n_runs must be a positive integer.")

    # Use common random seeds to make candidate comparisons
    # less sensitive to random variation.
    rng = random.Random(seed)

    if seed is None:
        run_seeds = [rng.randrange(0, 2**32) for _ in range(n_runs)]
    else:
        run_seeds = [
            int(seed) + i for i in range(n_runs)
        ]

    selected = []

    for _ in range(k):
        best_node = None
        best_average_reach = float("inf")

        for candidate in candidates:
            if candidate in selected:
                continue

            proposed_blocked = (
                already_blocked
                | set(selected)
                | {candidate}
            )

            total_reach = 0

            for run_seed in run_seeds:
                result = simulate_spread(
                    graph=graph,
                    source=source,
                    transmission_prob=transmission_prob,
                    blocked_nodes=proposed_blocked,
                    max_rounds=max_rounds,
                    seed=run_seed,
                )

                total_reach += result["final_reach"]

            average_reach = total_reach / n_runs

            # Candidates are sorted, so ties are resolved
            # consistently by choosing the first candidate.
            if average_reach < best_average_reach:
                best_average_reach = average_reach
                best_node = candidate

        if best_node is None:
            break

        selected.append(best_node)

    return selected
