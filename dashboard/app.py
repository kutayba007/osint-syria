"""
OSINT Syria - Tactical Dashboard
Streamlit-powered interactive command center with live threat map.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from src.database.supabase_client import SupabaseDB

# === Page Config ===
st.set_page_config(
    page_title="OSINT Syria — مركز القيادة",
    page_icon="🇸🇾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === Dark Theme CSS ===
st.markdown("""
<style>
    /* Dark background */
    .stApp {
        background-color: #0a0a0f;
        color: #e0e0e0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111118;
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #333;
        border-radius: 12px;
        padding: 16px;
    }
    
    [data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-size: 2rem !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #00d4ff !important;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
    }
    
    /* Threat level badges */
    .threat-critical {
        background: linear-gradient(135deg, #ff1744 0%, #d50000 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        animation: pulse 1.5s infinite;
    }
    .threat-high {
        background: linear-gradient(135deg, #ff9100 0%, #ff6d00 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
    }
    .threat-medium {
        background: linear-gradient(135deg, #ffd600 0%, #ffc400 100%);
        color: #333;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
    }
    .threat-low {
        background: linear-gradient(135deg, #00e676 0%, #00c853 100%);
        color: #333;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }
    
    /* Event cards */
    .event-card {
        background: #1a1a2e;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #00d4ff;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #555;
        padding: 20px;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)


def init_db():
    """Initialize database connection."""
    if "db" not in st.session_state:
        db = SupabaseDB()
        db.connect()
        st.session_state.db = db
    return st.session_state.db


def load_data(db, hours=24):
    """Load events from database."""
    events = db.get_recent_events(hours=hours)
    if events:
        return pd.DataFrame(events)
    return pd.DataFrame()


def render_header():
    """Render the main header."""
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='font-size: 2.5em; margin: 0;'>🇸🇾 OSINT SYRIA</h1>
        <p style='color: #888; font-size: 1.1em; margin-top: 5px;'>
            منصة استخبارات مصادر مفتوحة وإنذار مبكر
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(df):
    """Render top-level metrics."""
    col1, col2, col3, col4, col5 = st.columns(5)

    total = len(df)
    critical = len(df[df["threat_level"] == "critical"]) if "threat_level" in df.columns else 0
    high = len(df[df["threat_level"] == "high"]) if "threat_level" in df.columns else 0
    avg_conf = df["confidence"].mean() if "confidence" in df.columns and len(df) > 0 else 0
    gov_count = df["governorate"].nunique() if "governorate" in df.columns else 0

    with col1:
        st.metric("📨 إجمالي الأحداث", total)
    with col2:
        st.metric("🔴 حرجة", critical, delta=None)
    with col3:
        st.metric("🟠 عالية", high, delta=None)
    with col4:
        st.metric("🎯 متوسط الثقة", f"{avg_conf:.0%}")
    with col5:
        st.metric("🏛 المحافظات", gov_count)


def render_threat_map(df):
    """Render the interactive threat map using PyDeck."""
    st.markdown("### 🗺️ الخريطة التكتيكية الحية")

    if df.empty or "latitude" not in df.columns:
        st.info("📭 لا توجد بيانات جغرافية لعرضها حالياً")
        return

    # Filter events with coordinates
    map_df = df.dropna(subset=["latitude", "longitude"])

    if map_df.empty:
        st.info("📭 لا توجد إحداثيات متاحة")
        return

    # Color mapping for threat levels
    color_map = {
        "critical": [255, 23, 68],      # Red
        "high": [255, 145, 0],           # Orange
        "medium": [255, 214, 0],         # Yellow
        "low": [0, 230, 118],            # Green
    }

    map_df = map_df.copy()
    map_df["color"] = map_df["threat_level"].map(color_map).apply(
        lambda x: x if x else [100, 100, 100]
    )
    map_df["radius"] = map_df["threat_level"].map({
        "critical": 3000,
        "high": 2000,
        "medium": 1200,
        "low": 800,
    }).fillna(800)

    # Scatterplot Layer — event markers
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["longitude", "latitude"],
        get_color="color",
        get_radius="radius",
        opacity=0.7,
        pickable=True,
        auto_highlight=True,
    )

    # Text Layer — event labels
    text_layer = pdk.Layer(
        "TextLayer",
        data=map_df,
        get_position=["longitude", "latitude"],
        get_text="event_type",
        get_size=14,
        get_color=[255, 255, 255],
        get_alignment_baseline="'bottom'",
        get_pixel_offset=[0, -20],
    )

    # Heatmap Layer
    heatmap_layer = pdk.Layer(
        "HeatmapLayer",
        data=map_df,
        get_position=["longitude", "latitude"],
        get_weight="confidence",
        radiusPixels=60,
        intensity=1,
        threshold=0.05,
        colorRange=[
            [0, 255, 200, 50],
            [0, 200, 255, 100],
            [0, 100, 255, 150],
            [100, 0, 255, 200],
            [255, 0, 100, 255],
        ],
    )

    # View state — centered on Syria
    view_state = pdk.ViewState(
        latitude=34.8,
        longitude=38.0,
        zoom=6,
        pitch=45,
    )

    # Render the map
    st.pydeck_chart(pdk.Deck(
        layers=[heatmap_layer, scatter_layer, text_layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v11",
        tooltip={
            "html": """
                <b style='color: #00d4ff;'>{event_type}</b><br/>
                📍 {location_name}<br/>
                🏛 {governorate}<br/>
                ⚠️ Threat: <b>{threat_level}</b><br/>
                <i>{summary_ar}</i>
            """,
            "style": {
                "backgroundColor": "#1a1a2e",
                "color": "#e0e0e0",
                "fontSize": "13px",
                "padding": "8px",
                "borderRadius": "8px",
                "border": "1px solid #00d4ff",
            }
        },
    ))


def render_charts(df):
    """Render analytics charts."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 توزيع الأحداث حسب النوع")
        if "event_type" in df.columns and not df.empty:
            type_counts = df["event_type"].value_counts()
            fig = px.bar(
                x=type_counts.values,
                y=type_counts.index,
                orientation="h",
                color=type_counts.values,
                color_continuous_scale="Viridis",
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0a0a0f",
                plot_bgcolor="#0a0a0f",
                height=400,
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 لا توجد بيانات كافية")

    with col2:
        st.markdown("### 🏛 توزيع الأحداث حسب المحافظة")
        if "governorate" in df.columns and not df.empty:
            gov_counts = df["governorate"].value_counts().head(10)
            fig = px.pie(
                values=gov_counts.values,
                names=gov_counts.index,
                color_discrete_sequence=px.colors.qualitative.Dark24,
                hole=0.4,
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0a0a0f",
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                font=dict(color="#e0e0e0"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 لا توجد بيانات كافية")

    # Timeline
    st.markdown("### ⏱ خط زمني للأحداث")
    if "timestamp" in df.columns and not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df_sorted = df.sort_values("timestamp")

        fig = px.scatter(
            df_sorted,
            x="timestamp",
            y="threat_level",
            color="threat_level",
            color_discrete_map={
                "critical": "#ff1744",
                "high": "#ff9100",
                "medium": "#ffd600",
                "low": "#00e676",
            },
            hover_data=["event_type", "summary_ar", "governorate"],
            size_max=15,
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0a0a0f",
            plot_bgcolor="#0a0a0f",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)


def render_events_feed(df):
    """Render the live events feed."""
    st.markdown("### 📋 آخر الأحداث")

    if df.empty:
        st.info("📭 لا توجد أحداث لعرضها")
        return

    for _, row in df.head(20).iterrows():
        threat = row.get("threat_level", "low")
        css_class = f"threat-{threat}"

        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(threat, "⚪")

        st.markdown(f"""
        <div class="event-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="{css_class}">{icon} {threat.upper()}</span>
                <span style="color: #888; font-size: 0.85em;">{row.get('timestamp', 'N/A')}</span>
            </div>
            <h4 style="margin: 8px 0 4px 0; color: #fff;">{row.get('event_type', 'غير محدد')}</h4>
            <p style="color: #ccc; margin: 4px 0;">{row.get('summary_ar', 'لا ملخص')}</p>
            <div style="color: #888; font-size: 0.85em;">
                📍 {row.get('location_name', 'N/A')} | 🏛 {row.get('governorate', 'N/A')} | 
                📢 @{row.get('source_channel', 'N/A')} | 🎯 {row.get('confidence', 0):.0%}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar controls."""
    with st.sidebar:
        st.markdown("## ⚙️ لوحة التحكم")

        st.markdown("---")
        st.markdown("### 🔍 فلترة البيانات")

        hours = st.select_slider(
            "الوقت الحالي",
            options=[6, 12, 24, 48, 72, 168],
            value=24,
            format_func=lambda x: f"آخر {x} ساعة"
        )

        threat_filter = st.multiselect(
            "مستوى الخطورة",
            ["critical", "high", "medium", "low"],
            default=["critical", "high", "medium", "low"]
        )

        st.markdown("---")
        st.markdown("### 📊 إحصائيات سريعة")

        # System status
        st.markdown("""
        <div style="background: #1a1a2e; padding: 12px; border-radius: 8px;">
            <p style="color: #00e676;">🟢 النظام يعمل</p>
            <p style="color: #888; font-size: 0.85em;">آخر تحديث: just now</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        if st.button("🔄 تحديث البيانات", use_container_width=True):
            st.rerun()

        st.markdown("---")
        st.markdown("""
        <div class="footer">
            🇸🇾 OSINT Syria<br/>
            Early Warning System<br/>
            v1.0.0
        </div>
        """, unsafe_allow_html=True)

        return hours, threat_filter


def main():
    """Main dashboard function."""
    # Initialize
    db = init_db()
    render_header()

    # Sidebar
    hours, threat_filter = render_sidebar()

    # Load data
    df = load_data(db, hours=hours)

    # Apply filters
    if not df.empty and "threat_level" in df.columns:
        df = df[df["threat_level"].isin(threat_filter)]

    # Render sections
    render_metrics(df)
    st.markdown("---")

    # Map
    render_threat_map(df)
    st.markdown("---")

    # Charts
    render_charts(df)
    st.markdown("---")

    # Events feed
    render_events_feed(df)

    # Auto-refresh
    st.markdown("""
    <meta http-equiv="refresh" content="60">
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
