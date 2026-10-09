
import networkx as nx


def generate_network(n, model="erdos_renyi", seed=None):
    """
    Generate a social network for the Outbreak of Lies project.

    Parameters:
        n (int): Number of users in the network.
        model (str): Network model to use:
                     'erdos_renyi', 'small_world', or 'scale_free'.
        seed (int or None): Seed for reproducible network generation.

    Returns:
        networkx.Graph: A graph representing users and their connections.
    """

    # Validate the number of users.
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("n must be a positive integer.")

    if not isinstance(model, str):
        raise ValueError("model must be a string.")

    model = model.lower()

    # Generate the selected network model.
    if model == "erdos_renyi":
        graph = nx.erdos_renyi_graph(
            n=n,
            p=0.05,
            seed=seed
        )

    elif model == "small_world":
        if n < 3:
            raise ValueError(
                "The small_world model requires at least 3 users."
            )

        k = min(4, n - 1)

        # The Watts-Strogatz model requires an even k.
        if k % 2 != 0:
            k -= 1

        graph = nx.watts_strogatz_graph(
            n=n,
            k=k,
            p=0.1,
            seed=seed
        )

    elif model == "scale_free":
        if n < 2:
            raise ValueError(
                "The scale_free model requires at least 2 users."
            )

        graph = nx.barabasi_albert_graph(
            n=n,
            m=min(2, n - 1),
            seed=seed
        )

    else:
        raise ValueError(
            "Unknown model. Choose 'erdos_renyi', "
            "'small_world', or 'scale_free'."
        )

    # Add consistent attributes to every user.
    for user_id in graph.nodes():
        graph.nodes[user_id]["user_id"] = user_id
        graph.nodes[user_id]["state"] = "susceptible"

    # Store metadata about the generated network.
    graph.graph["model"] = model
    graph.graph["seed"] = seed

    return graph


def get_network_summary(graph):
    """
    Calculate basic statistics about the network.

    Returns:
        dict: Number of users, connections, average degree,
              density, and connected components.
    """

    n = graph.number_of_nodes()
    edges = graph.number_of_edges()

    if n == 0:
        return {
            "users": 0,
            "connections": 0,
            "average_degree": 0.0,
            "density": 0.0,
            "connected_components": 0
        }

    return {
        "users": n,
        "connections": edges,
        "average_degree": sum(
            degree for _, degree in graph.degree()
        ) / n,
        "density": nx.density(graph),
        "connected_components": nx.number_connected_components(graph)
    }
