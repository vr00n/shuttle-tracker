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
csv_url = "https://raw.githubusercontent.com/vr00n/shuttle-tracker/main/routes.csv"
df = pd.read_csv(csv_url)

# Streamlit UI
st.title("Employee Shuttle Tracker")

# Fetch the last known vehicle positions
vehicle_positions = get_last_vehicle_positions(api)

# Create tabs for each unique last_stop
last_stops = df['last_stop'].unique()
tabs = st.tabs(last_stops)

for i, last_stop in enumerate(last_stops):
    with tabs[i]:
        st.subheader(f"Shuttles to {last_stop}")
        selected_routes = df[df['last_stop'] == last_stop]
        
        # Display Map
        if not selected_routes.empty:
            first_stop_lat = selected_routes.iloc[0]['stop_lat']
            first_stop_lon = selected_routes.iloc[0]['stop_lon']
            m = folium.Map(location=[first_stop_lat, first_stop_lon], zoom_start=12)

            # Add last known vehicle positions
            for vehicle_name, (vehicle_lat, vehicle_lon) in vehicle_positions.items():
                folium.Marker(
                    location=[vehicle_lat, vehicle_lon],
                    popup=f"{vehicle_name} (Last Known Position)",
                    icon=folium.Icon(color="red", icon="info-sign")
                ).add_to(m)

            # Add shuttle route stops and lines
            for route_name in selected_routes["route_name"].unique():
                route = selected_routes[selected_routes["route_name"] == route_name]
                folium.PolyLine(
                    locations=route[["stop_lat", "stop_lon"]].values.tolist() + [(route.iloc[-1]['last_stop_lat'], route.iloc[-1]['last_stop_lon'])],
                    color="blue",
                    weight=2.5,
                    opacity=1
                ).add_to(m)
                for index, row in route.iterrows():
                    icon_html = f"""
                    <div style="font-size: 10px; color: white; background-color: red; border-radius: 50%; width: 24px; height: 24px; text-align: center; line-height: 24px;">
                        {row['stop_sequence']}
                    </div>
                    """
                    folium.Marker(
                        location=[row["stop_lat"], row["stop_lon"]],
                        popup=f"Stop {row['stop_sequence']}: {row['stop_intersection']}",
                        icon=folium.DivIcon(html=icon_html)
                    ).add_to(m)
                # Add last stop marker
                folium.Marker(
                    location=[route.iloc[-1]["last_stop_lat"], route.iloc[-1]["last_stop_lon"]],
                    popup=f"Last Stop: {route.iloc[-1]['last_stop']}",
                    icon=folium.Icon(color="green", icon="flag")
                ).add_to(m)

            # Display map in Streamlit
            folium_static(m)
        else:
            st.error("No route data available.")
