
import networkx as nx
import pytest

from evaluation import evaluate_strategies


def test_evaluation_includes_all_strategies():
    graph = nx.path_graph(6)

    results = evaluate_strategies(
        graph=graph,
        source=0,
        k=1,
        strategies=["random", "degree", "betweenness"],
        n_runs=3,
        transmission_prob=0.5,
        max_rounds=10,
        seed=42,
    )

    summary = results["summary"]

    assert "no_intervention" in summary
    assert "random" in summary
    assert "degree" in summary
    assert "betweenness" in summary


def test_evaluation_returns_valid_metrics():
    graph = nx.path_graph(6)

    results = evaluate_strategies(
        graph=graph,
        source=0,
        k=1,
        strategies=["random"],
        n_runs=3,
        seed=42,
    )

    metrics = results["summary"]["random"]

    assert 0 <= metrics["average_reach"] <= 6
    assert metrics["std_reach"] >= 0
    assert 0 <= metrics["min_reach"] <= 6
    assert 0 <= metrics["max_reach"] <= 6
    assert "reduction_percent" in metrics


def test_evaluation_rejects_invalid_run_count():
    graph = nx.path_graph(6)

    with pytest.raises(ValueError):
        evaluate_strategies(
            graph=graph,
            source=0,
            n_runs=0,
        )
