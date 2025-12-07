import json
import os
import sys
import subprocess
from typing import Dict, Any

import pandas as pd
import streamlit as st
import plotly.express as px


# =========================
# Paths / constants
# =========================

AGENT_SCRIPT = os.path.join("projects", "atomberg_sov", "atomberg_sov_agent.py")
OVERALL_PATH = "overall_sov.json"
BY_KW_PATH = "sov_by_keyword.json"
INSIGHTS_PATH = "insights.md"


# =========================
# Helpers: run pipeline + load & reshape
# =========================

def run_agent_pipeline() -> bool:
    """
    Run the YouTube SoV agent script to refresh data.
    Uses the same Python interpreter that runs Streamlit.
    """
    if not os.path.exists(AGENT_SCRIPT):
        st.error(f"Agent script not found at: {AGENT_SCRIPT}")
        return False

    try:
        with st.spinner("Running YouTube SoV agent (this may take a few minutes)..."):
            result = subprocess.run(
                [sys.executable, AGENT_SCRIPT],
                check=True,
                capture_output=True,
                text=True,
            )
            # Uncomment for debugging:
            # st.text(result.stdout)
            # st.text(result.stderr)
    except subprocess.CalledProcessError as e:
        st.error("Agent script failed. See details below.")
        st.code(e.stdout + "\n" + e.stderr)
        return False

    # Clear cached data so new JSON is loaded
    load_overall_sov.clear()
    load_sov_by_keyword.clear()
    return True


