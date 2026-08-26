"""
VENTORA — AI Inventory Risk Intelligence
=========================================
Predict. Optimize. Preserve.

Company-facing web application built on top of the verified, frozen analytical
pipeline (reconstruct.py -> Risk Engine -> Recommendation Engine ->
Business-Value Simulation). This app performs NO model inference, NO
retraining, and NO recomputation of any upstream analytical component. It is a
presentation + data-intake layer over already-verified artifacts:

    data/risk_df_recommendations_FINAL.pkl   (35,165 evaluation batches)
    data/business_value_comparison.csv       (3 simulated scenarios)

Run:
    streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==================================================================
# BRAND CONFIG (VENTORA brand guidelines)
# ==================================================================
BRAND = {
    "name": "VENTORA",
    "tagline": "Predict. Optimize. Preserve.",
    "deep_forest": "#003020",
    "intelligence_green": "#005030",
    "brand_green": "#2E7926",
    "signature_lime": "#C2E700",
    "off_white": "#F5F8F3",
    "white": "#FFFFFF",
    "muted_gray": "#82908A",
    "black": "#050807",
}
RISK_LEVELS_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
RISK_COLORS = {"LOW": "#2E9B62", "MEDIUM": "#E3B93F", "HIGH": "#E47A32", "CRITICAL": "#C83C32"}

DATA_DIR = Path(__file__).parent / "data"
ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"

# Columns the analytics dataset itself contains (source of truth for what the
# app CAN show). These are NOT the same as the raw input schema required to
# run the frozen models end-to-end — see "Company Data" limitation below.
RECOMMENDATION_DISPLAY_COLS = [
    "batch_id", "item_id", "category", "days_until_expiry", "current_inventory",
    "potential_excess_inventory", "expected_waste_exposure", "intervention_scope",
    "recommendation",
]

# Fields a company would need to provide for the RAW model pipeline
# (reconstruct.py) to run end-to-end. Documented, not invented.
REQUIRED_RAW_FIELDS = ["batch_id", "item_id", "category", "received_date", "expiry_date", "qty_received"]
OPTIONAL_RAW_FIELDS = ["food_category", "selling_price", "is_promoted", "is_holiday", "shelf_life_days"]
MODEL_ONLY_FIELDS = [
    "trailing_mean_7", "trailing_mean_28", "demand_cv_28", "snap_days_in_life",
    "event_days_in_life", "price_rel_52w",
]

st.set_page_config(
    page_title="VENTORA — AI Inventory Risk Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================================================================
# GLOBAL STYLE
# ==================================================================
st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {BRAND['off_white']}; }}
    section[data-testid="stSidebar"] {{
        background-color: {BRAND['deep_forest']};
    }}
    section[data-testid="stSidebar"] * {{ color: {BRAND['off_white']} !important; }}
    section[data-testid="stSidebar"] hr {{ border-color: #1a4a38; }}
    h1, h2, h3 {{ color: {BRAND['deep_forest']}; font-family: 'Montserrat', 'Segoe UI', sans-serif; }}
    div[data-testid="stMetric"] {{
        background-color: {BRAND['white']};
        border: 1px solid #DDE6DF;
        border-radius: 10px;
        padding: 14px 16px;
    }}
    div[data-testid="stMetric"] label {{ color: {BRAND['muted_gray']} !important; }}
    .venhero {{
        background: linear-gradient(135deg, {BRAND['deep_forest']} 0%, {BRAND['intelligence_green']} 100%);
        border-radius: 16px;
        padding: 36px 40px;
        color: {BRAND['off_white']};
        margin-bottom: 20px;
    }}
    .venhero h1 {{ color: {BRAND['white']}; margin-bottom: 4px; }}
    .venhero p {{ color: {BRAND['off_white']}; opacity: 0.9; font-size: 1.05rem; }}
    .venbadge {{
        display: inline-block; background-color: {BRAND['signature_lime']};
        color: {BRAND['deep_forest']}; font-weight: 600; border-radius: 20px;
        padding: 4px 14px; font-size: 0.85rem; margin-right: 8px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ==================================================================
# DATA LOADING (cached, read-only — never mutates or re-derives model outputs)
# ==================================================================
@st.cache_data
def load_demo_risk_df():
    df = pd.read_pickle(DATA_DIR / "risk_df_recommendations_FINAL.pkl")
    df["risk_level"] = pd.Categorical(df["risk_level"], categories=RISK_LEVELS_ORDER, ordered=True)
    return df


@st.cache_data
def load_business_value():
    return pd.read_csv(DATA_DIR / "business_value_comparison.csv", index_col=0)


try:
    demo_df = load_demo_risk_df()
    bv_df = load_business_value()
    DATA_LOAD_OK = True
except Exception as e:
    DATA_LOAD_OK = False
    st.error(f"Could not load required data files from `{DATA_DIR}`. Error: {e}")
    st.stop()

TOTAL_DEMO_BATCHES = len(demo_df)

# ==================================================================
# SESSION STATE
# ==================================================================
if "data_mode" not in st.session_state:
    st.session_state.data_mode = "demo"          # "demo" or "company"
if "uploaded_validated" not in st.session_state:
    st.session_state.uploaded_validated = None    # holds validation report dict
if "uploaded_preview" not in st.session_state:
    st.session_state.uploaded_preview = None       # holds preview DataFrame


from venlib import validate_company_csv  # noqa: E402  (testable validation logic)
from backend.inference import RiskEngine, ModelUnavailableError, generate_recommendation  # noqa: E402


# ==================================================================
# SIDEBAR — BRANDING + NAVIGATION
# ==================================================================
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    st.caption(BRAND["tagline"])
    st.divider()

    page = st.radio(
        "Navigate",
        [
            "🏠 Home",
            "📥 Data Input",
            "1 · Executive Overview",
            "2 · Risk Explorer",
            "3 · Recommendations",
            "4 · Business Impact",
        ],
    )
    st.divider()

    mode_label = "Verified Demo Dataset" if st.session_state.data_mode == "demo" else "Company Upload (validation only)"
    st.markdown(f"**Active data source:**\n\n{mode_label}")
    st.caption(
        f"Evaluation population: **{TOTAL_DEMO_BATCHES:,}** reconstructed inventory batches "
        "(real M5 retail sales + USDA FoodKeeper shelf-life data, test period)."
    )
    st.divider()
    st.caption(
        "Pipeline: Real Data → Batch Reconstruction → Demand Forecast (XGBoost) + "
        "Spoilage Prediction (LightGBM) → Risk Engine → Recommendation Engine → "
        "Business-Value Simulation."
    )

# Analytics pages always render the verified demo dataset — it is the only
# dataset in this deployment with actual model-generated risk scores.
risk_df = demo_df

# ==================================================================
# PAGE — HOME
# ==================================================================
if page == "🏠 Home":
    st.markdown(
        f"""
        <div class="venhero">
            <span class="venbadge">AI Inventory Risk Intelligence</span>
            <h1>{BRAND['name']}</h1>
            <p>{BRAND['tagline']}</p>
            <p>VENTORA identifies which inventory is most likely to become waste, explains why,
            and recommends what to do next.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    for col, num, label in zip(
        [c1, c2, c3, c4], ["01", "02", "03", "04"],
        ["PREDICT — demand + spoilage", "PRIORITIZE — risk engine",
         "RECOMMEND — what to do next", "MEASURE — business impact"]
    ):
        col.markdown(
            f"<div style='background:{BRAND['white']};border:1px solid #DDE6DF;border-radius:10px;"
            f"padding:16px;height:110px;'><span style='color:{BRAND['signature_lime']};"
            f"font-weight:700;background:{BRAND['deep_forest']};padding:2px 8px;border-radius:6px;"
            f"font-size:0.8rem;'>{num}</span><p style='margin-top:10px;color:{BRAND['deep_forest']};"
            f"font-weight:600;'>{label}</p></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    st.subheader("Get started")
    gs1, gs2 = st.columns(2)
    with gs1:
        st.markdown("**Explore the verified demo dataset**")
        st.caption(f"{TOTAL_DEMO_BATCHES:,} real, reconstructed inventory batches with model-generated "
                    "risk scores and recommendations — ready to explore immediately.")
        if st.button("Use Verified Demo Dataset →", type="primary"):
            st.session_state.data_mode = "demo"
            st.success("Demo dataset active. Open **Executive Overview** in the sidebar.")
    with gs2:
        st.markdown("**Provide your own inventory data**")
        st.caption("Upload a CSV/Excel file for schema validation. See the **Data Input** page for "
                    "supported fields and current limitations.")
        if st.button("Go to Data Input →"):
            st.info("Select **📥 Data Input** in the sidebar.")

    st.divider()
    st.subheader("Full Analytics Dashboard")
    st.caption(
        "The original Streamlit analytics dashboard (Executive Overview, Risk Explorer, "
        "Business Impact, Recommendations) is preserved unchanged and runs as a separate "
        "app at `dashboard/app.py`. This web application is the company-facing entry point; "
        "the dashboard remains the deep-dive analytics/exploration layer."
    )
    st.code("cd dashboard && streamlit run app.py", language="bash")

    st.divider()
    st.caption(
        "This application is a decision-support tool. Risk scores are model outputs, not "
        "certainties; business-value figures are simulated under stated assumptions, not "
        "guaranteed savings."
    )

# ==================================================================
# PAGE — DATA INPUT
# ==================================================================
elif page == "📥 Data Input":
    st.title("Data Input")
    st.caption("Bring your own inventory data, or use the verified demo dataset.")

    mode = st.radio(
        "Data source",
        ["Use Verified Demo Dataset", "Upload Company Data"],
        index=0 if st.session_state.data_mode == "demo" else 1,
        horizontal=True,
    )
    st.session_state.data_mode = "demo" if mode == "Use Verified Demo Dataset" else "company"

    if mode == "Use Verified Demo Dataset":
        st.success(
            f"Dataset validated successfully.\n\n**{TOTAL_DEMO_BATCHES:,}** inventory batches are "
            "ready for analysis. This is the fully verified, model-scored evaluation population."
        )
        st.dataframe(demo_df.head(20), use_container_width=True, height=300)

    else:
        st.markdown("#### Supported input schema")
        s1, s2 = st.columns(2)
        with s1:
            st.markdown("**Required fields**")
            st.code("\n".join(REQUIRED_RAW_FIELDS), language=None)
        with s2:
            st.markdown("**Optional fields**")
            st.code("\n".join(OPTIONAL_RAW_FIELDS), language=None)

        st.warning(
            "⚠️ **Basic upload validates schema only.** Standard inventory fields (the schema "
            "above) are not enough to compute a Risk Score on their own — the models also need "
            "trailing historical sales features "
            + ", ".join(f"`{c}`" for c in MODEL_ONLY_FIELDS)
            + " derived from the project's original historical sales data. If your file only has "
            "the standard fields, you'll get validation + preview here, not a Risk Score. "
            "See **Advanced: full-feature scoring** below if you can supply those engineered "
            "features directly."
        )

        uploaded = st.file_uploader("Upload inventory data (CSV or Excel)", type=["csv", "xlsx", "xls"])
        if uploaded is not None:
            status, report = validate_company_csv(uploaded.getvalue(), uploaded.name)
            if status == "error" and "message" in report and "missing_required" not in report:
                st.error(f"Dataset validation failed.\n\n{report['message']}")
            else:
                st.markdown(f"**Rows:** {report['n_rows']:,} · **Columns:** {report['n_cols']}")
                if report["missing_required"]:
                    st.error(
                        "Dataset validation failed.\n\nMissing required field(s): "
                        + ", ".join(f"`{c}`" for c in report["missing_required"])
                    )
                else:
                    st.success(
                        f"Dataset validated successfully.\n\n**{report['n_rows']:,}** inventory "
                        "records passed schema validation."
                    )
                    if report["present_optional"]:
                        st.caption("Optional fields detected: " + ", ".join(report["present_optional"]))
                    if len(report["missing_values"]) > 0:
                        st.warning("Missing values detected in required fields:\n\n" +
                                   "\n".join(f"- `{k}`: {v} missing" for k, v in report["missing_values"].items()))
                st.markdown("**Preview (first 20 rows)**")
                st.dataframe(report["preview"], use_container_width=True, height=300)

        st.divider()
        with st.expander("🔬 Advanced: full-feature scoring (uses the verified deployment models)"):
            st.markdown(
                "If your file already includes the fully engineered feature columns the frozen "
                "models expect (not just standard inventory fields), the app can run real "
                "inference using the verified `spoilage_model.joblib` / `demand_model.joblib` "
                "artifacts — no fake or estimated predictions."
            )
            engine = RiskEngine()
            if not engine.is_available:
                st.error(
                    "The deployment models are not currently loadable in this environment "
                    "(likely missing `lightgbm`/`xgboost`/`pyarrow`, or the artifacts aren't "
                    "present). This is an environment limitation, not a feature that's been "
                    "removed — see `deployment_artifacts/model_metadata.json` for what's required."
                )
            else:
                st.success("Deployment models loaded successfully — full-feature scoring is available.")
                st.caption("Required raw columns for the spoilage model: "
                           + ", ".join(f"`{c}`" for c in engine.spoilage.raw_required_columns()))
                st.caption("Required raw columns for the demand model (one row per category): "
                           + ", ".join(f"`{c}`" for c in engine.demand.raw_required_columns()))

                st.markdown("##### 🟢 Live Inference Demonstration")
                st.caption(
                    "No engineered data of your own yet? Load a small **synthetic** demo input — 6 "
                    "batches built for demonstration purposes using real, training-period item_ids "
                    "(so they resolve against `item_share_lookup.parquet`) with hand-set feature "
                    "values. This is **not** real company or sales data. Loading it runs the exact "
                    "same code path as an uploaded file: genuine LightGBM/XGBoost inference through "
                    "the verified deployment models, not a lookup of precomputed results."
                )
                if st.button("▶ Load Live Inference Demo"):
                    try:
                        demo_batches = pd.read_csv(DATA_DIR / "demo_live_inference_batches.csv")
                        demo_demand = pd.read_csv(DATA_DIR / "demo_live_inference_category_demand.csv")
                        demo_scored = engine.score(demo_batches, demo_demand)
                        demo_scored[["recommendation", "intervention_scope"]] = demo_scored.apply(
                            generate_recommendation, axis=1)
                        st.success(
                            f"**Live Inference Demonstration — {len(demo_scored)} synthetic batches "
                            "scored just now** by the verified `spoilage_model.joblib` / "
                            "`demand_model.joblib` (this run, this click — not the 35,165-batch "
                            "Verified Reference Results shown elsewhere in this app)."
                        )
                        st.dataframe(
                            demo_scored[["batch_id", "item_id", "category", "spoilage_probability",
                                         "risk_score", "risk_level", "recommendation"]],
                            use_container_width=True, height=260,
                        )
                    except ModelUnavailableError as e:
                        st.error(f"Model unavailable: {e}")
                    except ValueError as e:
                        st.error(f"Input error: {e}")

                st.markdown("##### Or bring your own fully-engineered data")
                adv_file = st.file_uploader("Batch-level file (fully engineered)", type=["csv"], key="adv_batches")
                adv_demand_file = st.file_uploader("Category-demand file (fully engineered)", type=["csv"],
                                                    key="adv_demand")
                if adv_file is not None and adv_demand_file is not None and st.button("Run Risk Analysis"):
                    try:
                        batches_df = pd.read_csv(adv_file)
                        demand_df = pd.read_csv(adv_demand_file)
                        scored = engine.score(batches_df, demand_df)
                        scored[["recommendation", "intervention_scope"]] = scored.apply(
                            generate_recommendation, axis=1)
                        st.success(f"Scored {len(scored):,} batches using the verified deployment models.")
                        st.dataframe(
                            scored[["batch_id", "item_id", "spoilage_probability", "risk_score",
                                    "risk_level", "recommendation"]],
                            use_container_width=True, height=400,
                        )
                        csv_out = scored.to_csv(index=False).encode("utf-8")
                        st.download_button("⬇ Download scored results (CSV)", csv_out,
                                            "ventora_company_scored.csv", "text/csv")
                    except ModelUnavailableError as e:
                        st.error(f"Model unavailable: {e}")
                    except ValueError as e:
                        st.error(f"Input error: {e}")

# ==================================================================
# PAGE 1 — EXECUTIVE OVERVIEW
# ==================================================================
elif page == "1 · Executive Overview":
    if st.session_state.data_mode == "company":
        st.info("Showing the **Verified Demo Dataset** — full inference on uploaded company data "
                "is not yet supported (see Data Input page).")

    st.title("Executive Overview")
    st.caption("What is at risk, and what value can the system create?")

    dist = risk_df["risk_level"].value_counts().reindex(RISK_LEVELS_ORDER).fillna(0).astype(int)
    high_crit_n = int(dist["HIGH"] + dist["CRITICAL"])
    total_exposure = risk_df["expected_waste_exposure"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Batches Evaluated", f"{TOTAL_DEMO_BATCHES:,}")
    c2.metric("High + Critical Batches", f"{high_crit_n:,}", f"{high_crit_n/TOTAL_DEMO_BATCHES:.1%} of total")
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
        dist_pct = (dist / TOTAL_DEMO_BATCHES * 100).round(1)
        fig = go.Figure(go.Bar(
            x=RISK_LEVELS_ORDER, y=dist.values,
            marker_color=[RISK_COLORS[l] for l in RISK_LEVELS_ORDER],
            text=[f"{v:,} ({p}%)" for v, p in zip(dist.values, dist_pct.values)],
            textposition="outside",
        ))
        fig.update_layout(yaxis_title="Batches", xaxis_title="Risk Level", height=380,
                           margin=dict(t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Actual Spoilage Rate by Risk Level")
        st.caption("Validates that the Risk Engine's tiering tracks real spoilage outcomes.")
        spoil_by_level = risk_df.groupby("risk_level", observed=True)["was_spoiled"].mean().reindex(RISK_LEVELS_ORDER) * 100
        fig2 = go.Figure(go.Bar(
            x=RISK_LEVELS_ORDER, y=spoil_by_level.values,
            marker_color=[RISK_COLORS[l] for l in RISK_LEVELS_ORDER],
            text=[f"{v:.1f}%" for v in spoil_by_level.values],
            textposition="outside",
        ))
        fig2.update_layout(yaxis_title="Observed Spoilage Rate (%)", xaxis_title="Risk Level", height=380,
                            margin=dict(t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("What the system recommends")
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
        batches carry a replenishment-only action aimed at future orders, not this batch.
        """
    )

# ==================================================================
# PAGE 2 — RISK EXPLORER
# ==================================================================
elif page == "2 · Risk Explorer":
    if st.session_state.data_mode == "company":
        st.info("Showing the **Verified Demo Dataset** — full inference on uploaded company data "
                "is not yet supported (see Data Input page).")

    st.title("Risk Explorer")
    st.caption("Filter and inspect batch-level risk detail.")

    f1, f2, f3, f4 = st.columns(4)
    sel_levels = f1.multiselect("Risk Level", RISK_LEVELS_ORDER, default=RISK_LEVELS_ORDER)
    sel_categories = f2.multiselect("Category", sorted(risk_df["category"].unique()))
    max_days = int(risk_df["days_until_expiry"].max())
    days_range = f3.slider("Days Until Expiry", 0, max_days, (0, max_days))
    min_excess = f4.number_input("Min. Potential Excess", min_value=0, value=0, step=1)

    filtered = risk_df[risk_df["risk_level"].isin(sel_levels)]
    if sel_categories:
        filtered = filtered[filtered["category"].isin(sel_categories)]
    filtered = filtered[
        (filtered["days_until_expiry"] >= days_range[0]) & (filtered["days_until_expiry"] <= days_range[1])
    ]
    filtered = filtered[filtered["potential_excess_inventory"] >= min_excess]

    st.markdown(f"**{len(filtered):,}** of {TOTAL_DEMO_BATCHES:,} batches match the current filters.")

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
        show_df, use_container_width=True, height=520,
        column_config={
            "Spoilage Probability": st.column_config.ProgressColumn("Spoilage Probability", min_value=0, max_value=1, format="%.2f"),
            "Risk Score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100, format="%.1f"),
        },
        hide_index=True,
    )
    st.caption(
        "Spoilage Probability is the model's raw output — not necessarily a calibrated real-world "
        "probability. Risk Score is a composite prioritization score, not a probability."
    )

    csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download filtered batches (CSV)", csv, "ventora_filtered_batches.csv", "text/csv")

# ==================================================================
# PAGE 3 — RECOMMENDATIONS
# ==================================================================
elif page == "3 · Recommendations":
    if st.session_state.data_mode == "company":
        st.info("Showing the **Verified Demo Dataset** — full inference on uploaded company data "
                "is not yet supported (see Data Input page).")

    st.title("Recommendations")
    st.caption("Which batches need attention, and what should the manager do?")

    tabs = st.tabs(["🔴 Critical", "🟠 High", "🟡 Medium", "🟢 Low"])
    level_map = {"🔴 Critical": "CRITICAL", "🟠 High": "HIGH", "🟡 Medium": "MEDIUM", "🟢 Low": "LOW"}

    all_filtered_frames = []
    for tab, label in zip(tabs, level_map):
        level = level_map[label]
        with tab:
            sub = risk_df[risk_df["risk_level"] == level]
            st.markdown(f"**{len(sub):,}** batches at {level} risk ({len(sub)/TOTAL_DEMO_BATCHES:.1%} of total).")

            if level in ("HIGH", "CRITICAL"):
                small_batch = sub[sub["current_inventory"] <= 2]
                if len(small_batch) > 0:
                    st.warning(
                        f"⚠️ {len(small_batch):,} of these batches ({len(small_batch)/len(sub):.1%}) have "
                        "**2 units or fewer received**. The recommendation text below still applies "
                        "(unchanged, per the frozen Recommendation Engine), but for very small batches "
                        "'discount / redistribute' may be operationally impractical — use judgment "
                        "alongside the inventory figures shown."
                    )

            labels = {
                "batch_id": "Batch ID", "item_id": "Item", "category": "Category",
                "days_until_expiry": "Days to Expiry", "current_inventory": "Inventory",
                "potential_excess_inventory": "Potential Excess", "expected_waste_exposure": "Expected Waste Exposure",
                "intervention_scope": "Scope", "recommendation": "Recommendation",
            }
            sub_show = sub[RECOMMENDATION_DISPLAY_COLS].rename(columns=labels).sort_values(
                "Expected Waste Exposure", ascending=False)
            st.dataframe(sub_show, use_container_width=True, height=420, hide_index=True)
            all_filtered_frames.append(sub[RECOMMENDATION_DISPLAY_COLS])

    st.divider()
    st.subheader("Intervention Scope Summary")
    scope_summary = risk_df.groupby(["risk_level", "intervention_scope"], observed=True).size().reset_index(name="count")
    scope_summary = scope_summary[scope_summary["count"] > 0]
    fig = px.bar(
        scope_summary, x="risk_level", y="count", color="intervention_scope",
        category_orders={"risk_level": RISK_LEVELS_ORDER},
        labels={"risk_level": "Risk Level", "count": "Batches", "intervention_scope": "Intervention Scope"},
        color_discrete_sequence=[BRAND["muted_gray"], BRAND["brand_green"], BRAND["signature_lime"]],
    )
    fig.update_layout(height=380, margin=dict(t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    export_priority = pd.concat(all_filtered_frames, ignore_index=True) if all_filtered_frames else risk_df[RECOMMENDATION_DISPLAY_COLS]
    csv = export_priority.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download all recommendations, priority order (CSV)", csv,
                        "ventora_recommendations.csv", "text/csv")

# ==================================================================
# PAGE 4 — BUSINESS IMPACT
# ==================================================================
elif page == "4 · Business Impact":
    if st.session_state.data_mode == "company":
        st.info("Showing the **Verified Demo Dataset** — full inference on uploaded company data "
                "is not yet supported (see Data Input page).")

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
    fig.add_trace(go.Bar(name="Baseline Waste (observed)", x=bv_df.index, y=bv_df["Baseline Waste Units"],
                          marker_color=BRAND["muted_gray"]))
    fig.add_trace(go.Bar(name="AI-Assisted Waste (simulated)", x=bv_df.index, y=bv_df["AI-Assisted Waste Units"],
                          marker_color=BRAND["intelligence_green"]))
    fig.update_layout(barmode="group", yaxis_title="Waste Units", height=420,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                       margin=dict(t=40, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
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

    st.divider()
    csv = bv_df.reset_index().to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download scenario table (CSV)", csv, "ventora_business_impact.csv", "text/csv")
