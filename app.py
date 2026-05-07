import streamlit as st
import pandas as pd
import math
import json
import threading
import websocket
import vendors as vd

# -------------------- AISstream API Key --------------------
API_KEY = "57d10e3b695f0f80099caced993ff7ed068e7f5f"  # Store carefully

# -------------------- Global Ship Location (Thread Safe) --------------------
if 'ship_location' not in st.session_state:
    st.session_state.ship_location = {"lat": 18.9, "lon": 72.5}  # Default Mumbai
if 'ws_running' not in st.session_state:
    st.session_state.ws_running = False
if 'current_mmsi' not in st.session_state:
    st.session_state.current_mmsi = None

# -------------------- WebSocket Callbacks --------------------
def on_message(ws, message):
    msg = json.loads(message)
    if msg.get("MessageType") == "PositionReport":
        pos = msg["Message"]["PositionReport"]
        lat = pos["Latitude"]
        lon = pos["Longitude"]
        # Update location in session state (accessible from Streamlit main thread)
        st.session_state.ship_location = {"lat": lat, "lon": lon}

def on_error(ws, error):
    pass  # handle silently for now

def on_close(ws, close_code, close_msg):
    st.session_state.ws_running = False

def on_open(ws, mmsi):
    """Subscribe to PositionReports for a specific MMSI."""
    sub_msg = {
        "Apikey": API_KEY,
        "BoundingBoxes": [[-90, -180], [90, 180]],  # whole world
        "FiltersShipMMSI": [mmsi],                  # only this ship
        "FilterMessageTypes": ["PositionReport"]
    }
    ws.send(json.dumps(sub_msg))
    st.session_state.ws_running = True

# -------------------- Start WebSocket Thread --------------------
def start_ws(mmsi):
    ws = websocket.WebSocketApp(
        "wss://stream.aisstream.io/v0/stream",
        on_open=lambda ws: on_open(ws, mmsi),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

# -------------------- Load ports (cached) --------------------
@st.cache_data
def load_ports():
    df = pd.read_csv('ports.csv')
    df.columns = ['port_name', 'lat', 'lon', 'country']
    return df

ports = load_ports()

# -------------------- Helper Functions --------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

PER_KM_COST = 50

def calculate_total_cost(price, dist):
    return price + (dist * PER_KM_COST)

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="DockMate", layout="wide")
st.title("🚢 DockMate - Ship Breakdown Assistance (Live Satellite AIS)")

# ---- Sidebar: AIS Tracking ----
st.sidebar.header("🛰 AIS Tracking Setup")
mmsi_input = st.sidebar.text_input("Ship MMSI (9 digits)", value="", max_chars=9)
if st.sidebar.button("Connect AIS"):
    if mmsi_input:
        # Restart WebSocket if MMSI changed or not running
        if st.session_state.current_mmsi != mmsi_input or not st.session_state.ws_running:
            st.session_state.current_mmsi = mmsi_input
            t = threading.Thread(target=start_ws, args=(mmsi_input,), daemon=True)
            t.start()
            st.sidebar.success(f"Tracking MMSI {mmsi_input}...")
    else:
        st.sidebar.error("Enter a valid 9-digit MMSI")

st.sidebar.markdown("---")
st.sidebar.header("📍 Current Ship Location")
ship_lat = st.session_state.ship_location["lat"]
ship_lon = st.session_state.ship_location["lon"]
st.sidebar.write(f"Lat: {ship_lat:.4f}, Lon: {ship_lon:.4f}")

# Manual override
override_lat = st.sidebar.number_input("Override Latitude", value=ship_lat, format="%.4f")
override_lon = st.sidebar.number_input("Override Longitude", value=ship_lon, format="%.4f")
ship_lat = override_lat
ship_lon = override_lon

st.sidebar.markdown("---")
part_needed = st.sidebar.selectbox("Required Part",
                                    ["Engine Gasket", "Fuel Pump", "Navigation Light"])

# ---- Main Action ----
if st.sidebar.button("🚨 Send Breakdown Alert"):
    # Calculate distances and vendors
    ports['distance_km'] = ports.apply(
        lambda row: haversine(ship_lat, ship_lon, row['lat'], row['lon']), axis=1)
    nearest_ports = ports.nsmallest(5, 'distance_km')

    results = []
    for _, port in nearest_ports.iterrows():
        port_name = port['port_name']
        country = port['country']
        dist = port['distance_km']
        vendor_list = vd.get_vendors_for_port(port_name, part_needed)
        for vendor in vendor_list:
            total_cost = calculate_total_cost(vendor['price'], dist)
            results.append({
                'Port': port_name,
                'Country': country,
                'Distance (km)': round(dist, 1),
                'Vendor': vendor['name'],
                'Part Price (₹)': vendor['price'],
                'Delivery Cost (₹)': round(total_cost - vendor['price'], 2),
                'Total Cost (₹)': total_cost,
                'Port Lat': port['lat'],
                'Port Lon': port['lon']
            })

    if results:
        results.sort(key=lambda x: x['Total Cost (₹)'])
        st.success(f"Found {len(results)} vendor options for {part_needed}.")

        # Map: ship + ports
        map_data = pd.DataFrame({
            'lat': [ship_lat] + [r['Port Lat'] for r in results],
            'lon': [ship_lon] + [r['Port Lon'] for r in results]
        })
        st.map(map_data)

        # Table
        display_df = pd.DataFrame(results).drop(columns=['Port Lat', 'Port Lon'])
        st.dataframe(display_df, use_container_width=True)

        # Best option
        best = results[0]
        st.metric("🏆 Best Option",
                  f"{best['Vendor']} at {best['Port']}",
                  f"₹{best['Total Cost (₹)']}")
    else:
        st.error("No vendor found for this part in nearby ports. Try different part/location.")
else:
    # Default map: show only ship
    st.map(pd.DataFrame({'lat': [ship_lat], 'lon': [ship_lon]}))
    st.info("Enter ship MMSI and click 'Connect AIS' to track live location, or manually set coordinates. Then click 'Send Alert'.")