@st.cache_data
def load_overall_sov(path: str = OVERALL_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File '{path}' not found.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_sov_by_keyword(path: str = BY_KW_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File '{path}' not found.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_insights(path: str = INSIGHTS_PATH) -> str:
    """
    Load AI-generated insights from insights.md (written by atomberg_sov_agent.py)
    """
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def overall_to_df(overall: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for brand, m in overall["metrics"].items():
        rows.append({
            "brand": brand,
            "posts_with_brand": m["posts_with_brand"],
            "sov_content": m["sov_content"],
            "sov_engagement": m["sov_engagement"],
            "sov_comments": m["sov_comments"],
            "share_of_positive_voice": m["share_of_positive_voice"],
        })
    df = pd.DataFrame(rows)
    # nicer display
    df["brand"] = df["brand"].str.capitalize()
    return df


def by_keyword_to_df(by_kw: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for kw, data in by_kw.items():
        for brand, m in data["metrics"].items():
            rows.append({
                "keyword": kw,
                "brand": brand.capitalize(),
                "posts_with_brand": m["posts_with_brand"],
                "sov_content": m["sov_content"],
                "sov_engagement": m["sov_engagement"],
                "sov_comments": m["sov_comments"],
                "share_of_positive_voice": m["share_of_positive_voice"],
            })
    return pd.DataFrame(rows)


# =========================
# Streamlit UI
# =========================

def main():
    st.set_page_config(
        page_title="Atomberg YouTube Share of Voice Dashboard",
        layout="wide",
    )

    st.title("📊 Atomberg Share of Voice (SoV) Dashboard")

    st.markdown(
        """
        This dashboard summarizes how **Atomberg** performs compared to other fan brands
        for smart-fan-related keywords across platforms (starting with YouTube, extensible to
        Google/Instagram/X).

        **Data source (current live demo):**
        - YouTube search results for keywords like **"smart fan"**, **"BLDC fan"**, **"smart ceiling fan"**, etc.
        - Top N videos per keyword, plus top comments and engagement metrics.
        - Brand mentions extracted from titles, descriptions, and comments.
        - Simple lexicon-based sentiment to approximate **Share of Positive Voice**.
        """
    )

    # ---- Sidebar: controls & refresh ----
    st.sidebar.header("Controls")

    if st.sidebar.button("🔁 Refresh data (run SoV agent)"):
        ok = run_agent_pipeline()
        if ok:
            st.sidebar.success("Data refreshed successfully!")
        else:
            st.sidebar.error("Failed to refresh data. See error above.")

    st.sidebar.markdown("---")
    st.sidebar.info(
        "Use the button above to re-run the SoV agent (YouTube + insights) "
        "and update the dashboard with fresh data."
    )

    # ---- Load data (auto-run agent if missing) ----
    try:
        overall_raw = load_overall_sov()
        by_kw_raw = load_sov_by_keyword()
    except FileNotFoundError:
        st.warning("No data files found yet. Running the SoV agent once...")
        ok = run_agent_pipeline()
        if not ok:
            st.stop()
        overall_raw = load_overall_sov()
        by_kw_raw = load_sov_by_keyword()

    overall_df = overall_to_df(overall_raw)
    kw_df = by_keyword_to_df(by_kw_raw)
    insights_md = load_insights()

    # =========================
    # Platform dimension (for future Google/IG/X)
    # =========================

    # If backend later adds a platform field, we respect it. For now, default to YouTube.
    if "platform" not in overall_df.columns:
        overall_df["platform"] = "YouTube"
    if "platform" not in kw_df.columns:
        kw_df["platform"] = "YouTube"

    all_platforms = sorted(overall_df["platform"].unique())

    st.sidebar.header("Filters & Settings")

    selected_platforms = st.sidebar.multiselect(
        "Platforms:",
        options=all_platforms,
        default=all_platforms,
    )

    if not selected_platforms:
        st.warning("Please select at least one platform.")
        st.stop()

    # Filter overall + keyword data by platform
    overall_platform_df = overall_df[overall_df["platform"].isin(selected_platforms)].copy()
    kw_platform_df = kw_df[kw_df["platform"].isin(selected_platforms)].copy()

    if overall_platform_df.empty or kw_platform_df.empty:
        st.warning("No data for the selected platform(s).")
        st.stop()

    # Keywords filter (after platform filter)
    all_keywords = sorted(kw_platform_df["keyword"].unique())
    selected_keywords = st.sidebar.multiselect(
        "Keywords (for per-keyword view):",
        options=all_keywords,
        default=all_keywords,
    )

    # Metric selector
    metric_map = {
        "Content SoV (share of videos mentioning brand)": "sov_content",
        "Engagement SoV (views+likes+comments)": "sov_engagement",
        "Share of Positive Voice (SoPV)": "share_of_positive_voice",
        "Comment SoV (share of brand mentions in comments)": "sov_comments",
    }
    metric_label = st.sidebar.selectbox(
        "Metric to visualize:",
        options=list(metric_map.keys()),
        index=1,  # default: engagement
    )
    metric_col = metric_map[metric_label]

    # Brand focus
    focus_brand_options = sorted(overall_platform_df["brand"].unique())
    default_focus_idx = (
        focus_brand_options.index("Atomberg")
        if "Atomberg" in focus_brand_options
        else 0
    )
    focus_brand = st.sidebar.selectbox(
        "Focus brand (for KPI cards):",
        options=focus_brand_options,
        index=default_focus_idx,
    )

    # =========================
    # Cross-platform summary cards
    # =========================
    st.subheader("Cross-Platform SoV Coverage")

    col_p1, col_p2, col_p3 = st.columns(3)
    col_p1.metric("Platforms analyzed", str(len(all_platforms)))
    col_p2.metric("Platforms selected", ", ".join(selected_platforms))
    col_p3.metric("Keywords tracked", str(len(all_keywords)))

    # =========================
    # Overall KPIs (top row)
    # =========================
    st.subheader("Overall Brand Performance (All Selected Platforms & Keywords)")

    # Sort by engagement SoV for selected platforms
    df_sorted = (
        overall_platform_df.sort_values("sov_engagement", ascending=False)
        .reset_index(drop=True)
    )

    # find focus brand row
    focus_row = df_sorted[df_sorted["brand"] == focus_brand].iloc[0]

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric(
        label=f"{focus_brand} – Content SoV",
        value=f"{focus_row['sov_content']*100:.1f}%",
        help="Share of all videos (in top search results) that mention this brand "
             "across the selected platforms."
    )
    col_kpi2.metric(
        label=f"{focus_brand} – Engagement SoV",
        value=f"{focus_row['sov_engagement']*100:.1f}%",
        help="Share of total engagement (views + 10×likes + 20×comments) "
             "across the selected platforms."
    )
    col_kpi3.metric(
        label=f"{focus_brand} – Share of Positive Voice",
        value=f"{focus_row['share_of_positive_voice']*100:.1f}%",
        help="Brand's share of positive, engagement-weighted sentiment "
             "across the selected platforms."
    )

    # =========================
    # Overall bar chart
    # =========================
    st.markdown("### Overall Share of Voice by Brand (Selected Platforms)")

    fig_overall = px.bar(
        df_sorted,
        x="brand",
        y=metric_col,
        text=df_sorted[metric_col].apply(lambda v: f"{v*100:.1f}%"),
        labels={"brand": "Brand", metric_col: metric_label},
        title=metric_label,
    )
    fig_overall.update_traces(textposition="outside")
    fig_overall.update_layout(
        yaxis_tickformat=".0%",
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )

    st.plotly_chart(fig_overall, use_container_width=True)

    # =========================
    # Per-keyword analysis
    # =========================
    st.markdown("### Per-Keyword Share of Voice")

    if selected_keywords:
        kw_filtered = kw_platform_df[kw_platform_df["keyword"].isin(selected_keywords)].copy()
    else:
        kw_filtered = kw_platform_df.copy()

    # Aggregate by keyword + brand for the chosen metric
    kw_metric_df = (
        kw_filtered.groupby(["keyword", "brand"], as_index=False)[metric_col]
        .mean()
    )

    # Heatmap style plot (keyword vs brand)
    pivot = kw_metric_df.pivot(index="keyword", columns="brand", values=metric_col).fillna(0)

    fig_kw = px.imshow(
        pivot,
        labels=dict(x="Brand", y="Keyword", color=metric_label),
        aspect="auto",
        zmin=0,
        zmax=pivot.values.max() if pivot.values.max() > 0 else 1,
        text_auto=".1%",
        title=f"{metric_label} by Keyword and Brand (Selected Platforms)",
    )
    st.plotly_chart(fig_kw, use_container_width=True)

    # =========================
    # Scatter: Engagement vs Positive Voice
    # =========================
    st.markdown("### Engagement vs. Positive Voice (Selected Platforms)")

    scatter_df = overall_platform_df.copy()
    scatter_df["sov_engagement_pct"] = scatter_df["sov_engagement"] * 100
    scatter_df["sopv_pct"] = scatter_df["share_of_positive_voice"] * 100

    fig_scatter = px.scatter(
        scatter_df,
        x="sov_engagement_pct",
        y="sopv_pct",
        text="brand",
        labels={
            "sov_engagement_pct": "Engagement SoV (%)",
            "sopv_pct": "Share of Positive Voice (%)",
        },
        title="Are brands both visible *and* positively perceived?",
    )
    fig_scatter.update_traces(textposition="top center")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # =========================
    # Raw tables
    # =========================
    with st.expander("Show underlying tables"):
        st.markdown("#### Overall metrics table (with platform column)")
        st.dataframe(
            overall_platform_df.style.format({
                "sov_content": "{:.2%}",
                "sov_engagement": "{:.2%}",
                "sov_comments": "{:.2%}",
                "share_of_positive_voice": "{:.2%}",
            }),
            use_container_width=True,
        )

        st.markdown("#### Per-keyword metrics table (with platform column)")
        st.dataframe(
            kw_platform_df.style.format({
                "sov_content": "{:.2%}",
                "sov_engagement": "{:.2%}",
                "sov_comments": "{:.2%}",
                "share_of_positive_voice": "{:.2%}",
            }),
            use_container_width=True,
        )

    # =========================
    # AI-Generated Insights & Recommendations
    # =========================
    # st.markdown("### 🧠 AI-Generated Insights & Recommendations")

    if insights_md.strip():
        st.markdown(insights_md, unsafe_allow_html=True)
    else:
        st.info(
            "No insights file found yet. Run the SoV agent once (using the "
            "Refresh data button in the sidebar) to generate AI-driven recommendations."
        )


if __name__ == "__main__":
    main()
