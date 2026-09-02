"""
OSINT Syria — Tactical Dashboard (Self-Contained)
Connects directly to Supabase. No parent project imports needed.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_supabase():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        st.error("❌ SUPABASE_URL and SUPABASE_KEY are required! Set them in Streamlit Cloud secrets or .env")
        st.stop()
    from supabase import create_client
    return create_client(url, key)


st.set_page_config(page_title="OSINT Syria", page_icon="🇸🇾", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #0a0a0f; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #111118; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #333; border-radius: 12px; padding: 16px;
    }
    [data-testid="stMetricValue"] { color: #00d4ff !important; font-size: 2rem !important; }
    h1, h2, h3 { color: #00d4ff !important; }
    .tc { background: linear-gradient(135deg, #ff1744, #d50000); color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold; animation: pulse 1.5s infinite; }
    .th { background: linear-gradient(135deg, #ff9100, #ff6d00); color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold; }
    .tm { background: linear-gradient(135deg, #ffd600, #ffc400); color: #333; padding: 4px 12px; border-radius: 20px; font-weight: bold; }
    .tl { background: linear-gradient(135deg, #00e676, #00c853); color: #333; padding: 4px 12px; border-radius: 20px; font-weight: bold; }
    @keyframes pulse { 0%{opacity:1} 50%{opacity:0.6} 100%{opacity:1} }
    .ec { background: #1a1a2e; border: 1px solid #333; border-radius: 12px; padding: 16px; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=30)
def load_events(hours: int) -> pd.DataFrame:
    sb = get_supabase()
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    for tbl in ["events", "osint_events"]:
        try:
            r = sb.table(tbl).select("*").gte("timestamp_utc", since).order("timestamp_utc", desc=True).limit(200).execute()
            if r.data:
                df = pd.DataFrame(r.data)
                st.session_state["table"] = tbl
                return df
        except Exception:
            pass
    # Fallback without time filter
    for tbl in ["events", "osint_events"]:
        try:
            r = sb.table(tbl).select("*").order("created_at", desc=True).limit(200).execute()
            if r.data:
                df = pd.DataFrame(r.data)
                st.session_state["table"] = tbl
                return df
        except Exception:
            pass
    return pd.DataFrame()


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Map Supabase column names to dashboard-friendly names."""
    if df.empty:
        return df
    renames = {
        "timestamp_utc": "timestamp",
        "confidence_score": "confidence",
        "title": "event_type",
        "title_arabic": "summary_ar",
        "raw_excerpt_arabic": "summary_ar",
        "raw_excerpt_english": "summary_en",
    }
    for old, new in renames.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
    if "threat_level" in df.columns:
        df["threat_level"] = df["threat_level"].str.lower()
    return df


# === Header ===
st.markdown("<div style='text-align:center;padding:20px 0'><h1 style='font-size:2.5em;margin:0'>🇸🇾 OSINT SYRIA</h1><p style='color:#888;font-size:1.1em;margin-top:5px'>منصة استخبارات مصادر مفتوحة وإنذار مبكر — AETHON Platform</p></div>", unsafe_allow_html=True)

# === Sidebar ===
with st.sidebar:
    st.markdown("## ⚙️ لوحة التحكم")
    st.markdown("---")
    hours = st.select_slider("الوقت", options=[6, 12, 24, 48, 72, 168], value=24, format_func=lambda x: f"آخر {x} ساعة")
    threat_filter = st.multiselect("مستوى الخطورة", ["critical", "high", "medium", "low"], default=["critical", "high", "medium", "low"])
    st.markdown("---")
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown(f"<p style='color:#888;font-size:0.85em'>آخر تحديث: {datetime.utcnow().strftime('%H:%M UTC')}</p>", unsafe_allow_html=True)

# === Load & Filter ===
df = normalize(load_events(hours))
if not df.empty and "threat_level" in df.columns:
    df = df[df["threat_level"].isin(threat_filter)]

# === Metrics ===
c1, c2, c3, c4, c5 = st.columns(5)
total = len(df)
critical = int((df["threat_level"] == "critical").sum()) if "threat_level" in df.columns else 0
high = int((df["threat_level"] == "high").sum()) if "threat_level" in df.columns else 0
avg_conf = float(df["confidence"].mean()) if "confidence" in df.columns else 0
gov_count = int(df["governorate"].nunique()) if "governorate" in df.columns else 0
c1.metric("📨 إجمالي الأحداث", total)
c2.metric("🔴 حرجة", critical)
c3.metric("🟠 عالية", high)
c4.metric("🎯 متوسط الثقة", f"{avg_conf:.0%}")
c5.metric("🏛 المحافظات", gov_count)

st.markdown("---")

# === Map ===
st.markdown("### 🗺️ الخريطة التكتيكية الحية")
if df.empty or "latitude" not in df.columns:
    st.info("📭 لا توجد بيانات — شغّل الـ Pipeline لجمع البيانات الحية.")
