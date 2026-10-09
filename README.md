# CommitCon — Outbreak of Lies

## Team Details

**Team Name:** CommitCon

**Team Members:**

1. Naishitha
2. Harshini
3. Jaanu Srutheka
4. Raj.Harini
5. Dhivyadharshini

## Selected Problem Statement

**Outbreak of Lies - Rumour Spread Simulation and Intervention**

The project models how rumours or misinformation spread through a social network and explores how targeted interventions can reduce their reach.

## Project Description

CommitCon simulates the spread of rumours across a synthetic social network. Users are represented as nodes, and connections between users are represented as edges.

The application generates networks using different graph models and simulates the spread of a rumour from a selected source. It then applies intervention strategies to identify users whose blocking may help reduce the spread.

The project compares intervention strategies using metrics such as final reach, number of affected users, and spread progression. An interactive Streamlit dashboard presents the network, simulation results, comparisons, and downloadable outputs.

### Key Features

- Synthetic social network generation.
- Rumour propagation simulation.
- Intervention strategies:
  - Random selection
  - Degree centrality
  - Betweenness centrality
  - Greedy selection
- Comparison of intervention effectiveness.
- Interactive network visualisation.
- Metrics and spread-history charts.
- Exportable results.

## Technologies and Tools Used

- **Python** — Core implementation
- **NetworkX** — Graph generation and network analysis
- **NumPy** — Numerical operations
- **Pandas** — Data handling and result tables
- **Plotly** — Interactive visualisations
- **Streamlit** — Interactive dashboard
- **Pytest** — Automated testing
- **Git and GitHub** — Version control and collaboration
- **Visual Studio Code** — Development environment

## Project Structure

```text
CommitCon/
├── app.py
├── network_generator.py
├── rumor_simulator.py
├── intervention.py
├── evaluation.py
├── requirements.txt
├── README.md
└── tests/
```

## Installation and Execution

### Prerequisites

- Python 3.10 or a compatible Python version supported by the dependencies.
- Git (if cloning the repository).
- A terminal or Visual Studio Code.

### 1. Clone the repository

```bash
git clone https://github.com/JaanuSrutheka/CommitCon.git
cd CommitCon
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Run the tests

```bash
python -m pytest -q
```

### 5. Launch the dashboard

```bash
python -m streamlit run app.py
```

Open the local URL displayed in the terminal, usually `http://localhost:8501`.

### Demonstration Workflow

1. Select a network-generation model and configure the number of users.
2. Set the rumour transmission probability and simulation parameters.
3. Choose an intervention strategy and intervention budget.
4. Run the experiment.
5. Inspect the network visualisation and rumour-spread metrics.
6. Compare the intervention strategies and review the charts.
7. Export the available results.

## Evaluation Metrics

The application can compare strategies using metrics such as:

- Final rumour reach.
- Number of users affected.
- Spread progression across simulation rounds.
- Differences in reach between intervention strategies.

A lower final reach generally indicates a more effective intervention, provided the experiments use comparable network and simulation settings.

## Significant External Resources Used

- NetworkX documentation: https://networkx.org/documentation/stable/
- Streamlit documentation: https://docs.streamlit.io/
- Plotly Python documentation: https://plotly.com/python/
- Pytest documentation: https://docs.pytest.org/

These resources are listed as technical references. Add any datasets, tutorials, research papers, or other resources that the team actually used.

## Use of AI Tools

AI tools, including ChatGPT, were used for assistance with [describe the actual uses, such as understanding concepts, debugging, documentation, or test development].

The project code, experimental results, and final submission should be reviewed and validated by the team. This disclosure should be adjusted to accurately reflect the team's actual use of AI tools and the hackathon's rules.

## Limitations

- The networks are synthetic and may not represent every real-world social network.
- Rumour transmission probabilities are model assumptions.
- Simulation results can vary with network structure, random seeds, and intervention settings.
- Results from the simulator should not be interpreted as guaranteed predictions of real-world misinformation spread.

## Future Enhancements

- Support real-world or anonymised social-network datasets.
- Add more intervention strategies.
- Evaluate results over repeated simulation runs.
- Improve the modelling of user behaviour and rumour transmission.
- Add downloadable experiment reports.
