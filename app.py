# 1. Import libraries
import streamlit as st
import pandas as pd
import numpy as np
import math
import vendors as vd  # our vendor module

# 2. Page config
st.set_page_config(page_title="DockMate", layout="wide")
st.title("🚢 DockMate - Ship Breakdown Assistance")

# 3. Load ports data (cached so baar-baar read na ho)
@st.cache_data
def load_ports():
    df = pd.read_csv('ports.csv')  # simple CSV file
    df.columns = ['port_name', 'lat', 'lon', 'country']
    return df

ports = load_ports()

# 4. Haversine distance function (geopy hatane ke liye)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# 5. Constants
PER_KM_COST = 50  # delivery cost per km

def calculate_total_cost(price, dist):
    return price + (dist * PER_KM_COST)

# 6. Sidebar for inputs
st.sidebar.header("Ship Breakdown Alert")
ship_lat = st.sidebar.number_input("Ship Latitude", value=18.9, format="%.4f")
ship_lon = st.sidebar.number_input("Ship Longitude", value=72.5, format="%.4f")
part_needed = st.sidebar.selectbox("Required Part", 
                                  ["Engine Gasket", "Fuel Pump", "Navigation Light"])

# 7. Alert button action
if st.sidebar.button("🚨 Send Breakdown Alert"):
    # Compute distance to all ports
    ports['distance_km'] = ports.apply(
        lambda row: haversine(ship_lat, ship_lon, row['lat'], row['lon']), axis=1)
    # Nearest 5 ports
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
        # Cheapest first
        results.sort(key=lambda x: x['Total Cost (₹)'])
        st.success(f"Found {len(results)} vendor options for {part_needed}.")

        # Show map with ship and ports
        map_data = pd.DataFrame({
            'lat': [ship_lat] + [r['Port Lat'] for r in results],
            'lon': [ship_lon] + [r['Port Lon'] for r in results]
        })
        st.map(map_data)

        # Display table
        display_df = pd.DataFrame(results).drop(columns=['Port Lat', 'Port Lon'])
        st.dataframe(display_df, use_container_width=True)

        # Highlight best option
        best = results[0]
        st.metric("🏆 Best Option", 
                  f"{best['Vendor']} at {best['Port']}", 
                  f"₹{best['Total Cost (₹)']}")
    else:
        st.error("No vendor found for this part in nearby ports. Try different part/location.")

else:
    # Default map showing only ship location
    st.map(pd.DataFrame({'lat': [ship_lat], 'lon': [ship_lon]}))
    st.info("Enter ship coordinates and required part, then click 'Send Alert'.")
