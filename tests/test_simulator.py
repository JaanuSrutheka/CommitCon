
import networkx as nx
import pytest

from rumor_simulator import simulate_spread


def test_source_is_infected():
    graph = nx.path_graph(5)

    result = simulate_spread(
        graph,
        source=0,
        transmission_prob=1.0,
        seed=42,
    )

    assert result["infected_users"] == [0, 1, 2, 3, 4]
    assert result["final_reach"] == 5


def test_zero_transmission_probability():
    graph = nx.path_graph(5)

    result = simulate_spread(
        graph,
        source=0,
        transmission_prob=0.0,
        seed=42,
    )

    assert result["infected_users"] == [0]
    assert result["final_reach"] == 1


def test_blocked_users_do_not_get_infected():
    graph = nx.path_graph(5)

    result = simulate_spread(
        graph,
        source=0,
        transmission_prob=1.0,
        blocked_nodes=[1],
        seed=42,
    )

    assert result["infected_users"] == [0]
    assert 1 not in result["infected_users"]


def test_invalid_source_raises_error():
    graph = nx.path_graph(5)

    with pytest.raises(ValueError):
        simulate_spread(graph, source=10)


def test_invalid_probability_raises_error():
    graph = nx.path_graph(5)

    with pytest.raises(ValueError):
        simulate_spread(graph, source=0, transmission_prob=1.5)


def test_spread_history_is_cumulative():
    graph = nx.path_graph(5)

    result = simulate_spread(
        graph,
        source=0,
        transmission_prob=1.0,
        seed=42,
    )

    history = result["spread_history"]

    assert history[0] == 1
    assert all(
        history[i] <= history[i + 1]
        for i in range(len(history) - 1)
    )
