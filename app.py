import os
import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import folium
import polyline
import streamlit.components.v1 as components
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# PAGE CONFIG — must be first Streamlit call
# ============================================================
st.set_page_config(
    page_title="LitroPH — Fuel Efficiency Route Optimizer",
    page_icon="litroph_icon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# GLOBAL CSS — dark theme, amber accents, monospace data
# ============================================================
st.markdown("""
<style>
  /* ── Base ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] {
    background-color: #0A0F1E;
    color: #E8EAF0;
    font-family: 'Inter', sans-serif;
  }

  .stApp { background-color: #0A0F1E; }

  /* ── Hide Streamlit chrome ── */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 0 2rem 4rem 2rem; max-width: 1400px; }

  /* ── Ticker bar ── */
  .ticker-bar {
    background: linear-gradient(90deg, #0D1326 0%, #111827 100%);
    border-bottom: 1px solid #F5A623;
    padding: 0.5rem 2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #94A3B8;
    display: flex;
    gap: 2.5rem;
    overflow-x: auto;
    white-space: nowrap;
    margin: 0 -2rem 0 -2rem;
  }
  .ticker-item { display: flex; align-items: center; gap: 0.4rem; }
  .ticker-label { color: #64748B; letter-spacing: 0.05em; text-transform: uppercase; font-size: 0.68rem; }
  .ticker-value { color: #F5A623; font-weight: 500; }
  .ticker-down { color: #10B981; }
  .ticker-up { color: #EF4444; }

  /* ── Hero ── */
  .hero {
    padding: 3rem 0 1.5rem 0;
    border-bottom: 1px solid #1E2A40;
    margin-bottom: 2rem;
  }
  .hero-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    color: #F5A623;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
  }
  .hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    line-height: 1.1;
    color: #F1F5F9;
    margin-bottom: 0.75rem;
    letter-spacing: -0.02em;
  }
  .hero-title span { color: #F5A623; }
  .hero-subtitle {
    font-size: 1rem;
    color: #64748B;
    font-weight: 400;
    max-width: 560px;
    line-height: 1.6;
  }

  /* ── Section headers ── */
  .section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 2.5rem 0 1.25rem 0;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #1E2A40;
  }
  .section-icon { font-size: 1.2rem; }
  .section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #F1F5F9;
    letter-spacing: 0.02em;
    text-transform: uppercase;
  }
  .section-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    background: #1E2A40;
    color: #F5A623;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    letter-spacing: 0.08em;
  }

  /* ── Cards ── */
  .card {
    background: #111827;
    border: 1px solid #1E2A40;
    border-radius: 8px;
    padding: 1.25rem;
  }
  .card-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    color: #475569;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
  }
  .card-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 500;
    color: #F5A623;
  }
  .card-sub {
    font-size: 0.72rem;
    color: #475569;
    margin-top: 0.2rem;
  }

  /* ── Route result cards ── */
  .route-recommended {
    background: linear-gradient(135deg, #0A1F12 0%, #111827 100%);
    border: 1px solid #10B981;
    border-radius: 8px;
    padding: 1.25rem;
  }
  .route-option {
    background: #111827;
    border: 1px solid #1E2A40;
    border-radius: 8px;
    padding: 1.25rem;
  }
  .route-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
  }
  .route-cost {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    line-height: 1;
  }
  .route-meta {
    font-size: 0.75rem;
    color: #64748B;
    margin-top: 0.4rem;
  }

  /* ── Streamlit widget overrides ── */
  div[data-testid="stTextInput"] input,
  div[data-testid="stNumberInput"] input,
  div[data-testid="stSelectbox"] select {
    background-color: #111827 !important;
    border: 1px solid #1E2A40 !important;
    color: #F1F5F9 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
  }
  div[data-testid="stTextInput"] input:focus,
  div[data-testid="stNumberInput"] input:focus {
    border-color: #F5A623 !important;
    box-shadow: 0 0 0 2px rgba(245, 166, 35, 0.15) !important;
  }
  label[data-testid="stWidgetLabel"] {
    color: #94A3B8 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
  }
  .stButton > button {
    background: #F5A623 !important;
    color: #0A0F1E !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 0.65rem 1.5rem !important;
    width: 100% !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.15s !important;
  }
  .stButton > button:hover { opacity: 0.88 !important; }

  /* ── Metric overrides ── */
  div[data-testid="stMetric"] {
    background: #111827;
    border: 1px solid #1E2A40;
    border-radius: 8px;
    padding: 1rem;
  }
  div[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    color: #F5A623 !important;
  }
  div[data-testid="stMetricLabel"] { color: #64748B !important; font-size: 0.75rem !important; }

  /* ── Alert boxes ── */
  div[data-testid="stAlert"] {
    background: #111827 !important;
    border-radius: 6px !important;
  }

  /* ── Divider ── */
  .divider {
    height: 1px;
    background: #1E2A40;
    margin: 2rem 0;
  }

  /* ── Map responsive height ── */
  iframe {
    min-height: 280px;
  }
  @media (min-width: 768px) {
    iframe {
      min-height: 380px;
    }
  }
    margin-top: 4rem;
    padding-top: 1.5rem;
    border-top: 1px solid #1E2A40;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #334155;
    text-align: center;
    letter-spacing: 0.05em;
  }
</style>
""", unsafe_allow_html=True)


# ============================================================
# DATABASE CONNECTION
# ============================================================
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )

