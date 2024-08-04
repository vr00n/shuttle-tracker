import streamlit as st
import mygeotab
import pandas as pd
import folium
from streamlit_folium import folium_static

# Function to fetch live position from Geotab
def get_vehicle_position(api, vehicle_id):
    try:
        device_statuses = api.get('DeviceStatusInfo', search={'deviceSearch': {'id': vehicle_id}})
        if not device_statuses:
            raise ValueError("No status data available for this vehicle.")

        device_status = device_statuses[0]
        vehicle_lat = device_status.get('latitude', None)
        vehicle_lon = device_status.get('longitude', None)
        vehicle_name = device_status.get('device', {}).get('name', 'Unknown Vehicle')

        if vehicle_lat is None or vehicle_lon is None:
            raise ValueError("Latitude or Longitude data is missing for the vehicle.")

        return vehicle_lat, vehicle_lon, vehicle_name

    except Exception as e:
        st.error(f"Error fetching vehicle position: {e}")
        return None, None, None

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

# Allow the user to select a route from a dropdown menu
route_name = st.selectbox("Select Route", df["route_name"].unique())
selected_route = df[df["route_name"] == route_name]

vehicle_id = st.text_input("Enter Vehicle ID:")
if st.button("Track Vehicle"):
    if vehicle_id:
        vehicle_lat, vehicle_lon, vehicle_name = get_vehicle_position(api, vehicle_id)
        if vehicle_lat and vehicle_lon:
            # Display Map
            m = folium.Map(location=[vehicle_lat, vehicle_lon], zoom_start=13)

            # Add vehicle position
            folium.Marker(
                location=[vehicle_lat, vehicle_lon],
                popup=f"{vehicle_name} (Current Position)",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)

            # Add shuttle route stops
            for index, row in selected_route.iterrows():
                folium.Marker(
                    location=[row["stop_lat"], row["stop_lon"]],
                    popup=f"Stop {row['stop_sequence']}: {row['stop_intersection']}",
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(m)

            # Draw route lines
            folium.PolyLine(
                locations=selected_route[["stop_lat", "stop_lon"]].values.tolist(),
                color="blue",
                weight=2.5,
                opacity=1
            ).add_to(m)

            # Display map in Streamlit
            folium_static(m)
        else:
            st.error("Could not retrieve vehicle position.")
    else:
        st.error("Please enter a valid Vehicle ID.")
