"""
OUTBREAK OF LIES — Containment Intelligence Console
A polished, interactive Streamlit dashboard for the team's synthetic rumour simulator.

Run:
    python -m pip install -r requirements.txt
    streamlit run app.py
"""

from __future__ import annotations

import traceback

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from network_generator import generate_network, get_network_summary
from rumor_simulator import simulate_spread
from intervention import select_interventions
from evaluation import evaluate_strategies


# ─────────────────────────────────────────────────────────────────────────────
# Page and design system
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Outbreak of Lies | Containment Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {
 --bg:#070B14; --surface:#0D1422; --surface2:#111C2D; --stroke:#223149;
 --text:#F1F6FF; --muted:#91A2BB; --cyan:#66E5FF; --red:#FF5F78;
 --green:#4DE0AE; --violet:#B9A2FF; --amber:#FFCA7A;
}
html, body, [class*="css"] { font-family:'Manrope',sans-serif; }
.stApp {
 background:
  radial-gradient(ellipse at 18% -8%,rgba(32,105,151,.20),transparent 35%),
  radial-gradient(ellipse at 100% 8%,rgba(112,70,173,.12),transparent 28%),
  var(--bg);
 color:var(--text);
}
[data-testid="stHeader"] {background:rgba(7,11,20,.78);}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#0D1625,#080E18);border-right:1px solid var(--stroke);}
.block-container {max-width:1660px;padding-top:1.25rem;padding-bottom:2.5rem;}
h1,h2,h3,h4 {font-family:'Manrope',sans-serif!important;letter-spacing:-.035em!important;color:var(--text)!important;}
p,li,label,.stMarkdown {color:#D7E1F1;}
small,.muted {color:var(--muted)!important;}
hr {border-color:var(--stroke)!important;}
[data-testid="stMetric"] {
 background:linear-gradient(145deg,rgba(17,28,45,.98),rgba(10,17,29,.98));
 border:1px solid #263750;border-radius:15px;padding:16px 18px;
 box-shadow:0 8px 28px rgba(0,0,0,.14);
}
[data-testid="stMetricLabel"] {color:#98A9C1!important;font-size:.76rem!important;text-transform:uppercase;letter-spacing:.09em;}
[data-testid="stMetricValue"] {color:#F2F7FF!important;font-weight:800;}
[data-testid="stMetricDelta"] {font-size:.77rem;}
.stTabs [data-baseweb="tab-list"] {gap:8px;border-bottom:1px solid var(--stroke);}
.stTabs [data-baseweb="tab"] {height:46px;background:transparent;border-radius:9px 9px 0 0;color:#9BAEC8;font-weight:700;}
.stTabs [aria-selected="true"] {color:var(--cyan)!important;border-bottom:2px solid var(--cyan)!important;}
.stButton > button, .stDownloadButton > button {
 border-radius:10px;border:1px solid #30435F;background:#121E31;color:#EAF4FF;
 font-weight:750;transition:all .18s ease;
}
.stButton > button:hover,.stDownloadButton > button:hover {
 border-color:var(--cyan);color:var(--cyan);box-shadow:0 0 18px rgba(102,229,255,.10);
}
.stFormSubmitButton > button {
 background:linear-gradient(95deg,#66E5FF,#8CA8FF)!important;color:#07111E!important;
 border:0!important;font-weight:900!important;min-height:3rem;
}
div[data-testid="stExpander"] {border:1px solid var(--stroke);border-radius:12px;background:rgba(13,20,34,.5);}
div[data-testid="stDataFrame"] {border:1px solid var(--stroke);border-radius:12px;overflow:hidden;}
.hero {
 display:flex;justify-content:space-between;align-items:center;gap:20px;
 padding:23px 25px;margin-bottom:18px;border:1px solid #263750;border-radius:20px;
 background:linear-gradient(110deg,rgba(18,34,53,.96),rgba(12,19,33,.82));
 box-shadow:0 14px 44px rgba(0,0,0,.16);
}
.hero-kicker {font:500 .69rem 'DM Mono',monospace;letter-spacing:.18em;color:var(--cyan);text-transform:uppercase;margin-bottom:8px;}
.hero-title {font-size:clamp(1.8rem,3.5vw,3rem);font-weight:800;letter-spacing:-.06em;color:#F7FAFF;line-height:1;}
.hero-title span {color:var(--cyan);}
.hero-copy {color:#9FB1CA;margin-top:10px;font-size:.93rem;}
.live-pill {white-space:nowrap;border:1px solid rgba(77,224,174,.42);background:rgba(77,224,174,.08);color:var(--green);border-radius:999px;padding:8px 12px;font:500 .7rem 'DM Mono',monospace;letter-spacing:.06em;}
.panel {
 background:linear-gradient(145deg,rgba(15,24,40,.96),rgba(10,17,29,.96));
 border:1px solid #24344B;border-radius:16px;padding:17px 19px;
}
.panel-kicker {font:500 .66rem 'DM Mono',monospace;letter-spacing:.15em;color:var(--muted);text-transform:uppercase;}
.panel-title {font-size:1.05rem;font-weight:800;color:#F1F6FF;margin-top:4px;}
.big-number {font-size:2.15rem;line-height:1.15;font-weight:800;letter-spacing:-.05em;}
.insight {
 border:1px solid rgba(77,224,174,.26);border-radius:16px;padding:18px;
 background:linear-gradient(135deg,rgba(25,73,67,.22),rgba(13,20,34,.95));
}
.tag {display:inline-block;border-radius:6px;padding:4px 7px;background:#15263A;color:#B6C9E1;font:500 .66rem 'DM Mono',monospace;}
.footnote {font-size:.77rem;color:#8497B2;}
div[data-testid="stAlert"] {border-radius:12px;}
footer {visibility:hidden;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

CYAN, RED, GREEN, VIOLET, AMBER = "#66E5FF", "#FF5F78", "#4DE0AE", "#B9A2FF", "#FFCA7A"
PALETTE = {
    "source": AMBER,
    "reached": RED,
    "unreached": CYAN,
    "blocked": GREEN,
}
STRATEGY_NAMES = {
    "no_intervention": "No intervention",
    "random": "Random selection",
    "degree": "Degree centrality",
    "betweenness": "Betweenness centrality",
    "greedy": "Greedy selection",
}
MODELS = {
    "Scale-free network": "scale_free",
    "Small-world network": "small_world",
    "Random network": "erdos_renyi",
}


# ─────────────────────────────────────────────────────────────────────────────
# Visual components and charts
# ─────────────────────────────────────────────────────────────────────────────
def section_heading(kicker: str, title: str, description: str | None = None):
    st.markdown(
        f'<div class="panel-kicker">{kicker}</div><div class="panel-title">{title}</div>',
        unsafe_allow_html=True,
    )
    if description:
        st.caption(description)


def make_network_figure(graph, infected, blocked, source, seed, layout_name, selected_targets=None):
    """Plot actual graph nodes and edges; colors reflect simulator outputs."""
    if graph.number_of_nodes() == 0:
        return go.Figure()

    if layout_name == "Circular":
        pos = nx.circular_layout(graph)
    elif layout_name == "Kamada–Kawai":
        pos = nx.kamada_kawai_layout(graph)
    else:
        pos = nx.spring_layout(graph, seed=seed, iterations=75)

    edge_x, edge_y = [], []
    for u, v in graph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [float(x0), float(x1), None]
        edge_y += [float(y0), float(y1), None]

    traces = [go.Scatter(
        x=edge_x, y=edge_y, mode="lines", hoverinfo="skip", name="Connections",
        line=dict(width=.65, color="rgba(108,137,174,.26)"),
    )]

    buckets = {"source": [], "reached": [], "blocked": [], "unreached": []}
    for node in graph.nodes():
        if node == source:
            buckets["source"].append(node)
        elif node in blocked:
            buckets["blocked"].append(node)
        elif node in infected:
            buckets["reached"].append(node)
        else:
            buckets["unreached"].append(node)

    labels = {
        "source": "Rumour source",
        "reached": "Rumour reached",
        "unreached": "Not reached",
        "blocked": "Intervention targets",
    }
    selected_targets = set(selected_targets or [])
    for state, nodes in buckets.items():
        if not nodes:
            continue
        xs, ys, hover, sizes, outlines = [], [], [], [], []
        for node in nodes:
            x, y = pos[node]
            xs.append(float(x))
            ys.append(float(y))
            degree = graph.degree[node]
            extras = "<br><b>Selected target:</b> Yes" if node in selected_targets else ""
            hover.append(
                f"<b>User {node}</b><br>State: {labels[state]}"
                f"<br>Connections: {degree}{extras}"
            )
            sizes.append(17 if state == "source" else (11 if node in selected_targets else 8))
            outlines.append("#FFFFFF" if state == "source" or node in selected_targets else PALETTE[state])
        traces.append(go.Scatter(
            x=xs, y=ys, mode="markers", name=labels[state],
            text=hover, hovertemplate="%{text}<extra></extra>",
            marker=dict(
                size=sizes, color=PALETTE[state], opacity=.97,
                line=dict(width=1.25, color=outlines),
            ),
        ))

    fig = go.Figure(traces)
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=560,
        margin=dict(l=3, r=3, t=28, b=3),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=10, color="#C6D5E9"), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#101A2B", bordercolor=CYAN,
                        font=dict(color="#F4F8FF")),
        xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
    )
    return fig


def make_comparison_chart(summary, total_users):
    rows = []
    for key, metrics in summary.items():
        rows.append({
            "key": key,
            "Strategy": STRATEGY_NAMES.get(key, key),
            "Average reach": metrics["average_reach"],
            "Reduction": metrics["reduction_percent"],
            "Std dev": metrics["std_reach"],
        })
    df = pd.DataFrame(rows).sort_values("Average reach", ascending=True)
    colors = {
        "No intervention": RED,
        "Random selection": "#8292AC",
        "Degree centrality": VIOLET,
        "Betweenness centrality": CYAN,
        "Greedy selection": GREEN,
    }
    fig = go.Figure(go.Bar(
        x=df["Average reach"], y=df["Strategy"], orientation="h",
        marker=dict(color=[colors.get(name, CYAN) for name in df["Strategy"]]),
        text=[f"{value:.1f}" for value in df["Average reach"]],
        textposition="outside", cliponaxis=False,
        customdata=df[["Reduction", "Std dev"]].to_numpy(),
        hovertemplate=(
            "<b>%{y}</b><br>Mean users reached: %{x:.2f}"
            "<br>Reduction vs baseline: %{customdata[0]:.1f}%"
            "<br>Standard deviation: %{customdata[1]:.2f}<extra></extra>"
        ),
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=350,
        margin=dict(l=4, r=40, t=10, b=8),
        xaxis=dict(title="Average users reached", range=[0, max(1, total_users * 1.10)], gridcolor="#26364C"),
        yaxis=dict(title=None, autorange="reversed"),
        showlegend=False,
    )
    return fig, df


def make_timeline(raw_results, strategies):
    """Average round-by-round cumulative reach from actual evaluation records."""
    fig = go.Figure()
    colors = {
        "no_intervention": RED, "random": "#8292AC",
        "degree": VIOLET, "betweenness": CYAN, "greedy": GREEN,
    }
    for strategy in strategies:
        histories = [
            row.get("spread_history", [])
            for row in raw_results
            if row.get("strategy") == strategy and row.get("spread_history")
        ]
        if not histories:
            continue
        max_len = max(map(len, histories))
        aligned = [h + [h[-1]] * (max_len - len(h)) for h in histories]
        mean_history = [sum(values) / len(values) for values in zip(*aligned)]
        fig.add_trace(go.Scatter(
            x=list(range(len(mean_history))), y=mean_history,
            mode="lines+markers", name=STRATEGY_NAMES.get(strategy, strategy),
            line=dict(color=colors.get(strategy, CYAN), width=2.7),
            marker=dict(size=5), hovertemplate="Round %{x}<br>Average reach: %{y:.1f}<extra>%{fullData.name}</extra>",
        ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=360,
        margin=dict(l=8, r=10, t=12, b=8),
        xaxis=dict(title="Simulation round", gridcolor="#26364C"),
        yaxis=dict(title="Average users reached", gridcolor="#26364C"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified",
    )
    return fig


def average_for_strategy(summary, key):
    return summary.get(key, {}).get("average_reach", 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# Hero
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
      <div>
        <div class="hero-kicker">Network risk modelling / containment analytics</div>
        <div class="hero-title">OUTBREAK <span>OF LIES</span></div>
        <div class="hero-copy">See how a rumour propagates. Find the intervention that slows it down.</div>
      </div>
      <div class="live-pill">● SYNTHETIC SIMULATION</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Controls
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ Experiment setup")
    st.caption("Configure the network, run the model, then explore the results.")
    with st.form("experiment_form", border=False):
        model_label = st.selectbox("Network topology", list(MODELS.keys()), index=0)
        n_users = st.slider("Network size", 30, 500, 100, 10)
        transmission_prob = st.slider("Transmission probability", 0.0, 1.0, 0.30, 0.05)
        budget = st.slider("Intervention budget", 0, 30, 8, 1)
        max_rounds = st.slider("Maximum rounds", 1, 50, 15, 1)
        n_runs = st.select_slider("Evaluation runs per strategy", options=[3, 5, 10, 15, 20], value=5)
        seed = st.number_input("Reproducibility seed", min_value=0, max_value=999999, value=42, step=1)
        selected_strategy_label = st.selectbox(
            "Network view intervention",
            ["Degree centrality", "Betweenness centrality", "Random selection", "Greedy selection"],
        )
        layout_name = st.selectbox("Graph layout", ["Spring", "Circular", "Kamada–Kawai"])
        run_clicked = st.form_submit_button("▶  RUN EXPERIMENT", use_container_width=True)

    st.markdown("---")
    st.markdown("### Model notes")
    st.markdown(
        '<div class="footnote">Synthetic users and connections only. Intervention targets are blocked inside the model, not on real platforms.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Tip: use 100 users and 3–5 runs for a quick live demo.")


# ─────────────────────────────────────────────────────────────────────────────
# Run real model
# ─────────────────────────────────────────────────────────────────────────────
if run_clicked:
    try:
        with st.spinner("Building the network and running intervention experiments…"):
            model = MODELS[model_label]
            graph = generate_network(n=int(n_users), model=model, seed=int(seed))
            if graph.number_of_nodes() < 1:
                raise ValueError("The network generator returned an empty graph.")

            source = min(graph.nodes(), key=str)
            strategy_key = {
                "Degree centrality": "degree",
                "Betweenness centrality": "betweenness",
                "Random selection": "random",
                "Greedy selection": "greedy",
            }[selected_strategy_label]
            actual_budget = min(int(budget), max(0, graph.number_of_nodes() - 1))

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
            "graph": graph, "source": source, "selected_targets": selected_targets,
            "single_result": single_result, "evaluation": evaluation,
            "model_label": model_label, "n_users": int(n_users),
            "transmission_prob": float(transmission_prob), "budget": actual_budget,
            "max_rounds": int(max_rounds), "n_runs": int(n_runs), "seed": int(seed),
            "strategy_key": strategy_key, "strategy_label": selected_strategy_label,
            "layout_name": layout_name,
        }
        st.toast("Experiment complete", icon="✅")
    except Exception as exc:
        st.error(f"Experiment failed: {exc}")
        with st.expander("Technical details"):
            st.code(traceback.format_exc())

if "outbreak_result" not in st.session_state:
    st.markdown(
        """
        <div class="panel">
          <div class="panel-kicker">Welcome to the containment lab</div>
          <div class="panel-title" style="font-size:1.35rem;margin-top:8px">Run your first outbreak experiment</div>
          <p style="color:#9FB1CA;margin-top:8px">Choose a network topology and transmission probability in the sidebar, then run the experiment to populate the live network, intervention benchmarks, and evidence-based insights.</p>
          <span class="tag">NETWORK SCIENCE</span> &nbsp; <span class="tag">STOCHASTIC SPREAD</span> &nbsp; <span class="tag">INTERVENTION ANALYSIS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    intro = st.columns(3, gap="medium")
    for col, num, title, copy in zip(
        intro,
        ["01", "02", "03"],
        ["Model the network", "Trace propagation", "Compare containment"],
        [
            "Generate a synthetic network with different connection patterns.",
            "Explore which users are reached during the simulated outbreak.",
            "Compare targeting strategies using repeated runs and a shared baseline.",
        ],
    ):
        with col:
            st.markdown(
                f'<div class="panel" style="min-height:150px"><div class="panel-kicker">{num} / LAB STAGE</div><div class="panel-title">{title}</div><p class="footnote">{copy}</p></div>',
                unsafe_allow_html=True,
            )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Result model
# ─────────────────────────────────────────────────────────────────────────────
data = st.session_state["outbreak_result"]
graph = data["graph"]
source = data["source"]
single = data["single_result"]
evaluation = data["evaluation"]
summary = evaluation["summary"]
raw_results = evaluation["raw_results"]
infected = set(single["infected_users"])
blocked = set(single["blocked_nodes"])
total_users = graph.number_of_nodes()
reach = single["final_reach"]
reach_pct = 100 * reach / total_users if total_users else 0
stats = get_network_summary(graph)
baseline = average_for_strategy(summary, "no_intervention")
intervention_keys = [key for key in summary if key != "no_intervention"]
best_key = min(intervention_keys, key=lambda key: summary[key]["average_reach"])
best_avg = summary[best_key]["average_reach"]
best_reduction = summary[best_key]["reduction_percent"]
reach_delta = baseline - best_avg


# ─────────────────────────────────────────────────────────────────────────────
# KPI ribbon
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="panel-kicker">Executive snapshot / current experiment</div>', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4, gap="medium")
with k1:
    st.metric("Network population", f"{total_users:,}", f"{graph.number_of_edges():,} connections")
with k2:
    st.metric("Reach in selected run", f"{reach_pct:.1f}%", f"{reach:,} users reached")
with k3:
    st.metric("Intervention targets", f"{len(blocked):,}", f"{data['strategy_label']} strategy")
with k4:
    st.metric("Rounds simulated", str(single["rounds"]), "Reached stopping condition" if single["stopped_reason"] != "max_rounds" else "Maximum round limit")

st.markdown("<br>", unsafe_allow_html=True)

overview_tab, network_tab, strategy_tab, report_tab = st.tabs([
    "◈  Command overview", "◎  Network explorer", "↗  Strategy lab", "▤  Experiment report"
])

# ─────────────────────────────────────────────────────────────────────────────
# Command overview
# ─────────────────────────────────────────────────────────────────────────────
with overview_tab:
    left, right = st.columns([1.8, 1], gap="large")
    with left:
        section_heading("01 / PROPAGATION MAP", "The network at a glance",
                        f"{data['model_label']} · source user {source} · selected view: {data['strategy_label']}")
        st.plotly_chart(
            make_network_figure(
                graph, infected, blocked, source, data["seed"], data["layout_name"],
                selected_targets=data["selected_targets"],
            ),
            use_container_width=True,
            config={"displaylogo": False, "scrollZoom": True},
            key="overview_network",
        )
        st.markdown(
            '<div class="footnote">Amber = source · coral = reached · cyan = not reached · green = intervention target. Hover a node for details.</div>',
            unsafe_allow_html=True,
        )
    with right:
        section_heading("02 / OUTBREAK STATUS", "Containment telemetry",
                        "A summary of the selected single simulation.")
        if reach_pct >= 70:
            status, status_color, status_copy = "WIDE REACH", RED, "A large share of the network was reached in this run."
        elif reach_pct >= 35:
            status, status_color, status_copy = "MODERATE REACH", AMBER, "The rumour reached a substantial part of the network."
        else:
            status, status_color, status_copy = "LIMITED REACH", GREEN, "Spread remained comparatively limited in this run."
        st.markdown(
            f'<div class="panel"><span class="tag" style="color:{status_color};border:1px solid {status_color}">{status}</span>'
            f'<div class="big-number" style="color:{status_color};margin-top:12px">{reach_pct:.1f}%</div>'
            f'<p class="footnote">{status_copy}</p><hr>'
            f'<p><span class="footnote">ORIGIN NODE</span><br><b>User {source}</b></p>'
            f'<p><span class="footnote">TRANSMISSION PROBABILITY</span><br><b>{data["transmission_prob"]:.2f}</b></p>'
            f'<p><span class="footnote">TERMINATION REASON</span><br><b>{single["stopped_reason"].replace("_", " ").title()}</b></p>'
            f'<p><span class="footnote">NETWORK DENSITY</span><br><b>{stats["density"]:.4f}</b></p></div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        section_heading("03 / TOP FINDING", "Best observed strategy")
        st.markdown(
            f'<div class="insight"><div class="panel-kicker">LOWEST AVERAGE REACH</div>'
            f'<div class="panel-title" style="font-size:1.2rem;color:{GREEN}">{STRATEGY_NAMES[best_key]}</div>'
            f'<div class="big-number" style="color:{CYAN};margin-top:10px">{best_avg:.1f}<span style="font-size:.9rem;color:#91A2BB"> / {total_users} users</span></div>'
            f'<p class="footnote">Baseline: {baseline:.1f} users · {best_reduction:.1f}% reduction versus no intervention.</p>'
            f'<p class="footnote">Observed in this experiment only; not a guarantee of real-world effectiveness.</p></div>',
            unsafe_allow_html=True,
        )
    st.markdown("---")
    tl_col, network_stats_col = st.columns([1.6, 1], gap="large")
    with tl_col:
        section_heading("04 / SPREAD DYNAMICS", "How reach evolves",
                        "Mean cumulative reach across the evaluation runs, by strategy.")
        st.plotly_chart(
            make_timeline(raw_results, ["no_intervention", "degree", "betweenness", "random", "greedy"]),
            use_container_width=True, config={"displaylogo": False}, key="overview_timeline",
        )
    with network_stats_col:
        section_heading("05 / NETWORK PROFILE", "Topology diagnostics")
        c1, c2 = st.columns(2)
        c1.metric("Average degree", f'{stats["average_degree"]:.2f}')
        c2.metric("Network density", f'{stats["density"]:.3f}')
        c3, c4 = st.columns(2)
        c3.metric("Connected components", f'{stats["connected_components"]}')
        c4.metric("Connections", f'{stats["connections"]:,}')
        st.markdown(
            '<div class="footnote">Topology influences how quickly and widely simulated information can travel. Compare network models using the same seed and settings.</div>',
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Network explorer
# ─────────────────────────────────────────────────────────────────────────────
with network_tab:
    section_heading("INTERACTIVE GRAPH", "Explore users and connections",
                    "Zoom, pan, and hover over nodes. The layout is generated from the actual NetworkX graph.")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        view_state = st.selectbox("Emphasize node state", ["All states", "Rumour reached", "Not reached", "Intervention targets"], key="network_filter")
    with c2:
        show_edges = st.toggle("Show connections", value=True)
    with c3:
        st.caption(f"{total_users} nodes · {graph.number_of_edges()} edges · layout: {data['layout_name']}")
    fig = make_network_figure(
        graph, infected, blocked, source, data["seed"], data["layout_name"],
        selected_targets=data["selected_targets"],
    )
    if view_state != "All states":
        desired = {
            "Rumour reached": "Rumour reached",
            "Not reached": "Not reached",
            "Intervention targets": "Intervention targets",
        }[view_state]
        for trace in fig.data:
            if trace.name in {"Rumour source", "Rumour reached", "Not reached", "Intervention targets"}:
                trace.visible = (trace.name == desired or trace.name == "Rumour source")
    if not show_edges and fig.data:
        fig.data[0].visible = False
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "scrollZoom": True}, key="network_explorer_graph")
    target_rows = []
    for node in graph.nodes():
        state = "Rumour source" if node == source else (
            "Intervention target" if node in blocked else (
                "Rumour reached" if node in infected else "Not reached"
            )
        )
        target_rows.append({
            "User ID": node, "State in selected run": state,
            "Connections": graph.degree[node],
            "Selected by intervention": node in set(data["selected_targets"]),
        })
    node_df = pd.DataFrame(target_rows)
    st.markdown("#### User-level details")
    filter_text = st.text_input("Filter by user ID or state", placeholder="e.g. 12 or reached", key="node_search").strip().lower()
    if filter_text:
        node_df = node_df[
            node_df.astype(str).apply(lambda col: col.str.lower().str.contains(filter_text, regex=False)).any(axis=1)
        ]
    st.dataframe(node_df, use_container_width=True, hide_index=True, height=300)


# ─────────────────────────────────────────────────────────────────────────────
# Strategy lab
# ─────────────────────────────────────────────────────────────────────────────
with strategy_tab:
    section_heading("BENCHMARK ARENA", "Which intervention contains the spread?",
                    f"Strategies evaluated over {data['n_runs']} repeated trials using a shared baseline.")
    chart_col, result_col = st.columns([1.65, 1], gap="large")
    with chart_col:
        comparison_fig, comparison_df = make_comparison_chart(summary, total_users)
        st.plotly_chart(comparison_fig, use_container_width=True, config={"displaylogo": False}, key="strategy_comparison")
    with result_col:
        st.markdown(
            f'<div class="insight"><div class="panel-kicker">BEST OBSERVED</div>'
            f'<div class="panel-title" style="color:{GREEN};font-size:1.3rem">{STRATEGY_NAMES[best_key]}</div>'
            f'<div class="big-number" style="color:{CYAN};margin-top:12px">{best_reduction:+.1f}%</div>'
            f'<p class="footnote">Reach reduction relative to the no-intervention baseline.</p><hr>'
            f'<p>Average baseline reach: <b>{baseline:.2f}</b></p>'
            f'<p>Average reach with this strategy: <b>{best_avg:.2f}</b></p>'
            f'<p>Average users avoided: <b>{reach_delta:.2f}</b></p></div>',
            unsafe_allow_html=True,
        )
    st.markdown("#### Strategy scorecard")
    strategy_rows = []
    for key, metrics in summary.items():
        strategy_rows.append({
            "Strategy": STRATEGY_NAMES.get(key, key),
            "Average reach": round(metrics["average_reach"], 2),
            "Variation (std dev)": round(metrics["std_reach"], 2),
            "Best run": metrics["min_reach"],
            "Worst run": metrics["max_reach"],
            "Reduction vs baseline": f'{metrics["reduction_percent"]:.1f}%',
            "Intervention targets": 0 if key == "no_intervention" else data["budget"],
        })
    st.dataframe(pd.DataFrame(strategy_rows), use_container_width=True, hide_index=True)
    st.caption("A lower average reach is better. Standard deviation describes run-to-run variability; small samples can be noisy.")
    with st.expander("How the strategies work"):
        st.markdown(
            "- **Random selection:** chooses targets randomly.\n"
            "- **Degree centrality:** prioritizes users with many direct connections.\n"
            "- **Betweenness centrality:** prioritizes users that connect different parts of the network.\n"
            "- **Greedy selection:** estimates which additional target most reduces simulated reach.\n"
            "- **No intervention:** baseline run without selected targets."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Report and export
# ─────────────────────────────────────────────────────────────────────────────
with report_tab:
    section_heading("EXPERIMENT RECORD", "Reproducible results",
                    "Export this experiment's strategy summary and inspect the parameters used.")
    report_rows = []
    for key, metrics in summary.items():
        report_rows.append({
            "strategy_key": key,
            "strategy": STRATEGY_NAMES.get(key, key),
            "average_reach_users": round(metrics["average_reach"], 4),
            "standard_deviation": round(metrics["std_reach"], 4),
            "minimum_reach": metrics["min_reach"],
            "maximum_reach": metrics["max_reach"],
            "reduction_percent": round(metrics["reduction_percent"], 4),
            "intervention_budget": 0 if key == "no_intervention" else data["budget"],
            "runs": data["n_runs"],
        })
    report_df = pd.DataFrame(report_rows)
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        st.markdown('<div class="panel-kicker">EXPERIMENT PARAMETERS</div>', unsafe_allow_html=True)
        st.json({
            "network_model": data["model_label"],
            "network_users": total_users,
            "network_edges": graph.number_of_edges(),
            "source_user": source,
            "transmission_probability": data["transmission_prob"],
            "intervention_budget": data["budget"],
            "maximum_rounds": data["max_rounds"],
            "evaluation_runs": data["n_runs"],
            "random_seed": data["seed"],
            "selected_network_view": data["strategy_label"],
        })
    with c2:
        st.markdown('<div class="panel-kicker">INTERPRETATION</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="panel"><div class="panel-title">What this run suggests</div>'
            f'<p class="footnote">In this generated network, <b>{STRATEGY_NAMES[best_key]}</b> produced the lowest average reach across the strategies tested.</p>'
            f'<p class="footnote">Average reach moved from {baseline:.2f} users without intervention to {best_avg:.2f} users under the best observed strategy.</p>'
            f'<p class="footnote">This result depends on the network, random seed, transmission probability, budget, and number of trials.</p></div>',
            unsafe_allow_html=True,
        )
    st.dataframe(report_df, use_container_width=True, hide_index=True)
    st.download_button(
        "↓  Download strategy report (CSV)",
        data=report_df.to_csv(index=False).encode("utf-8"),
        file_name="outbreak_of_lies_experiment_report.csv",
        mime="text/csv",
        use_container_width=False,
    )
    raw_df = pd.DataFrame(raw_results)
    with st.expander("View individual simulation runs"):
        if not raw_df.empty:
            display_cols = [col for col in ["run", "strategy", "final_reach", "reached_fraction", "rounds", "intervention_count"] if col in raw_df]
            st.dataframe(raw_df[display_cols], use_container_width=True, hide_index=True)
            st.download_button(
                "Download raw runs (CSV)",
                data=raw_df.to_csv(index=False).encode("utf-8"),
                file_name="outbreak_of_lies_raw_runs.csv",
                mime="text/csv",
            )

st.markdown("---")
st.markdown(
    '<div class="footnote">OUTBREAK OF LIES · A synthetic network simulation for experimentation and education. '
    'It does not detect truth in real posts, monitor live social platforms, or block real accounts.</div>',
    unsafe_allow_html=True,
)
