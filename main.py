import streamlit as st
import plotly.graph_objs as go
import requests
from collections import deque
from datetime import datetime
import time
import subprocess
import threading

# Constants
MAX_DATA_POINTS = 200
UPDATE_FREQ_SEC = 0.05  # Update every 0.05 seconds (50 ms)

# Data storage
time_data = deque(maxlen=MAX_DATA_POINTS)
accel_x = deque(maxlen=MAX_DATA_POINTS)
accel_y = deque(maxlen=MAX_DATA_POINTS)
accel_z = deque(maxlen=MAX_DATA_POINTS)
db = deque(maxlen=MAX_DATA_POINTS)

# Page Config
st.set_page_config(page_title="Live Sensor Readings", layout="wide")
st.markdown("# Live Sensor Readings")
st.markdown("Streamed from Sensor Logger")

# Fetch sensor data from Flask server
def fetch_sensor_data():
    try:
        response = requests.get("http://localhost:8000/get_data")
        if response.status_code == 200:
            data = response.json()
            # Clear and update local data storage
            time_data.clear()
            accel_x.clear()
            accel_y.clear()
            accel_z.clear()
            db.clear()
            time_data.extend([datetime.fromisoformat(t) for t in data["time"]])
            accel_x.extend(data["accel_x"])
            accel_y.extend(data["accel_y"])
            accel_z.extend(data["accel_z"])
            db.extend(data['db'])  # Ensure 'db' is included in the Flask server response
    except requests.ConnectionError:
        st.warning("Cannot connect to the Flask server. Make sure it is running.")

# Plotting function for accelerometer data
def plot_live_data():
    data = [
        go.Scatter(x=list(time_data), y=list(d), mode="lines", name=name)
        for d, name in zip([accel_x, accel_y, accel_z], ["X", "Y", "Z"])
    ]
    layout = go.Layout(
        xaxis=dict(type="date", title="Time"),
        yaxis=dict(title="Acceleration ms<sup>-2</sup>", range=[-15, 15]),
    )
    fig = go.Figure(data=data, layout=layout)
    return fig

# Plotting function for db data
def plot_db_data():
    db_fig = go.Figure(
        data=go.Scatter(x=list(time_data), y=list(db), mode="lines", name="DB"),
        layout=go.Layout(
            xaxis=dict(type="date", title="Time"),
            yaxis=dict(title="DB Values"),
        )
    )
    return db_fig

# Create placeholders for the live graphs
col1, col2 = st.columns([2, 1])
graph_placeholder = col1.empty()
db_graph_placeholder = col2.empty()

# Function to run the data collection script
def run_data_collection():
    subprocess.run(["python", 'main_dash.py'])

# Start the data collection in a separate thread
data_thread = threading.Thread(target=run_data_collection)
data_thread.start()

time.sleep(1)
# Main loop to update data in real-time
while True:
    fetch_sensor_data()  # Fetch new data from Flask server
    fig = plot_live_data()  # Create the plot with the latest accelerometer data
    db_fig = plot_db_data()  # Create the plot for db data

    # Update the plots in the placeholders
    graph_placeholder.plotly_chart(fig, use_container_width=True, key=str(time.time()))  # Update with unique key
    db_graph_placeholder.plotly_chart(db_fig, use_container_width=True, key=str(time.time() + 0.1))  # Unique key for db graph

    time.sleep(UPDATE_FREQ_SEC)  # Pause for the update frequency
