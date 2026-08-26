"""
AI-Driven Smart Inventory Analytics System — Decision-Support Dashboard
=========================================================================
Consumes the verified, frozen recommendation-enhanced dataset produced by the
upstream pipeline (reconstruct.py -> Risk Engine -> recommendation_engine.py).

This app performs NO model inference, NO retraining, and NO recomputation of
the Risk Engine or Business-Value Simulation. It is a pure presentation layer
over already-verified artifacts:

    data/risk_df_recommendations_FINAL.pkl   (35,165 evaluation batches)
    data/business_value_comparison.csv       (3 simulated scenarios)

Run:
    streamlit run app.py
"""
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
RISK_LEVELS_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
RISK_COLORS = {"LOW": "#2E7D32", "MEDIUM": "#F9A825", "HIGH": "#EF6C00", "CRITICAL": "#C62828"}

st.set_page_config(
    page_title="Smart Inventory Analytics — Decision Support",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# Data loading (cached, read-only — never mutates or re-derives model outputs)
# ------------------------------------------------------------------
@st.cache_data
def load_risk_df():
    path = DATA_DIR / "risk_df_recommendations_FINAL.pkl"
    df = pd.read_pickle(path)
    df["risk_level"] = pd.Categorical(df["risk_level"], categories=RISK_LEVELS_ORDER, ordered=True)
    return df


@st.cache_data
def load_business_value():
    path = DATA_DIR / "business_value_comparison.csv"
    return pd.read_csv(path, index_col=0)


try:
    risk_df = load_risk_df()
    bv_df = load_business_value()
    DATA_LOAD_OK = True
except Exception as e:
    DATA_LOAD_OK = False
    st.error(
        f"Could not load required data files from `{DATA_DIR}`. "
        f"Expected `risk_df_recommendations_FINAL.pkl` and `business_value_comparison.csv`. "
        f"Error: {e}"
    )
    st.stop()

TOTAL_BATCHES = len(risk_df)

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
st.sidebar.title("📦 Smart Inventory Analytics")
st.sidebar.caption("AI-Driven Expiry Risk & Waste Reduction — Decision Support System")
page = st.sidebar.radio(
    "Navigate",
    ["1 · Executive Overview", "2 · Risk Explorer", "3 · Business Impact", "4 · Recommendations"],
)
st.sidebar.divider()
st.sidebar.markdown(
    f"""
**Data scope**
Evaluation population: **{TOTAL_BATCHES:,}** reconstructed inventory batches
(real M5 retail sales + USDA FoodKeeper shelf-life data, test period).

This is the model evaluation population, not the full historical source dataset.
"""
)
st.sidebar.divider()
st.sidebar.caption(
    "Pipeline: Real Data → Batch Reconstruction → Demand Forecast (XGBoost) + "
    "Spoilage Prediction (LightGBM) → Risk Engine → Recommendation Engine → "
    "Business-Value Simulation."
)

# ==================================================================
# PAGE 1 — EXECUTIVE OVERVIEW
# ==================================================================
if page == "1 · Executive Overview":
    st.title("Executive Overview")
    st.caption("What is at risk, and what value can the system create?")

    dist = risk_df["risk_level"].value_counts().reindex(RISK_LEVELS_ORDER).fillna(0).astype(int)
    high_crit_n = int(dist["HIGH"] + dist["CRITICAL"])
    total_exposure = risk_df["expected_waste_exposure"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Batches Evaluated", f"{TOTAL_BATCHES:,}")
    c2.metric("High + Critical Batches", f"{high_crit_n:,}", f"{high_crit_n/TOTAL_BATCHES:.1%} of total")
    c3.metric("Total Expected Waste Exposure", f"{total_exposure:,.0f} units",
              help="Model-predicted, receipt-time exposure from the Risk Engine — a forward-looking "
                   "expectation, not realized/observed waste.")
    base_row = bv_df.loc["Base"]
    c4.metric("Simulated Waste Reduction (Base scenario)", f"{base_row['Waste Reduction %']:.1f}%",
              help="Simulated under stated intervention assumptions — not a measured causal result.")

    st.divider()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Risk Distribution")
        dist_pct = (dist / TOTAL_BATCHES * 100).round(1)
        fig = go.Figure(
            go.Bar(
                x=RISK_LEVELS_ORDER,
                y=dist.values,
                marker_color=[RISK_COLORS[l] for l in RISK_LEVELS_ORDER],
                text=[f"{v:,} ({p}%)" for v, p in zip(dist.values, dist_pct.values)],
                textposition="outside",
            )
        )
        fig.update_layout(
            yaxis_title="Batches", xaxis_title="Risk Level", height=380,
            margin=dict(t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Actual Spoilage Rate by Risk Level")
        st.caption("Validates that the Risk Engine's tiering tracks real spoilage outcomes.")
        spoil_by_level = risk_df.groupby("risk_level", observed=True)["was_spoiled"].mean().reindex(RISK_LEVELS_ORDER) * 100
        fig2 = go.Figure(
            go.Bar(
                x=RISK_LEVELS_ORDER,
                y=spoil_by_level.values,
                marker_color=[RISK_COLORS[l] for l in RISK_LEVELS_ORDER],
                text=[f"{v:.1f}%" for v in spoil_by_level.values],
                textposition="outside",
            )
        )
        fig2.update_layout(
            yaxis_title="Observed Spoilage Rate (%)", xaxis_title="Risk Level", height=380,
            margin=dict(t=10, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("What the system recommends")
    scope_counts = risk_df["intervention_scope"].value_counts()
    s1, s2, s3 = st.columns(3)
    s1.metric("Batch-level intervention", f"{int(risk_df['intervention_scope'].eq('batch-level').sum()):,}",
               help="HIGH/CRITICAL batches with a discount/redistribution action targeting this batch.")
    s2.metric("Replenishment-only", f"{int(risk_df['intervention_scope'].eq('replenishment-only (future batches)').sum()):,}",
               help="MEDIUM batches — action targets future orders, not this batch.")
    s3.metric("No action needed", f"{int(risk_df['intervention_scope'].eq('none').sum()):,}",
               help="LOW risk batches under normal inventory management.")

    st.markdown(
        """
        **Key insight:** Waste is concentrated in a minority of batches. The Risk Engine flags the
        **HIGH** and **CRITICAL** tier — about 1 in 5 batches — as the actionable population where a
        discount, redistribution, or urgent sale could change *this batch's* own outcome. **MEDIUM**
        batches instead drive a replenishment adjustment for *future* orders. **LOW** batches need no
        intervention. The Business-Value Simulation (Page 3) estimates what a consistent intervention
        policy on the HIGH/CRITICAL population could be worth.
        """
    )

# ==================================================================
# PAGE 2 — RISK EXPLORER
# ==================================================================
elif page == "2 · Risk Explorer":
    st.title("Risk Explorer")
    st.caption("Filter and inspect individual batches to identify which inventory needs attention.")

    with st.expander("Filters", expanded=True):
        f1, f2, f3 = st.columns(3)
        sel_risk = f1.multiselect("Risk level", RISK_LEVELS_ORDER, default=["HIGH", "CRITICAL"])
        sel_cat = f2.multiselect("Category", sorted(risk_df["category"].unique().tolist()))
        sel_food = f3.multiselect("Food category", sorted(risk_df["food_category"].unique().tolist()))

        f4, f5, f6 = st.columns(3)
        sel_scope = f4.multiselect("Intervention scope", sorted(risk_df["intervention_scope"].unique().tolist()))
        min_days, max_days = int(risk_df["days_until_expiry"].min()), int(risk_df["days_until_expiry"].max())
        sel_days = f5.slider("Days until expiry", min_days, max_days, (min_days, max_days))
        item_search = f6.text_input("Item ID contains", "")

    filtered = risk_df.copy()
    if sel_risk:
        filtered = filtered[filtered["risk_level"].isin(sel_risk)]
    if sel_cat:
        filtered = filtered[filtered["category"].isin(sel_cat)]
    if sel_food:
        filtered = filtered[filtered["food_category"].isin(sel_food)]
    if sel_scope:
        filtered = filtered[filtered["intervention_scope"].isin(sel_scope)]
    filtered = filtered[
        (filtered["days_until_expiry"] >= sel_days[0]) & (filtered["days_until_expiry"] <= sel_days[1])
    ]
    if item_search:
        filtered = filtered[filtered["item_id"].str.contains(item_search, case=False, na=False)]

    st.markdown(f"**{len(filtered):,}** of {TOTAL_BATCHES:,} batches match the current filters.")

    display_cols = [
        "batch_id", "item_id", "category", "food_category", "days_until_expiry",
        "current_inventory", "expected_demand_before_expiry", "potential_excess_inventory",
        "spoilage_probability", "expected_waste_exposure", "risk_score", "risk_level",
        "recommendation",
    ]
    col_labels = {
        "batch_id": "Batch ID", "item_id": "Item", "category": "Category",
        "food_category": "Food Category", "days_until_expiry": "Days to Expiry",
        "current_inventory": "Inventory", "expected_demand_before_expiry": "Expected Demand (before expiry)",
        "potential_excess_inventory": "Potential Excess", "spoilage_probability": "Spoilage Probability",
        "expected_waste_exposure": "Expected Waste Exposure", "risk_score": "Risk Score",
        "risk_level": "Risk Level", "recommendation": "Recommendation",
    }
    show_df = filtered[display_cols].rename(columns=col_labels).sort_values("Risk Score", ascending=False)

    st.dataframe(
        show_df,
        use_container_width=True,
        height=520,
        column_config={
            "Spoilage Probability": st.column_config.ProgressColumn(
                "Spoilage Probability", min_value=0, max_value=1, format="%.2f"
            ),
            "Risk Score": st.column_config.ProgressColumn(
                "Risk Score", min_value=0, max_value=100, format="%.1f"
            ),
        },
        hide_index=True,
    )

    st.caption(
        "Spoilage Probability is the model's raw output — not necessarily a calibrated real-world "
        "probability. Risk Score is a composite prioritization score, not a probability."
    )

    csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered batches (CSV)", csv, "filtered_batches.csv", "text/csv")

# ==================================================================
# PAGE 3 — BUSINESS IMPACT
# ==================================================================
elif page == "3 · Business Impact":
    st.title("Business Impact")
    st.info(
        "⚠️ **All figures on this page are SIMULATED under stated intervention assumptions.** "
        "They are estimates of what a consistent discount/redistribution policy on HIGH/CRITICAL "
        "batches could achieve — not a measured, real-world, causal result. The baseline itself "
        "(FIFO/FEFO, no intervention) is the real, reconstructed outcome from actual M5 sales; only "
        "the AI-assisted side is simulated."
    )

    baseline_waste = bv_df["Baseline Waste Units"].iloc[0]
    baseline_spoil = bv_df["Baseline Spoilage Rate"].iloc[0]

    st.subheader("Baseline (FIFO/FEFO, No Intervention) — observed, reconstructed")
    b1, b2, b3 = st.columns(3)
    b1.metric("Baseline Waste Units", f"{baseline_waste:,.0f}")
    b2.metric("Baseline Spoilage Rate", f"{baseline_spoil:.1%}")
    b3.metric("Intervention Population (HIGH+CRITICAL)", f"{int(bv_df['Intervention Count (HIGH+CRITICAL)'].iloc[0]):,}")

    st.subheader("Simulated Waste Reduction — AI-Assisted Strategy vs. Baseline")
    st.caption("Three scenarios reflect a range of assumed intervention effectiveness, not a single predicted fact.")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Baseline Waste (observed)",
        x=bv_df.index, y=bv_df["Baseline Waste Units"],
        marker_color="#B0BEC5",
    ))
    fig.add_trace(go.Bar(
        name="AI-Assisted Waste (simulated)",
        x=bv_df.index, y=bv_df["AI-Assisted Waste Units"],
        marker_color="#1565C0",
    ))
    fig.update_layout(
        barmode="group", yaxis_title="Waste Units", height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Scenario Detail")
    scenario_display = bv_df.copy()
    scenario_display["Simulated Waste Reduction"] = scenario_display["Waste Reduction %"].map(lambda x: f"{x:.1f}%")
    scenario_display["Baseline Spoilage Rate"] = scenario_display["Baseline Spoilage Rate"].map(lambda x: f"{x:.1%}")
    scenario_display["AI-Assisted Spoilage Rate (simulated)"] = scenario_display["AI-Assisted Spoilage Rate"].map(lambda x: f"{x:.1%}")
    st.dataframe(
        scenario_display[[
            "Baseline Waste Units", "AI-Assisted Waste Units", "Simulated Waste Reduction",
            "Baseline Spoilage Rate", "AI-Assisted Spoilage Rate (simulated)",
            "Spoilage Rate Reduction (pp)", "Intervention Count (HIGH+CRITICAL)",
        ]],
        use_container_width=True,
    )

    st.markdown(
        """
        **How to read this:** the *Conservative* scenario assumes a modest intervention effect
        (low full-prevention probability, small partial-loss reduction); *Optimistic* assumes a
        stronger effect consistent with the upper end of reported retail markdown/redistribution
        outcomes. The *Base* scenario is the middle assumption. None of these numbers should be
        quoted as "our AI reduces waste by X%" — the correct framing is *"under the simulated
        intervention policy and stated assumptions, waste could be reduced by approximately X%."*
        """
    )

    st.subheader("Reference: Forward-Looking Expected Waste Exposure")
    total_exposure = risk_df["expected_waste_exposure"].sum()
    st.metric("Total Expected Waste Exposure (Risk Engine, predicted)", f"{total_exposure:,.0f} units")
    st.caption(
        "This is a distinct, receipt-time PREDICTED quantity from the Risk Engine — kept separate "
        "from the realized baseline waste and the simulated AI-assisted waste above, per the "
        "terminology lock."
    )

# ==================================================================
# PAGE 4 — RECOMMENDATIONS
# ==================================================================
elif page == "4 · Recommendations":
    st.title("Recommendations")
    st.caption("Which batches need attention, and what should the manager do?")

    tabs = st.tabs(["🔴 Critical", "🟠 High", "🟡 Medium", "🟢 Low"])
    level_map = {"🔴 Critical": "CRITICAL", "🟠 High": "HIGH", "🟡 Medium": "MEDIUM", "🟢 Low": "LOW"}

    for tab, label in zip(tabs, level_map):
        level = level_map[label]
        with tab:
            sub = risk_df[risk_df["risk_level"] == level]
            st.markdown(f"**{len(sub):,}** batches at {level} risk ({len(sub)/TOTAL_BATCHES:.1%} of total).")

            if level in ("HIGH", "CRITICAL"):
                small_batch = sub[sub["current_inventory"] <= 2]
                if len(small_batch) > 0:
                    st.warning(
                        f"⚠️ {len(small_batch):,} of these batches ({len(small_batch)/len(sub):.1%}) have "
                        f"**2 units or fewer received**. The recommendation text below still applies "
                        f"(unchanged, per the frozen Recommendation Engine), but for very small batches "
                        f"'discount / redistribute' may be operationally impractical — use judgment "
                        f"alongside the inventory figures shown."
                    )

            cols = [
                "batch_id", "item_id", "category", "days_until_expiry", "current_inventory",
                "potential_excess_inventory", "expected_waste_exposure", "intervention_scope",
                "recommendation",
            ]
            labels = {
                "batch_id": "Batch ID", "item_id": "Item", "category": "Category",
                "days_until_expiry": "Days to Expiry", "current_inventory": "Inventory",
                "potential_excess_inventory": "Potential Excess", "expected_waste_exposure": "Expected Waste Exposure",
                "intervention_scope": "Scope", "recommendation": "Recommendation",
            }
            st.dataframe(
                sub[cols].rename(columns=labels).sort_values("Expected Waste Exposure", ascending=False),
                use_container_width=True, height=420, hide_index=True,
            )

    st.divider()
    st.subheader("Intervention Scope Summary")
    scope_summary = risk_df.groupby(["risk_level", "intervention_scope"], observed=True).size().reset_index(name="count")
    scope_summary = scope_summary[scope_summary["count"] > 0]
    fig = px.bar(
        scope_summary, x="risk_level", y="count", color="intervention_scope",
        category_orders={"risk_level": RISK_LEVELS_ORDER},
        labels={"risk_level": "Risk Level", "count": "Batches", "intervention_scope": "Intervention Scope"},
    )
    fig.update_layout(height=380, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
