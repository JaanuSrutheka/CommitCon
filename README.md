# Outbreak of Lies

**Misinformation Containment and Intervention Optimization**

## Overview

Outbreak of Lies is a simulation-based platform that models how misinformation spreads through a social network and identifies effective intervention targets when resources are limited.

## Objectives

- Generate or load a social network.
- Simulate stochastic rumour propagation.
- Select intervention targets using different strategies.
- Compare random, degree-based, betweenness-based and greedy selection.
- Evaluate effectiveness through repeated simulations.
- Visualize spread reduction and intervention performance.

## Tech Stack

- Python
- NetworkX
- NumPy
- Pandas
- Streamlit
- Matplotlib and Plotly
- Pytest

## Setup

```bash
git clone YOUR_REPOSITORY_URL
cd outbreak-of-lies
python -m venv .venv
```

Activate the virtual environment and install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the application after implementation:

```bash
streamlit run app.py
```

## Project Structure

- `network_generator.py` — Network creation
- `rumor_simulator.py` — Rumour propagation
- `intervention.py` — Intervention selection algorithms
- `evaluation.py` — Repeated experiments and metrics
- `app.py` — Interactive dashboard
- `tests/` — Automated tests

## Team Workflow

Each member works on a dedicated feature branch. Changes are submitted through pull requests and reviewed before being merged into `main`.
