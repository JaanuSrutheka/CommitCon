"""
Outbreak of Lies — Misinformation Spread & Containment Dashboard

Run from the project root:
    python -m pip install -r requirements.txt
    streamlit run app.py

This dashboard uses the repository's real NetworkX generator, rumour simulator,
intervention selector, and evaluation module. All results are synthetic.
"""

from __future__ import annotations

import math
import traceback

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from network_generator import generate_network, get_network_summary
from rumor_simulator import simulate_spread
from intervention import select_interventions
from evaluation import evaluate_strategies


# ---------------------------------------------------------------------------
# Page setup and styling
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Outbreak of Lies | Containment Lab",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
:root {
    --bg: #080D19;
    --panel: #111A2B;
    --panel2: #151F33;
    --line: #27364D;
    --cyan: #62E6FF;
    --red: #FF647C;
    --green: #55D6A2;
    --violet: #BCA5FF;
    --muted: #9AAAC2;
}
.stApp {
    background:
      radial-gradient(ellipse at 15% 0%, rgba(28, 72, 111, .22), transparent 38%),
      radial-gradient(ellipse at 95% 10%, rgba(91, 58, 132, .14), transparent 32%),
      var(--bg);
}
[data-testid="stHeader"] { background: rgba(8,13,25,.85); }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #10192A 0%, #0B1220 100%);
    border-right: 1px solid var(--line);
}
.block-container { padding-top: 1.4rem; padding-bottom: 2.5rem; max-width: 1600px; }
h1, h2, h3 { letter-spacing: -0.025em; }
h1 { color: #F2F6FF; font-weight: 800; }
p, label, [data-testid="stMarkdownContainer"] { color: #D5DFEF; }
.eyebrow {
    color: var(--cyan); font-size: .72rem; letter-spacing: .18em;
    font-weight: 800; text-transform: uppercase; margin-bottom: .35rem;
}
.hero-title { font-size: clamp(1.8rem, 3vw, 2.7rem); font-weight: 850;
    letter-spacing: -.045em; color: #F5F8FF; line-height: 1.05; }
.hero-subtitle { color: #AAB9D0; font-size: 1rem; margin-top: .55rem; }
.status-pill {
    display: inline-block; border: 1px solid rgba(98,230,255,.4);
    color: var(--cyan); background: rgba(98,230,255,.08);
    padding: .35rem .65rem; border-radius: 999px; font-size: .72rem;
    font-weight: 800; letter-spacing: .08em;
}
.metric-card {
    background: linear-gradient(145deg, rgba(21,31,51,.96), rgba(13,21,36,.96));
    border: 1px solid #283850; border-radius: 16px; padding: 17px 18px;
    min-height: 116px; box-shadow: 0 8px 26px rgba(0,0,0,.12);
}
.metric-label { color: #9AAAC2; font-size: .72rem; letter-spacing: .09em;
    text-transform: uppercase; font-weight: 750; }
.metric-value { color: #F3F7FF; font-size: 2rem; line-height: 1.25;
    font-weight: 850; margin-top: .35rem; }
.metric-foot { color: #93A6C2; font-size: .76rem; margin-top: .15rem; }
.section-card {
    background: rgba(17,26,43,.78); border: 1px solid #26364E;
    border-radius: 18px; padding: 16px 18px;
}
.small-muted { color: #93A6C2; font-size: .83rem; }
div[data-testid="stButton"] > button[kind="primaryFormSubmit"],
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(90deg, #27C8F5, #7B8CFF);
    color: #07101D; border: 0; font-weight: 850; min-height: 2.8rem;
    border-radius: 10px; box-shadow: 0 6px 20px rgba(39,200,245,.18);
}
div[data-testid="stDownloadButton"] > button {
    border: 1px solid #3B506D; border-radius: 9px; background: #141F32;
}
hr { border-color: #26364E; }
footer { visibility: hidden; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MODEL_LABELS = {
    "Erdős–Rényi": "erdos_renyi",
    "Small-world": "small_world",
    "Scale-free": "scale_free",
}
STRATEGY_LABELS = {
    "random": "Random selection",
    "degree": "Degree centrality",
    "betweenness": "Betweenness centrality",
    "greedy": "Greedy selection",
    "no_intervention": "No intervention",
}
NODE_COLORS = {
    "reached": "#FF647C",
    "unreached": "#62E6FF",
    "blocked": "#55D6A2",
    "source": "#FFB454",
}


def metric_card(label: str, value: str, foot: str, accent: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value" style="color:{accent}">{value}</div>
          <div class="metric-foot">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def make_network_figure(graph, infected, blocked, source, seed, layout_name):
    """Build a Plotly network figure from the real NetworkX graph."""
    if graph.number_of_nodes() == 0:
        return go.Figure()

    if layout_name == "Circular":
        pos = nx.circular_layout(graph)
    elif layout_name == "Kamada-Kawai":
        pos = nx.kamada_kawai_layout(graph)
    else:
        pos = nx.spring_layout(graph, seed=seed, iterations=60)

    edge_x, edge_y = [], []
    for u, v in graph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([float(x0), float(x1), None])
        edge_y.extend([float(y0), float(y1), None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=0.65, color="rgba(111,139,174,0.30)"),
        hoverinfo="skip", name="Connections",
    )

    groups = {"reached": [], "unreached": [], "blocked": [], "source": []}
    for node in graph.nodes():
        if node == source:
            groups["source"].append(node)
        elif node in blocked:
            groups["blocked"].append(node)
        elif node in infected:
            groups["reached"].append(node)
        else:
            groups["unreached"].append(node)

    traces = [edge_trace]
    group_names = {
        "source": "Rumour source",
        "reached": "Rumour reached",
        "unreached": "Not reached",
        "blocked": "Intervention targets",
    }
    for group, nodes in groups.items():
        if not nodes:
            continue
        xs, ys, hover = [], [], []
        for node in nodes:
            x, y = pos[node]
            xs.append(float(x))
            ys.append(float(y))
            hover.append(
                f"<b>User {node}</b><br>"
                f"State: {group_names[group]}<br>"
                f"Connections: {graph.degree[node]}"
            )
        color = NODE_COLORS[group]
        traces.append(go.Scatter(
            x=xs, y=ys, mode="markers", name=group_names[group],
            text=hover, hovertemplate="%{text}<extra></extra>",
            marker=dict(
                size=14 if group == "source" else 8,
                color=color,
                opacity=0.98,
                line=dict(width=1.4 if group == "source" else 0.6,
                          color="#F7FAFF" if group == "source" else color),
            ),
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=530,
        margin=dict(l=8, r=8, t=8, b=8),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01,
            xanchor="left", x=0, font=dict(size=10, color="#C7D4E7"),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(bgcolor="#101A2B", bordercolor="#62E6FF",
                        font=dict(color="#F3F7FF")),
        xaxis=dict(visible=False, fixedrange=False),
        yaxis=dict(visible=False, fixedrange=False, scaleanchor="x",
                   scaleratio=1),
        showlegend=True,
    )
    return fig


def make_history_figure(history):
    """Plot cumulative and newly reached users from the simulator history."""
    rounds = list(range(len(history)))
    newly = [history[0]] + [
        max(0, history[i] - history[i - 1]) for i in range(1, len(history))
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rounds, y=history, mode="lines+markers",
        name="Cumulative reach",
        line=dict(color="#62E6FF", width=3),
        marker=dict(size=6, color="#62E6FF"),
        fill="tozeroy", fillcolor="rgba(98,230,255,.09)",
    ))
    fig.add_trace(go.Bar(
        x=rounds, y=newly, name="Newly reached",
        marker_color="rgba(255,100,124,.65)", opacity=.75,
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=320,
        margin=dict(l=8, r=8, t=18, b=8),
        xaxis_title="Simulation round", yaxis_title="Users",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0),
        barmode="overlay",
    )
    return fig


def make_comparison_figure(summary, total_users):
    rows = []
    for strategy, metrics in summary.items():
        rows.append({
            "Strategy": STRATEGY_LABELS.get(strategy, strategy),
            "Average reach": metrics["average_reach"],
            "Reduction (%)": metrics["reduction_percent"],
            "Strategy key": strategy,
        })
    df = pd.DataFrame(rows).sort_values("Average reach", ascending=True)
    color_map = {
        "No intervention": "#FF647C",
        "Random selection": "#8EA0BA",
        "Degree centrality": "#BCA5FF",
        "Betweenness centrality": "#62E6FF",
        "Greedy selection": "#55D6A2",
    }
    fig = go.Figure(go.Bar(
        x=df["Average reach"],
        y=df["Strategy"],
        orientation="h",
        marker_color=[color_map.get(s, "#62E6FF") for s in df["Strategy"]],
        text=[f'{v:.1f} users' for v in df["Average reach"]],
        textposition="outside",
        cliponaxis=False,
        customdata=df[["Reduction (%)"]].to_numpy(),
        hovertemplate=(
            "%{y}<br>Average users reached: %{x:.2f}"
            "<br>Reduction vs baseline: %{customdata[0]:.1f}%<extra></extra>"
        ),
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=330,
        margin=dict(l=8, r=40, t=12, b=8),
        xaxis=dict(title="Average users reached", range=[0, max(total_users * 1.08, 1)]),
        yaxis=dict(title=None, autorange="reversed"),
        showlegend=False,
    )
    return fig, df


def history_average_by_round(raw_results, strategy):
    """Average cumulative spread history across the repeated evaluation runs."""
    histories = [
        row["spread_history"] for row in raw_results
        if row["strategy"] == strategy and row.get("spread_history")
    ]
    if not histories:
        return []
    max_len = max(len(h) for h in histories)
    padded = []
    for history in histories:
        # After a run ends, cumulative reach stays at its final value.
        padded.append(history + [history[-1]] * (max_len - len(history)))
    return [sum(values) / len(values) for values in zip(*padded)]


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown('<div class="eyebrow">MISINFORMATION CONTAINMENT INTELLIGENCE</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="hero-title">OUTBREAK <span style="color:#62E6FF">OF LIES</span></div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Model the spread. Test interventions. Measure containment.</div>',
        unsafe_allow_html=True,
    )
with header_right:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="status-pill">● SIMULATION MODE</div>',
                unsafe_allow_html=True)
st.markdown("---")


# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🛡️ Simulation lab")
    st.caption("Configure a synthetic social network and run an experiment.")

    with st.form("simulation_controls"):
        model_label = st.selectbox("Network model", list(MODEL_LABELS.keys()))
        n_users = st.slider("Number of users", min_value=20, max_value=500,
                            value=100, step=10)
        transmission_prob = st.slider(
            "Transmission probability", min_value=0.0, max_value=1.0,
            value=0.30, step=0.05, help="Chance of transmission across each eligible edge."
        )
        budget = st.slider("Intervention budget", min_value=0, max_value=30,
                           value=8, step=1,
                           help="Number of users selected by each intervention strategy.")
        max_rounds = st.slider("Maximum spread rounds", 1, 50, 15)
        n_runs = st.select_slider("Evaluation repetitions",
                                  options=[3, 5, 10, 20, 30],
                                  value=5,
                                  help="More repetitions improve stability but take longer.")
        seed = st.number_input("Random seed", min_value=0, max_value=999999,
                               value=42, step=1)
        selected_strategy_label = st.selectbox(
            "Strategy for network view",
            ["Degree centrality", "Betweenness centrality",
             "Random selection", "Greedy selection"],
            index=0,
        )
        layout_name = st.selectbox("Network layout",
                                   ["Spring", "Circular", "Kamada-Kawai"])
        run_clicked = st.form_submit_button("▶  RUN SIMULATION", use_container_width=True)

    st.markdown("---")
    st.markdown("#### What this models")
    st.caption(
        "A synthetic network and a simplified rumour-propagation process. "
        "Interventions affect this simulation only; no real accounts are monitored or blocked."
    )


# ---------------------------------------------------------------------------
# Execute simulation only when requested
# ---------------------------------------------------------------------------

if run_clicked:
    try:
        model = MODEL_LABELS[model_label]
        with st.spinner("Generating network and evaluating containment strategies…"):
            graph = generate_network(n=n_users, model=model, seed=int(seed))
            if graph.number_of_nodes() == 0:
                raise ValueError("The generated network is empty.")

            source = min(graph.nodes(), key=str)
            strategy_key = {
                "Degree centrality": "degree",
                "Betweenness centrality": "betweenness",
                "Random selection": "random",
                "Greedy selection": "greedy",
            }[selected_strategy_label]

            eligible_count = max(0, graph.number_of_nodes() - 1)
            actual_budget = min(int(budget), eligible_count)

            selected_targets = select_interventions(
                graph=graph,
                k=actual_budget,
                strategy=strategy_key,
                simulator_config={
                    "source": source,
                    "transmission_prob": float(transmission_prob),
                    "max_rounds": int(max_rounds),
                    "seed": int(seed),
                    "n_runs": 3,
                },
            )
            single_result = simulate_spread(
                graph=graph,
                source=source,
                transmission_prob=float(transmission_prob),
                blocked_nodes=selected_targets,
                max_rounds=int(max_rounds),
                seed=int(seed),
            )
            evaluation = evaluate_strategies(
                graph=graph,
                source=source,
                k=actual_budget,
                strategies=["random", "degree", "betweenness", "greedy"],
                n_runs=int(n_runs),
                transmission_prob=float(transmission_prob),
                max_rounds=int(max_rounds),
                seed=int(seed),
                greedy_runs=3,
            )

        st.session_state["outbreak_result"] = {
            "graph": graph,
            "source": source,
            "selected_targets": selected_targets,
            "single_result": single_result,
            "evaluation": evaluation,
            "model_label": model_label,
            "n_users": n_users,
            "transmission_prob": transmission_prob,
            "budget": actual_budget,
            "max_rounds": max_rounds,
            "n_runs": n_runs,
            "seed": int(seed),
            "strategy_key": strategy_key,
            "strategy_label": selected_strategy_label,
            "layout_name": layout_name,
        }
    except Exception as exc:
        st.error(f"Simulation could not complete: {exc}")
        with st.expander("Technical details"):
            st.code(traceback.format_exc())


# ---------------------------------------------------------------------------
# Dashboard results
# ---------------------------------------------------------------------------

if "outbreak_result" not in st.session_state:
    st.info("Configure the experiment in the sidebar, then select **RUN SIMULATION** to populate the dashboard.")
    intro_a, intro_b, intro_c = st.columns(3)
    with intro_a:
        st.markdown('<div class="section-card"><div class="eyebrow">01 / MODEL</div><h3>Generate a network</h3><p class="small-muted">Choose a network structure and model the connections between synthetic users.</p></div>', unsafe_allow_html=True)
    with intro_b:
        st.markdown('<div class="section-card"><div class="eyebrow">02 / SIMULATE</div><h3>Watch spread unfold</h3><p class="small-muted">Run the rumour propagation process and inspect which users are reached.</p></div>', unsafe_allow_html=True)
    with intro_c:
        st.markdown('<div class="section-card"><div class="eyebrow">03 / CONTAIN</div><h3>Compare strategies</h3><p class="small-muted">Measure average reach across intervention methods and repeated trials.</p></div>', unsafe_allow_html=True)
    st.stop()

data = st.session_state["outbreak_result"]
graph = data["graph"]
source = data["source"]
targets = set(data["selected_targets"])
single = data["single_result"]
evaluation = data["evaluation"]
summary = evaluation["summary"]
infected = set(single["infected_users"])
blocked = set(single["blocked_nodes"])
total_users = graph.number_of_nodes()
reach = single["final_reach"]
reach_pct = 100 * reach / total_users if total_users else 0
not_reached = max(0, total_users - reach - len(blocked))

# Top metrics
m1, m2, m3, m4 = st.columns(4, gap="medium")
with m1:
    metric_card("TOTAL USERS", f"{total_users:,}",
                f"{graph.number_of_edges():,} network connections", "#F3F7FF")
with m2:
    metric_card("RUMOUR REACH", f"{reach_pct:.1f}%",
                f"{reach:,} users reached in selected run", "#FF647C")
with m3:
    metric_card("USERS PROTECTED", f"{len(blocked):,}",
                f"{not_reached:,} additional users not reached", "#55D6A2")
with m4:
    metric_card("SPREAD ROUNDS", str(single["rounds"]),
                "Maximum reached" if single["stopped_reason"] == "max_rounds"
                else "Spread stopped naturally", "#BCA5FF")

st.markdown("<br>", unsafe_allow_html=True)

# Main visual and status panel
network_col, status_col = st.columns([2.25, 1], gap="large")
with network_col:
    st.markdown("### ◉ Live spread network")
    st.caption(
        f"{data['model_label']} · source user {source} · "
        f"view strategy: {data['strategy_label']}"
    )
    network_fig = make_network_figure(
        graph, infected, blocked, source, data["seed"], data["layout_name"]
    )
    st.plotly_chart(network_fig, use_container_width=True,
                    config={"displaylogo": False, "scrollZoom": True})
with status_col:
    st.markdown("### Outbreak status")
    if reach_pct >= 70:
        status_text, status_color = "HIGH SPREAD", "#FF647C"
        status_note = "A large share of this synthetic network was reached."
    elif reach_pct >= 35:
        status_text, status_color = "MODERATE SPREAD", "#FFB454"
        status_note = "Spread reached a meaningful portion of the network."
    else:
        status_text, status_color = "LIMITED SPREAD", "#55D6A2"
        status_note = "Spread remained comparatively contained in this run."

    st.markdown(
        f'<div class="section-card"><div class="status-pill" style="color:{status_color};border-color:{status_color}">{status_text}</div>'
        f'<h2 style="margin-top:1rem;color:{status_color}">{reach_pct:.1f}%</h2>'
        f'<p class="small-muted">{status_note}</p><hr>'
        f'<p><b>Source user</b><br/>User {source}</p>'
        f'<p><b>Intervention targets</b><br/>{len(blocked)} users</p>'
        f'<p><b>Transmission probability</b><br/>{data["transmission_prob"]:.2f}</p>'
        f'<p><b>Termination</b><br/>{single["stopped_reason"].replace("_", " ").title()}</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    net_stats = get_network_summary(graph)
    s1, s2 = st.columns(2)
    with s1:
        st.metric("Avg. connections", f'{net_stats["average_degree"]:.2f}')
    with s2:
        st.metric("Network density", f'{net_stats["density"]:.3f}')
    st.caption(f'{net_stats["connected_components"]} connected component(s)')

st.markdown("---")

# Intervention comparison
st.markdown("### Intervention impact")
st.caption(
    f"Average rumour reach across {data['n_runs']} repeated runs. "
    "Lower reach indicates better containment in this experiment."
)
chart_col, insight_col = st.columns([1.7, 1], gap="large")
with chart_col:
    comparison_fig, comparison_df = make_comparison_figure(summary, total_users)
    st.plotly_chart(comparison_fig, use_container_width=True,
                    config={"displaylogo": False})
with insight_col:
    intervention_keys = [key for key in summary if key != "no_intervention"]
    best_key = min(intervention_keys, key=lambda key: summary[key]["average_reach"])
    baseline = summary["no_intervention"]["average_reach"]
    best_avg = summary[best_key]["average_reach"]
    best_reduction = summary[best_key]["reduction_percent"]
    st.markdown(
        f'<div class="section-card"><div class="eyebrow">KEY INSIGHT</div>'
        f'<h3 style="color:#55D6A2">{STRATEGY_LABELS[best_key]}</h3>'
        f'<p class="small-muted">Lowest average rumour reach in this evaluation.</p>'
        f'<h2 style="color:#62E6FF">{best_avg:.1f} <span style="font-size:.9rem;color:#9AAAC2">users reached on average</span></h2>'
        f'<p>Baseline without intervention: <b>{baseline:.1f}</b> users.</p>'
        f'<p>Change versus baseline: <b style="color:{"#55D6A2" if best_reduction >= 0 else "#FF647C"}">{best_reduction:+.1f}% reduction</b></p>'
        f'<p class="small-muted">Observed result for this synthetic network, seed, and parameter set; not a real-world effectiveness claim.</p></div>',
        unsafe_allow_html=True,
    )

# Timeline
st.markdown("---")
st.markdown("### Spread over time")
st.caption("Round-by-round history for the selected intervention strategy in the displayed network.")
st.plotly_chart(make_history_figure(single["spread_history"]),
                use_container_width=True, config={"displaylogo": False})

# Results table and CSV
st.markdown("---")
st.markdown("### Evaluation report")
st.caption("Summary statistics across repeated runs; standard deviation describes variation between trials.")
table_rows = []
for key, metrics in summary.items():
    table_rows.append({
        "Strategy": STRATEGY_LABELS.get(key, key),
        "Average reach (users)": round(metrics["average_reach"], 2),
        "Std. deviation": round(metrics["std_reach"], 2),
        "Minimum reach": metrics["min_reach"],
        "Maximum reach": metrics["max_reach"],
        "Reduction vs baseline (%)": round(metrics["reduction_percent"], 2),
        "Intervention budget": 0 if key == "no_intervention" else data["budget"],
    })
report_df = pd.DataFrame(table_rows)
st.dataframe(report_df, use_container_width=True, hide_index=True)
st.download_button(
    "⬇ Download evaluation as CSV",
    data=report_df.to_csv(index=False).encode("utf-8"),
    file_name="outbreak_of_lies_evaluation.csv",
    mime="text/csv",
)

with st.expander("Experiment configuration and interpretation"):
    st.json({
        "network_model": data["model_label"],
        "total_users": total_users,
        "connections": graph.number_of_edges(),
        "source_user": source,
        "transmission_probability": data["transmission_prob"],
        "intervention_budget": data["budget"],
        "maximum_rounds": data["max_rounds"],
        "evaluation_runs": data["n_runs"],
        "random_seed": data["seed"],
        "selected_view_strategy": data["strategy_label"],
    })
    st.write(
        "This application is a synthetic susceptible-infected simulation. "
        "Blocked nodes cannot receive or transmit the rumour within the model. "
        "It does not detect misinformation in real posts, access social platforms, "
        "or block actual accounts."
    )
