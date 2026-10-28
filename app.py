"""Gold stock-transfer monitor: adapted version.

All figures are SAMPLE (practice) data, not real market or central-bank data.

Adaptation: a "Compare two countries" view in the Declared tab. It answers
"Did two countries buy or sell at the same time, and how far apart did their
totals drift?", with a month-range control and a running-total option.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import design

DATA = Path(__file__).parent / "data"

st.set_page_config(page_title="Gold stock-transfer monitor", layout="wide")


@st.cache_data
def load(name: str) -> pd.DataFrame:
    """Read data/<name>.csv and turn any date column into real dates."""
    df = pd.read_csv(DATA / f"{name}.csv")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


price = load("price")
etf = load("etf")
declared = load("declared")
gap = load("gap")
swiss = load("swiss")

etf["total_t"] = etf["gld_t"] + etf["iau_t"]
latest = declared["date"].max()
last_12 = declared[declared["date"] > latest - pd.DateOffset(months=12)]
ranking = (
    last_12.groupby("country", as_index=False)["net_purchases_t"].sum()
    .sort_values("net_purchases_t")
)

# ---------------------------------------------------------------- header
st.title("Gold stock-transfer monitor")
st.caption(
    f"Who holds the stock, and which way it is moving. "
    f"**Sample data**, as of {latest:%B %Y}."
)

top_buyer = ranking.iloc[-1]
top_seller = ranking.iloc[0]
p_now, p_prev = price["price_usd_oz"].iloc[-1], price["price_usd_oz"].iloc[-2]
e_now, e_prev = etf["total_t"].iloc[-1], etf["total_t"].iloc[-2]
latest_gap = gap.iloc[-1]

m = st.columns(5)
m[0].metric("Price, $/oz", f"{p_now:,.0f}", f"{(p_now / p_prev - 1):+.1%} m/m")
m[1].metric("GLD + IAU holdings", f"{e_now:,.0f} t", f"{e_now - e_prev:+.0f} t m/m")
m[2].metric(
    f"Unreported gap, {latest_gap['quarter']}",
    f"{latest_gap['estimated_t'] - latest_gap['reported_t']:+.0f} t",
)
m[3].metric("Top buyer, 12m", top_buyer["country"], f"{top_buyer['net_purchases_t']:+.0f} t")
m[4].metric("Top seller, 12m", top_seller["country"], f"{top_seller['net_purchases_t']:+.0f} t")

st.caption(
    "Solid lines show reported series; dashed lines show estimates. "
    "Each country keeps one colour on every chart."
)

tabD, tabI = st.tabs(["Declared", "Inferred"])

# ---------------------------------------------------------------- Declared
with tabD:
    st.subheader("Price and its opportunity cost")
    st.caption("Has the price moved away from the level real yields would imply? (sample data)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=price["date"], y=price["yield_implied_usd_oz"], name="Yield-implied",
        line=dict(color="grey", dash=design.ESTIMATE_DASH, width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=price["date"], y=price["price_usd_oz"], name="Actual price",
        line=dict(color=design.GOLD, width=2.5),
        fill="tonexty", fillcolor="rgba(168,130,42,0.12)",
    ))
    fig.update_yaxes(title="$ per ounce")
    st.plotly_chart(design.style(fig, 420), width="stretch")
    st.caption("Shaded area: actual price above the yield-implied level.")

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.subheader("Western investor holdings")
        fig = px.line(
            etf, x="date", y="total_t",
            labels={"date": "Month", "total_t": "Tonnes held"},
            title="GLD + IAU gold held (sample data)",
        )
        fig.update_traces(line_color=design.ETF_GREY)
        st.plotly_chart(design.style(fig), width="stretch")
    with right:
        st.subheader("Declared official sector")
        fig = px.bar(
            ranking, x="net_purchases_t", y="country", orientation="h",
            color="country",
            color_discrete_map={c: design.colour_for(c) for c in ranking["country"]},
            labels={"net_purchases_t": "Tonnes, last 12 months", "country": ""},
            title="Net purchases, last 12 months (sample data)",
        )
        fig.update_layout(showlegend=False, hovermode="closest")
        st.plotly_chart(design.style(fig), width="stretch")

    with st.expander("12-month detail per bank"):
        detail = last_12.pivot(index="date", columns="country", values="net_purchases_t")
        detail.index = detail.index.strftime("%b %Y")
        st.dataframe(detail.round(1), width="stretch")

    # -------- NEW VIEW: compare two countries over a chosen period --------
    st.divider()
    st.subheader("Compare two countries over time")
    st.caption(
        "Did two countries buy or sell at the same time? Choose two countries "
        "and a period. **Sample data**, not real central-bank figures."
    )

    countries = sorted(declared["country"].unique())
    col_a, col_b = st.columns(2)
    with col_a:
        country_a = st.selectbox(
            "First country", countries,
            index=countries.index("China") if "China" in countries else 0,
        )
    with col_b:
        country_b = st.selectbox(
            "Second country", countries,
            index=countries.index("Russia") if "Russia" in countries else 1,
        )

    first = declared["date"].min().to_pydatetime()
    last = declared["date"].max().to_pydatetime()
    start, end = st.slider(
        "Months to show", min_value=first, max_value=last,
        value=(first, last), format="MMM YYYY",
    )
    view = st.radio(
        "Show", ["Monthly purchases and sales", "Running total"], horizontal=True
    )

    if country_a == country_b:
        st.warning("Choose two different countries to compare.")
    else:
        pair = declared[
            declared["country"].isin([country_a, country_b])
            & declared["date"].between(start, end)
        ].sort_values("date").copy()
        colours = {country_a: design.colour_for(country_a),
                   country_b: design.colour_for(country_b)}
        if colours[country_a] == colours[country_b]:
            colours[country_b] = "#2E8B7A"  # keep the two countries distinguishable

        t1, t2 = st.columns(2)
        for col, c in [(t1, country_a), (t2, country_b)]:
            total = pair.loc[pair["country"] == c, "net_purchases_t"].sum()
            col.metric(f"{c}: net over selected months", f"{total:+,.0f} t")

        if view == "Monthly purchases and sales":
            fig = px.bar(
                pair, x="date", y="net_purchases_t", color="country",
                barmode="group", color_discrete_map=colours,
                labels={"date": "Month", "net_purchases_t": "Tonnes", "country": "Country"},
                title=f"{country_a} vs {country_b}: monthly purchases and sales (sample data)",
            )
        else:
            pair["running_total_t"] = pair.groupby("country")["net_purchases_t"].cumsum()
            fig = px.line(
                pair, x="date", y="running_total_t", color="country",
                color_discrete_map=colours,
                labels={"date": "Month", "running_total_t": "Tonnes (cumulative)",
                        "country": "Country"},
                title=f"{country_a} vs {country_b}: running total from {start:%b %Y} (sample data)",
            )
        fig.add_hline(y=0, line_width=1, line_color="grey")
        st.plotly_chart(design.style(fig, 420), width="stretch")
        st.caption(
            "Above zero means net buying; below zero means net selling. The ranking "
            "above covers only the latest 12 months; this view covers the months you choose."
        )

# ---------------------------------------------------------------- Inferred
with tabI:
    st.subheader("Reported purchases beside an estimate")
    st.caption("Tonnes per quarter: reported by central banks vs an outside estimate (sample data).")
    show_mine = st.toggle("Show mine replenishment", value=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=gap["quarter"], y=gap["reported_t"], name="Reported", marker_color="#3B3A36",
    ))
    fig.add_trace(go.Scatter(
        x=gap["quarter"], y=gap["estimated_t"], name="Estimate",
        line=dict(color=design.GOLD, dash=design.ESTIMATE_DASH, width=2),
    ))
    if show_mine:
        fig.add_hline(
            y=900, line_dash="dot", line_color="grey",
            annotation_text="Approx. quarterly mine supply (sample)",
        )
    fig.update_yaxes(title="Tonnes per quarter")
    st.plotly_chart(design.style(fig), width="stretch")

    st.subheader("Where is gold being sent?")
    fig = px.area(
        swiss, x="date", y="exports_t", color="destination",
        color_discrete_map={d: design.colour_for(d) for d in swiss["destination"].unique()},
        labels={"date": "Month", "exports_t": "Tonnes per month", "destination": "Destination"},
        title="Swiss exports by destination (sample data)",
    )
    st.plotly_chart(design.style(fig), width="stretch")

st.caption(
    "All values are sample data for teaching. Sources when live would include COMEX "
    "futures, FRED real yields, GLD and IAU holdings, IMF IFS, World Gold Council and "
    "Swiss-Impex."
)