@st.cache_data(ttl=3600)
def get_latest_prices():
    """Fetch current week brand prices from analytical_core."""
    conn = init_connection()
    query = """
        SELECT brand, fuel_display_name, fuel_type_slug,
               price_php, price_trend, weekly_change_php, week_date
        FROM analytical_core.brand_prices_weekly
        WHERE week_date = (SELECT MAX(week_date) FROM analytical_core.brand_prices_weekly)
        ORDER BY fuel_display_name, price_php ASC
    """
    return pd.read_sql(query, conn)

@st.cache_data(ttl=3600)
def get_price_history():
    """Fetch all weekly price averages per fuel type for trend charts."""
    conn = init_connection()
    query = """
        SELECT week_date, fuel_display_name, fuel_type_slug,
               price_avg, price_min, price_max, brand_count
        FROM analytical_core.fuel_prices_weekly
        ORDER BY week_date ASC
    """
    return pd.read_sql(query, conn)

def get_brand_price(df, fuel_slug, brand):
    """Look up a specific brand's price from the loaded DataFrame."""
    match = df[(df['fuel_type_slug'] == fuel_slug) & (df['brand'] == brand)]
    if not match.empty:
        return float(match.iloc[0]['price_php'])
    return None

def get_average_price(df, fuel_slug):
    """Get national average price for a fuel type."""
    subset = df[df['fuel_type_slug'] == fuel_slug]
    if not subset.empty:
        return float(subset['price_php'].mean())
    return None


# ============================================================
# TOMTOM ROUTING
# ============================================================
def get_routes(origin_lat, origin_lon, dest_lat, dest_lon):
    """Call TomTom API and return processed route options."""
    api_key = os.getenv("TOMTOM_API_KEY")
    url = (
        f"https://api.tomtom.com/routing/1/calculateRoute/"
        f"{origin_lat},{origin_lon}:{dest_lat},{dest_lon}/json"
        f"?key={api_key}&traffic=true&departAt=now"
        f"&routeType=fastest&maxAlternatives=2"
        f"&computeTravelTimeFor=all&sectionType=traffic"
    )
    response = requests.get(url, timeout=15)
    data = response.json()

    if "routes" not in data:
        return []

    routes = []
    for route in data["routes"]:
        summary = route["summary"]
        distance_km = summary["lengthInMeters"] / 1000
        free_flow = summary.get("noTrafficTravelTimeInSeconds", summary["travelTimeInSeconds"])
        live_time = summary["travelTimeInSeconds"]
        traffic_delay = summary.get("trafficDelayInSeconds", 0)
        traffic_multiplier = min(free_flow / live_time, 1.0) if live_time > 0 else 1.0
        coords = [[p["latitude"], p["longitude"]] for p in route["legs"][0]["points"]]
        routes.append({
            "distance_km": distance_km,
            "free_flow_min": free_flow / 60,
            "live_time_min": live_time / 60,
            "traffic_delay_min": traffic_delay / 60,
            "traffic_multiplier": traffic_multiplier,
            "coords": coords,
            "sections": route.get("sections", [])
        })

    # Deduplicate and sort by cost (cost computed after fuel price known)
    seen = set()
    unique = []
    for r in routes:
        key = round(r["distance_km"], 1)
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def calculate_cost(distance_km, km_per_liter, traffic_multiplier, price_per_liter):
    actual_efficiency = km_per_liter * traffic_multiplier
    liters = distance_km / actual_efficiency
    return liters * price_per_liter, traffic_multiplier


