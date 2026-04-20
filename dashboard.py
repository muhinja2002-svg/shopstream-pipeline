"""
ShopStream Dashboard
--------------------
A live analytics dashboard powered by Streamlit and DuckDB.

Run with:
    streamlit run dashboard.py
"""

import time
import duckdb
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

DB_PATH = "data/shopstream.db"
AUTO_REFRESH_SECONDS = 10

st.set_page_config(
    page_title="ShopStream Analytics",
    page_icon="🛒",
    layout="wide",
)

# ── Header ──────────────────────────────────────────────────────────────────
st.title("🛒 ShopStream — Live Analytics")
st.caption(
    f"Auto-refreshes every {AUTO_REFRESH_SECONDS}s · "
    f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
)

# ── Data loading ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=AUTO_REFRESH_SECONDS)
def load_all():
    """Query DuckDB and return all data needed by the dashboard."""
    try:
        db = duckdb.connect(DB_PATH, read_only=True)

        # Conversion funnel aggregates
        funnel = db.execute("""
            WITH user_steps AS (
                SELECT
                    event_json->>'user_id' AS user_id,
                    MAX(CASE WHEN event_json->>'event_type' = 'page_view'    THEN 1 ELSE 0 END) AS saw_page,
                    MAX(CASE WHEN event_json->>'event_type' = 'add_to_cart'  THEN 1 ELSE 0 END) AS added_to_cart,
                    MAX(CASE WHEN event_json->>'event_type' = 'order_placed' THEN 1 ELSE 0 END) AS purchased
                FROM raw_events
                GROUP BY user_id
            )
            SELECT
                SUM(saw_page)                                                              AS total_visitors,
                SUM(added_to_cart)                                                         AS total_adds,
                SUM(purchased)                                                             AS total_purchases,
                ROUND(SUM(purchased)::FLOAT / NULLIF(SUM(saw_page), 0) * 100, 2)          AS conversion_rate,
                ROUND(SUM(added_to_cart)::FLOAT / NULLIF(SUM(saw_page), 0) * 100, 2)      AS page_to_cart_pct,
                ROUND(SUM(purchased)::FLOAT / NULLIF(SUM(added_to_cart), 0) * 100, 2)     AS cart_to_order_pct
            FROM user_steps
        """).df()

        # Events per hour over the last 24 hours
        events_over_time = db.execute("""
            SELECT
                DATE_TRUNC('hour', (event_json->>'timestamp')::TIMESTAMP) AS hour,
                event_json->>'event_type'                                  AS event_type,
                COUNT(*)                                                    AS event_count
            FROM raw_events
            WHERE (event_json->>'timestamp')::TIMESTAMP >= NOW() - INTERVAL '24 hours'
            GROUP BY 1, 2
            ORDER BY 1
        """).df()

        # Top SKUs by revenue from completed orders
        top_skus = db.execute("""
            SELECT
                event_json->>'sku'                                                          AS sku,
                COUNT(*) FILTER (WHERE event_json->>'event_type' = 'order_placed')          AS orders,
                ROUND(
                    SUM(CASE WHEN event_json->>'event_type' = 'order_placed'
                        THEN (event_json->>'price')::FLOAT ELSE 0 END), 2
                )                                                                           AS revenue
            FROM raw_events
            GROUP BY sku
            HAVING orders > 0
            ORDER BY revenue DESC
            LIMIT 10
        """).df()

        # 20 most recently ingested events
        recent = db.execute("""
            SELECT
                event_json->>'timestamp'              AS event_time,
                event_json->>'event_type'             AS event_type,
                event_json->>'user_id'                AS user_id,
                event_json->>'session_id'             AS session_id,
                event_json->>'sku'                    AS sku,
                ROUND((event_json->>'price')::FLOAT, 2) AS price
            FROM raw_events
            ORDER BY ingested_at DESC
            LIMIT 20
        """).df()

        total_events = db.execute("SELECT COUNT(*) FROM raw_events").fetchone()[0]

        db.close()
        return funnel, events_over_time, top_skus, recent, total_events, None

    except Exception as e:
        return None, None, None, None, 0, str(e)


funnel, events_over_time, top_skus, recent, total_events, error = load_all()

# ── Error state ───────────────────────────────────────────────────────────────
if error:
    st.error(f"❌ Could not connect to database: {error}")
    st.info("Make sure `consumer.py` has run and created `data/shopstream.db`.")
    st.stop()

if funnel is None or funnel.empty or funnel.iloc[0]["total_visitors"] == 0:
    st.warning("⚠️ No data yet. Start `producer.py` and `consumer.py` to generate events.")
    st.stop()

row = funnel.iloc[0]

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Events",      f"{total_events:,}")
k2.metric("Unique Visitors",   f"{int(row['total_visitors']):,}")
k3.metric("Add to Cart",       f"{int(row['total_adds']):,}",
          delta=f"{row['page_to_cart_pct']}% of visitors")
k4.metric("Orders",            f"{int(row['total_purchases']):,}",
          delta=f"{row['cart_to_order_pct']}% of carts")
k5.metric("Overall Conversion",f"{row['conversion_rate']}%")

st.markdown("---")

# ── Funnel + Events over time ─────────────────────────────────────────────────
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Conversion Funnel")
    fig_funnel = go.Figure(
        go.Funnel(
            y=["Page View", "Add to Cart", "Order Placed"],
            x=[
                int(row["total_visitors"]),
                int(row["total_adds"]),
                int(row["total_purchases"]),
            ],
            textinfo="value+percent initial",
            marker=dict(color=["#1D9E75", "#EF9F27", "#534AB7"]),
        )
    )
    fig_funnel.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

with col_right:
    st.subheader("Events — Last 24 Hours")
    if not events_over_time.empty:
        fig_line = px.line(
            events_over_time,
            x="hour",
            y="event_count",
            color="event_type",
            markers=True,
            color_discrete_map={
                "page_view":    "#1D9E75",
                "add_to_cart":  "#EF9F27",
                "order_placed": "#534AB7",
            },
            labels={"event_count": "Events", "hour": "Time", "event_type": ""},
        )
        fig_line.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No events in the last 24 hours — run `producer.py` to generate live data.")

st.markdown("---")

# ── Top SKUs + Recent Events ──────────────────────────────────────────────────
col_left2, col_right2 = st.columns([1, 2])

with col_left2:
    st.subheader("Top 10 SKUs by Revenue")
    if not top_skus.empty:
        top_skus["revenue"] = top_skus["revenue"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(top_skus, use_container_width=True, hide_index=True)
    else:
        st.info("No completed orders yet.")

with col_right2:
    st.subheader("Recent Events (Live Feed)")
    if recent is not None and not recent.empty:
        # Colour-code by event type
        def highlight_event(row):
            colours = {
                "page_view":    "background-color: #E1F5EE",
                "add_to_cart":  "background-color: #FAEEDA",
                "order_placed": "background-color: #EEEDFE",
            }
            return [colours.get(row["event_type"], "")] * len(row)

        st.dataframe(
            recent.style.apply(highlight_event, axis=1),
            use_container_width=True,
            hide_index=True,
        )

# ── Refresh button + auto-refresh ─────────────────────────────────────────────
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

# Auto-refresh loop — sleeps then triggers a full rerun
time.sleep(AUTO_REFRESH_SECONDS)
st.rerun()