else:
    mdf = df.dropna(subset=["latitude", "longitude"]).copy()
    if not mdf.empty:
        cmap = {"critical": "#ff1744", "high": "#ff9100", "medium": "#ffd600", "low": "#00e676"}
        mdf["color"] = mdf["threat_level"].map(cmap).fillna("#888")
        mdf["size"] = mdf["threat_level"].map({"critical": 40, "high": 28, "medium": 18, "low": 12}).fillna(12)
        hdata = {"location_name": True, "governorate": True, "latitude": False, "longitude": False, "size": False}
        if "summary_ar" in mdf.columns:
            hdata["summary_ar"] = True
        fig = px.scatter_geo(mdf, lat="latitude", lon="longitude", color="threat_level", size="size", color_discrete_map=cmap, hover_name="event_type" if "event_type" in mdf.columns else None, hover_data=hdata, projection="natural earth")
        fig.update_geos(center=dict(lat=34.8, lon=38.0), projection_scale=6, showcountries=True, countrycolor="#333", bgcolor="#0a0a0f", landcolor="#111827", oceancolor="#0a0a1a", showocean=True, showland=True)
        fig.update_layout(template="plotly_dark", paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f", height=500, margin=dict(l=0, r=0, t=0, b=0), legend=dict(font=dict(color="#e0e0e0"), bgcolor="rgba(17,24,39,0.8)"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 لا توجد إحداثيات")

st.markdown("---")

# === Charts ===
if not df.empty:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📊 توزيع الأحداث")
        if "event_type" in df.columns:
            vc = df["event_type"].value_counts().head(12)
            fig = px.bar(x=vc.values, y=vc.index, orientation="h", color=vc.values, color_continuous_scale="Viridis")
            fig.update_layout(template="plotly_dark", paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f", height=400, showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("### 🏛 المحافظات")
        if "governorate" in df.columns:
            gv = df["governorate"].value_counts().head(10)
            fig = px.pie(values=gv.values, names=gv.index, color_discrete_sequence=px.colors.qualitative.Dark24, hole=0.4)
            fig.update_layout(template="plotly_dark", paper_bgcolor="#0a0a0f", height=400, margin=dict(l=0, r=0, t=30, b=0), font=dict(color="#e0e0e0"))
            st.plotly_chart(fig, use_container_width=True)
    if "timestamp" in df.columns:
        st.markdown("### ⏱ خط زمني")
        tmp = df.copy()
        tmp["timestamp"] = pd.to_datetime(tmp["timestamp"], errors="coerce")
        tmp = tmp.dropna(subset=["timestamp"]).sort_values("timestamp")
        if not tmp.empty:
            fig = px.scatter(tmp, x="timestamp", y="threat_level", color="threat_level", color_discrete_map={"critical": "#ff1744", "high": "#ff9100", "medium": "#ffd600", "low": "#00e676"})
            fig.update_layout(template="plotly_dark", paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f", height=300, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📭 لا توجد بيانات كافية — شغّل الـ Pipeline.")

st.markdown("---")

# === Events Feed ===
st.markdown("### 📋 آخر الأحداث")
if df.empty:
    st.info("📭 لا توجد أحداث — شغّل الـ Pipeline لجمع البيانات الحية من تليجرام.")
else:
    for _, row in df.head(20).iterrows():
        threat = str(row.get("threat_level", "low")).lower()
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(threat, "⚪")
        css = {"critical": "tc", "high": "th", "medium": "tm", "low": "tl"}.get(threat, "tl")
        etype = row.get("event_type", "") or row.get("category", "") or "غير محدد"
        summary = row.get("summary_ar", "") or row.get("title_arabic", "") or row.get("raw_excerpt_arabic", "") or row.get("title", "") or ""
        location = row.get("location_name", "N/A") or "N/A"
        gov = row.get("governorate", "N/A") or "N/A"
        channel = row.get("source_channel", "N/A") or "N/A"
        conf = row.get("confidence", 0) or 0
        ts = row.get("timestamp", "") or row.get("created_at", "") or ""

        st.markdown(f"""
        <div class="ec" style="border-left: 4px solid {'#ff1744' if threat=='critical' else '#ff9100' if threat=='high' else '#ffd600' if threat=='medium' else '#00e676'}">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <span class="{css}">{icon} {threat.upper()}</span>
                <span style="color:#888;font-size:0.85em">{ts}</span>
            </div>
            <h4 style="margin:8px 0 4px 0;color:#fff">{etype}</h4>
            <p style="color:#ccc;margin:4px 0">{str(summary)[:200]}</p>
            <div style="color:#888;font-size:0.85em">📍 {location} | 🏛 {gov} | 📢 @{channel} | 🎯 {conf:.0%}</div>
        </div>
        """, unsafe_allow_html=True)

# Auto-refresh
st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)