def build_route_map(routes_with_costs, origin_lat, origin_lon, dest_lat, dest_lon,
                    origin_label, dest_label):
    """Build Folium map with color-ranked routes and traffic overlays."""
    all_pts = [pt for r in routes_with_costs for pt in r["coords"]]
    center_lat = sum(p[0] for p in all_pts) / len(all_pts)
    center_lon = sum(p[1] for p in all_pts) / len(all_pts)

    route_map = folium.Map(
        location=[center_lat, center_lon],
        tiles="CartoDB dark_matter",
        zoom_start=13
    )

    colors = ["#10B981", "#F5A623", "#EF4444"]
    weights = [7, 5, 4]
    labels = ["RECOMMENDED", "OPTION 2", "OPTION 3"]
    opacities = [0.95, 0.65, 0.55]

    for rank, route in reversed(list(enumerate(routes_with_costs[:3]))):
        label = (f"{labels[rank]}  ·  ₱{route['cost']:.2f}  ·  "
                 f"{route['distance_km']:.1f} km  ·  "
                 f"{route['live_time_min']:.0f} min")
        folium.PolyLine(
            locations=route["coords"],
            color=colors[rank],
            weight=weights[rank],
            opacity=opacities[rank],
            tooltip=label,
            z_index_offset=(3 - rank) * 100
        ).add_to(route_map)

        for section in route.get("sections", []):
            if section.get("sectionType") == "TRAFFIC" and section.get("magnitudeOfDelay", 0) >= 3:
                s, e = section["startPointIndex"], section["endPointIndex"]
                folium.PolyLine(
                    locations=route["coords"][s:e + 1],
                    color="#7F1D1D",
                    weight=4,
                    opacity=1.0,
                    dash_array="6 4",
                    tooltip=f"Traffic incident (level {section['magnitudeOfDelay']})"
                ).add_to(route_map)

    folium.Marker(
        [origin_lat, origin_lon],
        tooltip=f"START: {origin_label}",
        icon=folium.Icon(color="blue", icon="play", prefix="fa")
    ).add_to(route_map)
    folium.Marker(
        [dest_lat, dest_lon],
        tooltip=f"END: {dest_label}",
        icon=folium.Icon(color="red", icon="stop", prefix="fa")
    ).add_to(route_map)

    route_map.fit_bounds(all_pts)
    return route_map


# ============================================================
# GEOCODING (TomTom)
# ============================================================
def geocode(address):
    api_key = os.getenv("TOMTOM_API_KEY")
    url = f"https://api.tomtom.com/search/2/geocode/{requests.utils.quote(address)}.json?key={api_key}&countrySet=PH&limit=1"
    r = requests.get(url, timeout=10)
    data = r.json()
    if data.get("results"):
        pos = data["results"][0]["position"]
        return pos["lat"], pos["lon"]
    return None, None


# ============================================================
# LOAD DATA
# ============================================================
try:
    df_prices = get_latest_prices()
    df_history = get_price_history()
    data_ok = True
    latest_week = df_prices["week_date"].iloc[0].strftime("%b %d, %Y") if not df_prices.empty else "—"
except Exception as e:
    data_ok = False
    latest_week = "—"
    df_prices = pd.DataFrame()
    df_history = pd.DataFrame()


