
"""
Tests for the Outbreak of Lies intervention module.
"""

import networkx as nx
import pytest

from intervention import select_interventions


# ---------------------------------------------------------
# 1. Random selection
# ---------------------------------------------------------

def test_random_selects_requested_number():
    graph = nx.path_graph(6)

    selected = select_interventions(
        graph,
        k=2,
        strategy="random",
        simulator_config={"source": 0, "seed": 42},
    )

    assert len(selected) == 2
    assert len(set(selected)) == 2
    assert all(node in graph for node in selected)
    assert 0 not in selected


def test_random_selection_is_reproducible():
    graph = nx.path_graph(10)
    config = {"source": 0, "seed": 42}

    first = select_interventions(
        graph, 3, "random", config
    )
    second = select_interventions(
        graph, 3, "random", config
    )

    assert first == second


# ---------------------------------------------------------
# 2. Degree centrality
# ---------------------------------------------------------

def test_degree_selects_most_connected_user():
    graph = nx.Graph()
    graph.add_edges_from([
        (0, 1),
        (1, 2),
        (1, 3),
        (3, 4),
        (3, 5),
        (3, 6),
    ])

    selected = select_interventions(
        graph,
        k=1,
        strategy="degree",
        simulator_config={"source": 0},
    )

    assert selected == [3]


def test_degree_selects_multiple_users():
    graph = nx.star_graph(5)

    selected = select_interventions(
        graph,
        k=2,
        strategy="degree",
        simulator_config={"source": 5},
    )

    assert len(selected) == 2
    assert selected[0] == 0
    assert 5 not in selected


# ---------------------------------------------------------
# 3. Betweenness centrality
# ---------------------------------------------------------

def test_betweenness_returns_valid_users():
    graph = nx.path_graph(7)

    selected = select_interventions(
        graph,
        k=2,
        strategy="betweenness",
        simulator_config={"source": 0},
    )

    assert len(selected) == 2
    assert len(set(selected)) == 2
    assert 0 not in selected
    assert all(node in graph for node in selected)


def test_betweenness_selects_central_bridge():
    graph = nx.path_graph(5)

    selected = select_interventions(
        graph,
        k=1,
        strategy="betweenness",
        simulator_config={"source": 0},
    )

    assert selected == [2]


# ---------------------------------------------------------
# 4. Greedy influence minimization
# ---------------------------------------------------------

def test_greedy_selects_effective_bridge():
    graph = nx.path_graph(5)

    selected = select_interventions(
        graph,
        k=1,
        strategy="greedy",
        simulator_config={
            "source": 0,
            "transmission_prob": 1.0,
            "max_rounds": 10,
            "n_runs": 3,
            "seed": 42,
        },
    )

    # Blocking node 1 prevents the rumour from reaching
    # nodes 1, 2, 3 and 4 from source 0.
    assert selected == [1]


def test_greedy_selects_requested_number():
    graph = nx.path_graph(8)

    selected = select_interventions(
        graph,
        k=2,
        strategy="greedy",
        simulator_config={
            "source": 0,
            "transmission_prob": 0.5,
            "max_rounds": 10,
            "n_runs": 3,
            "seed": 42,
        },
    )

    assert len(selected) == 2
    assert len(set(selected)) == 2
    assert 0 not in selected


def test_greedy_requires_source():
    graph = nx.path_graph(5)

    with pytest.raises(ValueError, match="source"):
        select_interventions(
            graph,
            k=1,
            strategy="greedy",
            simulator_config={},
        )


# ---------------------------------------------------------
# 5. Input validation
# ---------------------------------------------------------

def test_empty_graph_raises_error():
    graph = nx.Graph()

    with pytest.raises(ValueError, match="at least one"):
        select_interventions(graph, 1, "random")


def test_invalid_strategy_raises_error():
    graph = nx.path_graph(5)

    with pytest.raises(ValueError, match="Unknown strategy"):
        select_interventions(graph, 1, "unknown")


def test_negative_budget_raises_error():
    graph = nx.path_graph(5)

    with pytest.raises(ValueError, match="non-negative"):
        select_interventions(graph, -1, "random")


def test_non_integer_budget_raises_error():
    graph = nx.path_graph(5)

    with pytest.raises(ValueError, match="non-negative"):
        select_interventions(graph, 1.5, "random")


def test_budget_too_large_raises_error():
    graph = nx.path_graph(4)

    with pytest.raises(ValueError, match="eligible users"):
        select_interventions(
            graph,
            k=4,
            strategy="random",
            simulator_config={"source": 0},
        )


def test_zero_budget_returns_empty_list():
    graph = nx.path_graph(5)

    selected = select_interventions(
        graph,
        k=0,
        strategy="random",
    )

    assert selected == []


def test_invalid_graph_type_raises_error():
    with pytest.raises(TypeError, match="NetworkX"):
        select_interventions([], 1, "random")


# ---------------------------------------------------------
# 6. Existing interventions
# ---------------------------------------------------------

def test_already_blocked_users_are_not_selected_again():
    graph = nx.path_graph(6)

    selected = select_interventions(
        graph,
        k=2,
        strategy="degree",
        simulator_config={
            "source": 0,
            "blocked_nodes": {1},
        },
    )

    assert len(selected) == 2
    assert 0 not in selected
    assert 1 not in selected


def test_unknown_blocked_user_raises_error():
    graph = nx.path_graph(5)

    with pytest.raises(ValueError, match="Unknown blocked users"):
        select_interventions(
            graph,
            k=1,
            strategy="random",
            simulator_config={"blocked_nodes": {100}},
        )


# ---------------------------------------------------------
# 7. Greedy parameter validation
# ---------------------------------------------------------

def test_greedy_rejects_zero_simulation_runs():
    graph = nx.path_graph(5)

    with pytest.raises(ValueError, match="n_runs"):
        select_interventions(
            graph,
            k=1,
            strategy="greedy",
            simulator_config={
                "source": 0,
                "n_runs": 0,
            },
        )


def test_greedy_rejects_invalid_transmission_probability():
    graph = nx.path_graph(5)

    with pytest.raises(ValueError, match="transmission_prob"):
        select_interventions(
            graph,
            k=1,
            strategy="greedy",
            simulator_config={
                "source": 0,
                "transmission_prob": 1.5,
            },
        )


def test_greedy_rejects_unknown_source():
    graph = nx.path_graph(5)

    with pytest.raises(ValueError, match="source"):
        select_interventions(
            graph,
            k=1,
            strategy="greedy",
            simulator_config={"source": 100},
        )
