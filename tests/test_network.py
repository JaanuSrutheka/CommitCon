
import sys
from pathlib import Path

# Allow Python to find network_generator.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from network_generator import generate_network


def test_generate_network():
    graph = generate_network(
        n=100,
        model="erdos_renyi",
        seed=42
    )

    assert graph.number_of_nodes() == 100
    assert graph.number_of_edges() >= 0

    print("Network generation successful!")


if __name__ == "__main__":
    test_generate_network()

    graph = generate_network(
        n=100,
        model="erdos_renyi",
        seed=42
    )

    print("Number of users:", graph.number_of_nodes())
    print("Number of connections:", graph.number_of_edges())