# ============================================================
# TICKER BAR
# ============================================================
if data_ok and not df_prices.empty:
    fuel_types_for_ticker = sorted(df_prices["fuel_display_name"].unique().tolist())
    ticker_html = '<div class="ticker-bar">'
    ticker_html += f'<div class="ticker-item"><span class="ticker-label">WEEK</span><span class="ticker-value">{latest_week}</span></div>'

    for ft in fuel_types_for_ticker:
        subset = df_prices[df_prices["fuel_display_name"] == ft]
        if not subset.empty:
            avg = subset["price_php"].mean()
            trend = subset.iloc[0]["price_trend"]
            arrow = "↓" if trend == "DOWN" else "↑" if trend == "UP" else "→"
            cls = "ticker-down" if trend == "DOWN" else "ticker-up" if trend == "UP" else "ticker-value"
            change = abs(float(subset.iloc[0]["weekly_change_php"])) if pd.notna(subset.iloc[0]["weekly_change_php"]) else 0
            ticker_html += (
                f'<div class="ticker-item">'
                f'<span class="ticker-label">{ft.upper()}</span>'
                f'<span class="ticker-value">₱{avg:.2f}/L</span>'
                f'<span class="{cls}">{arrow} ₱{change:.2f}</span>'
                f'</div>'
            )
    ticker_html += "</div>"
    st.markdown(ticker_html, unsafe_allow_html=True)

