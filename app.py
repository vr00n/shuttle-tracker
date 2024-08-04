import streamlit as st
import mygeotab
import pandas as pd
import folium
from streamlit_folium import folium_static

# Function to fetch the last known position of each vehicle from Geotab
def get_last_vehicle_positions(api):
    try:
        device_statuses = api.get('DeviceStatusInfo')
        vehicle_positions = {}
        for device_status in device_statuses:
            vehicle_lat = device_status.get('latitude', None)
            vehicle_lon = device_status.get('longitude', None)
            vehicle_name = device_status.get('device', {}).get('name', 'Unknown Vehicle')
            if vehicle_lat is not None and vehicle_lon is not None:
                vehicle_positions[vehicle_name] = (vehicle_lat, vehicle_lon)
        return vehicle_positions
    except Exception as e:
        st.error(f"Error fetching vehicle positions: {e}")
        return {}

# Geotab Authentication
database = 'nycsbus'
server = 'afmfe.att.com'
geotab_username = st.secrets["geotab_username"]
geotab_password = st.secrets["geotab_password"]
api = mygeotab.API(username=geotab_username, password=geotab_password, database=database, server=server)

try:
    api.authenticate()
except mygeotab.exceptions.AuthenticationException:
    st.error("Authentication failed!")
    st.stop()

# Read the CSV file from GitHub
csv_url = "https://raw.githubusercontent.com/<your-github-username>/<your-repo-name>/main/routes.csv"
df = pd.read_csv(csv_url)

# Streamlit UI
st.title("Employee Shuttle Tracker")

# Fetch the last known vehicle positions
vehicle_positions = get_last_vehicle_positions(api)

# Display Map
if not df.empty:
    first_stop_lat = df.iloc[0]['stop_lat']
    first_stop_lon = df.iloc[0]['stop_lon']
    m = folium.Map(location=[first_stop_lat, first_stop_lon], zoom_start=12)

    # Add last known vehicle positions
    for vehicle_name, (vehicle_lat, vehicle_lon) in vehicle_positions.items():
        folium.Marker(
            location=[vehicle_lat, vehicle_lon],
            popup=f"{vehicle_name} (Last Known Position)",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

    # Add shuttle route stops and lines
    for route_name in df["route_name"].unique():
        selected_route = df[df["route_name"] == route_name]
        folium.PolyLine(
            locations=selected_route[["stop_lat", "stop_lon"]].values.tolist(),
            color="blue",
            weight=2.5,
            opacity=1
        ).add_to(m)
        for index, row in selected_route.iterrows():
            folium.Marker(
                location=[row["stop_lat"], row["stop_lon"]],
                popup=f"Stop {row['stop_sequence']}: {row['stop_intersection']}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

    # Display map in Streamlit
    folium_static(m)
else:
    st.error("No route data available.")