# ============================================================
# INJECT RESPONSIVE LAYOUT CSS
# ============================================================
st.markdown("""
<style>
/* 1. MOBILE RESPONSIVE LOGO BREAKOUT RULES */
@media (max-width: 768px) {
    .responsive-logo img {
        position: absolute !important;
        top: 15px !important;
        right: 15px !important;
        width: 100px !important;
        z-index: 999999 !important;
    }
    .hero-title {
        padding-right: 90px;
    }
}

/* 2. SPACING BETWEEN SECTIONS */
.map-spacer {
    margin-bottom: 30px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HERO
# ============================================================
col_hero, col_logo = st.columns([3, 1])
with col_hero:
    st.markdown("""
    <div class="hero">
      <div class="hero-eyebrow">⛽ LITROPH · FUEL ROUTE OPTIMIZER</div>
      <div class="hero-title">Find the cheapest route.<br><span>Save every liter.</span></div>
      <div class="hero-subtitle">
        Live Philippine pump prices meet real-time Metro Manila traffic.
        Enter your trip and see which route costs you the least in peso — down to the centavo.
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_logo:
    # Desktop layout margin push
    st.markdown("<div style='margin-top: 45px;'></div>", unsafe_allow_html=True)
    # Wrapped logo inside a div to target mobile CSS scaling rules cleanly
    st.markdown('<div class="responsive-logo">', unsafe_allow_html=True)
    st.image("litroph_logo.png", width=180)
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# SECTION 1 — ROUTE CALCULATOR
# ============================================================
st.markdown("""
<div class="section-header">
  <span class="section-icon">🗺️</span>
  <span class="section-title">Route Cost Calculator</span>
  <span class="section-badge">LIVE TRAFFIC · TOMTOM API</span>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.6], gap="large")

with col_left:
    origin_input = st.text_input("Origin", placeholder="e.g. SM North EDSA, Quezon City")
    dest_input = st.text_input("Destination", placeholder="e.g. Ayala Center, Makati")

    col_a, col_b = st.columns(2)
    with col_a:
        fuel_options = {
            "Diesel": "diesel",
            "Unleaded 91": "unleaded-91",
            "Premium 95": "prem-95",
            "Premium 97": "prem-97",
            "Prem Diesel": "prem-diesel",
            "Kerosene": "kerosene",
        }
        fuel_label = st.selectbox("Fuel type", list(fuel_options.keys()))
        fuel_slug = fuel_options[fuel_label]
    with col_b:
        brands_available = (
            sorted(df_prices[df_prices["fuel_type_slug"] == fuel_slug]["brand"].unique().tolist())
            if data_ok and not df_prices.empty else []
        )
        brand_options = ["National average"] + brands_available
        brand_choice = st.selectbox("Gas station brand", brand_options)

    km_per_liter = st.number_input(
        "Your car's fuel efficiency (km/L)",
        min_value=1.0, max_value=40.0, value=12.0, step=0.5,
        help="Check your dashboard trip computer. Most Metro Manila city cars: 8–15 km/L."
    )

    calculate_btn = st.button("⚡ Calculate Cheapest Route")

with col_right:
    if calculate_btn:
        if not origin_input or not dest_input:
            st.warning("Please enter both origin and destination.")
        else:
            with st.spinner("Fetching live traffic data from TomTom..."):
                origin_lat, origin_lon = geocode(origin_input)
                dest_lat, dest_lon = geocode(dest_input)

                if not origin_lat or not dest_lat:
                    st.error("Could not geocode one or both locations. Try a more specific address.")
                else:
                    # Get fuel price
                    if brand_choice == "National average":
                        fuel_price = get_average_price(df_prices, fuel_slug)
                        price_label = f"National avg · ₱{fuel_price:.2f}/L"
                    else:
                        fuel_price = get_brand_price(df_prices, fuel_slug, brand_choice)
                        price_label = f"{brand_choice} · ₱{fuel_price:.2f}/L"

                    if not fuel_price:
                        st.error("Price data not available for this fuel type.")
                    else:
                        routes = get_routes(origin_lat, origin_lon, dest_lat, dest_lon)

                        if not routes:
                            st.error("Could not fetch routes. Check TomTom API key.")
                        else:
                            # Compute cost per route
                            for r in routes:
                                cost, mult = calculate_cost(
                                    r["distance_km"], km_per_liter,
                                    r["traffic_multiplier"], fuel_price
                                )
                                r["cost"] = cost

                            routes.sort(key=lambda x: x["cost"])

                            # Show map
                            route_map = build_route_map(
                                routes, origin_lat, origin_lon,
                                dest_lat, dest_lon,
                                origin_input, dest_input
                            )
                            components.html(
                                route_map._repr_html_(),
                                height=500
                            )

                            # Injected a safe HTML margin right here to act as a shield, pushing the cards down
                            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                            # Show route result cards
                            st.markdown(f"<div style='font-size:0.72rem;color:#475569;font-family:JetBrains Mono,monospace;margin:0.75rem 0 0.5rem 0;letter-spacing:0.08em;'>FUEL · {price_label.upper()}</div>", unsafe_allow_html=True)

                            rank_colors = ["#10B981", "#F5A623", "#EF4444"]
                            rank_labels = ["RECOMMENDED", "OPTION 2", "OPTION 3"]
                            rank_card_class = ["route-recommended", "route-option", "route-option"]

                            result_cols = st.columns(len(routes[:3]))
                            for i, (col, route) in enumerate(zip(result_cols, routes[:3])):
                                with col:
                                    savings = routes[0]["cost"] - route["cost"] if i > 0 else None
                                    traffic_pct = int((1 - route["traffic_multiplier"]) * 100)
                                    st.markdown(f"""
                                    <div class="{rank_card_class[i]}">
                                      <div class="route-label" style="color:{rank_colors[i]};">{rank_labels[i]}</div>
                                      <div class="route-cost" style="color:{rank_colors[i]};">₱{route['cost']:.2f}</div>
                                      <div class="route-meta">
                                        {route['distance_km']:.1f} km &nbsp;·&nbsp;
                                        {route['live_time_min']:.0f} min
                                        {f'&nbsp;·&nbsp;<span style="color:#EF4444;">+{traffic_pct}% traffic</span>' if traffic_pct > 5 else ''}
                                      </div>
                                      {'<div class="route-meta" style="color:#10B981;margin-top:0.4rem;">Saves ₱' + f"{abs(savings):.2f}" + ' vs Option 1</div>' if savings is not None and savings < 0 else ''}
                                    </div>
                                    """, unsafe_allow_html=True)
    else:
        # Placeholder state
        st.markdown("""
        <div style="height:380px;background:#111827;border:1px solid #1E2A40;border-radius:8px;
             display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.75rem;">
          <div style="font-size:2.5rem;">🗺️</div>
          <div style="color:#334155;font-size:0.85rem;font-family:'JetBrains Mono',monospace;letter-spacing:0.05em;">
            ENTER A TRIP TO SEE THE MAP
          </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# SECTION 2 — CURRENT WEEK BRAND RANKING
# ============================================================
st.markdown("""
<div class="section-header">
  <span class="section-icon">📊</span>
  <span class="section-title">Brand Price Ranking</span>
  <span class="section-badge">THIS WEEK · GASWATCHPH</span>
</div>
""", unsafe_allow_html=True)

if data_ok and not df_prices.empty:
    col_fuel_select, _ = st.columns([1, 3])
    with col_fuel_select:
        chart2_fuel = st.selectbox(
            "Select fuel type",
            sorted(df_prices["fuel_display_name"].unique().tolist()),
            key="chart2_fuel"
        )

    df_chart2 = df_prices[df_prices["fuel_display_name"] == chart2_fuel].sort_values("price_php")

    if not df_chart2.empty:
        fig2 = px.bar(
            df_chart2,
            x="brand", y="price_php",
            color="price_php",
            color_continuous_scale=[[0, "#10B981"], [0.5, "#F5A623"], [1, "#EF4444"]],
            text="price_php",
            labels={"price_php": "₱ per Liter", "brand": ""},
        )
        fig2.update_traces(
            texttemplate="₱%{text:.2f}",
            textposition="outside",
            textfont=dict(family="JetBrains Mono", size=11, color="#94A3B8")
        )
        fig2.update_layout(
            paper_bgcolor="#0A0F1E",
            plot_bgcolor="#111827",
            font=dict(family="Inter", color="#94A3B8", size=12),
            coloraxis_showscale=False,
            xaxis=dict(
                showgrid=False,
                tickfont=dict(family="JetBrains Mono", size=11, color="#64748B"),
                linecolor="#1E2A40"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#1E2A40",
                tickprefix="₱",
                tickfont=dict(family="JetBrains Mono", size=11)
            ),
            margin=dict(t=20, b=20, l=10, r=10),
            height=320,
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        cheapest = df_chart2.iloc[0]
        priciest = df_chart2.iloc[-1]
        spread = float(priciest["price_php"]) - float(cheapest["price_php"])

        m1, m2, m3 = st.columns(3)
        m1.metric("Cheapest brand", cheapest["brand"], f"₱{cheapest['price_php']:.2f}/L")
        m2.metric("Most expensive", priciest["brand"], f"₱{priciest['price_php']:.2f}/L")
        m3.metric("Price spread", f"₱{spread:.2f}/L", f"{len(df_chart2)} brands tracked")
else:
    st.info("Waiting for price data. Run the Lambda ingestion function first.")


# ============================================================
# SECTION 3 — PRICE TREND HISTORY
# ============================================================
st.markdown("""
<div class="section-header">
  <span class="section-icon">📈</span>
  <span class="section-title">Historical Price Trends</span>
  <span class="section-badge">METRO MANILA · WEEKLY</span>
</div>
""", unsafe_allow_html=True)

if data_ok and not df_history.empty:
    unique_weeks = df_history["week_date"].nunique()

    if unique_weeks < 2:
        st.info(
            f"Price trend chart needs at least 2 weeks of data. "
            f"Currently loaded: {unique_weeks} week(s). "
            f"This chart will populate after the next Tuesday ingestion run."
        )
    else:
        fig1 = px.line(
            df_history,
            x="week_date", y="price_avg",
            color="fuel_display_name",
            markers=True,
            labels={
                "week_date": "Week",
                "price_avg": "Mean Price (₱/L)",
                "fuel_display_name": "Fuel Type"
            }
        )
        fig1.update_traces(line=dict(width=2), marker=dict(size=6))
        fig1.update_layout(
            paper_bgcolor="#0A0F1E",
            plot_bgcolor="#111827",
            font=dict(family="Inter", color="#94A3B8", size=12),
            legend=dict(
                bgcolor="#111827",
                bordercolor="#1E2A40",
                borderwidth=1,
                font=dict(size=11)
            ),
            xaxis=dict(
                showgrid=False,
                tickformat="%b %d",
                tickfont=dict(family="JetBrains Mono", size=11, color="#64748B"),
                linecolor="#1E2A40"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#1E2A40",
                tickprefix="₱",
                range=[60, 130],
                tickfont=dict(family="JetBrains Mono", size=11)
            ),
            hovermode="x unified",
            margin=dict(t=20, b=20, l=10, r=10),
            height=340,
        )
        fig1.update_traces(hovertemplate="₱%{y:.2f}")
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})




# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="app-footer">
  LITROPH · DATA SOURCED FROM GASWATCHPH.COM &amp; TOMTOM API ·
  PRICES ARE REFERENCE FIGURES — ACTUAL PUMP PRICES MAY VARY ·
  BUILT BY JAMES ANDRE L. KALAW · T.I.P. QUEZON CITY
</div>
""", unsafe_allow_html=True)