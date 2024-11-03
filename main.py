import pandas as pd
import streamlit as st
import plotly.graph_objs as go
import requests
from collections import deque
from datetime import datetime
import time
import subprocess
import threading

# Constants
MAX_DATA_POINTS = 500
UPDATE_FREQ_SEC = 0.1  # Update every 0.1 seconds

# Data storage
time_data = deque(maxlen=MAX_DATA_POINTS)
accel_x = deque(maxlen=MAX_DATA_POINTS)
accel_y = deque(maxlen=MAX_DATA_POINTS)
accel_z = deque(maxlen=MAX_DATA_POINTS)
db = deque(maxlen=MAX_DATA_POINTS)

# Page Config
st.set_page_config(page_title="Live Sensor Readings", layout="wide")
st.markdown("# Live Sensor Readings")

# Initialize session state to store all data if it doesn't already exist
if 'activity_df' not in st.session_state:
    st.session_state['activity_df'] = pd.DataFrame(columns=['time', 'accel_x', 'accel_y', 'accel_z', 'db'])
if 'stop' not in st.session_state:
    st.session_state['stop'] = False

# Fetch sensor data from Flask server
def fetch_sensor_data():
    try:
        response = requests.get("http://localhost:8000/get_data")
        if response.status_code == 200:
            data = response.json()
            time_data.clear()
            accel_x.clear()
            accel_y.clear()
            accel_z.clear()
            db.clear()
            time_data.extend([datetime.fromisoformat(t) for t in data["time"]])
            accel_x.extend(data["accel_x"])
            accel_y.extend(data["accel_y"])
            accel_z.extend(data["accel_z"])
            db.extend(data['db'])

            # Check that all arrays have the same length
            if len(time_data) == len(accel_x) == len(accel_y) == len(accel_z):
                # Append new data to session_state DataFrame
                new_data = pd.DataFrame({
                    'time': list(time_data),
                    'accel_x': list(accel_x),
                    'accel_y': list(accel_y),
                    'accel_z': list(accel_z),
                    # 'db': list(db)
                })
                st.session_state['activity_df'] = pd.concat([st.session_state['activity_df'], new_data], ignore_index=True)
            else:
                st.warning("Data arrays are of unequal length; skipping this update.")
    except requests.ConnectionError:
        st.warning("Cannot connect to the Flask server. Make sure it is running.")

# Plotting functions
def plot_live_data():
    data = [
        go.Scatter(
            x=list(time_data),
            y=list(d),
            mode="lines",
            name=name,
            line=dict(width=3, color=color)
        )
        for d, name, color in zip([accel_x, accel_y, accel_z], ["X", "Y", "Z"], ['#A51C30', '#2066A8', '#5E4C54'])
    ]
    layout = go.Layout(
        xaxis=dict(type="date", title="Time", title_font=dict(size=18), tickfont=dict(size=14)),
        yaxis=dict(title="Acceleration ms<sup>-2</sup>", title_font=dict(size=18), tickfont=dict(size=16),
                   range=[-5, 5]),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return go.Figure(data=data, layout=layout)

def plot_db_data():
    db_fig = go.Figure(
        data=go.Scatter(
            x=list(time_data),
            y=list(db),
            mode="lines",
            name="DB",
            line=dict(width=3, color='black')
        ),
        layout=go.Layout(
            xaxis=dict(type="date", title="Time", title_font=dict(size=18), tickfont=dict(size=14)),
            yaxis=dict(title="DB Values", title_font=dict(size=18), tickfont=dict(size=14)),
            margin=dict(l=40, r=40, t=40, b=40)
        )
    )
    db_fig.add_shape(
        type="line", x0=min(time_data), x1=max(time_data), y0=-5, y1=-5,
        line=dict(color="red", width=2, dash="dash")
    )
    return db_fig

# Display placeholders
col1, col2 = st.columns([1, 1])
graph_placeholder = col1.empty()
db_graph_placeholder = col2.empty()

# Function to run data collection
def run_data_collection():
    subprocess.run(["python", 'main_dash.py'])

data_thread = threading.Thread(target=run_data_collection)
data_thread.start()

# "Start" and "Stop" Buttons
if st.button("Stop Data Collection"):
    st.session_state['stop'] = True

time.sleep(1)
while not st.session_state['stop']:
    fetch_sensor_data()  # Fetch new data
    fig = plot_live_data()
    db_fig = plot_db_data()

    # Update the plots
    graph_placeholder.plotly_chart(fig, use_container_width=True, key=str(time.time()))
    db_graph_placeholder.plotly_chart(db_fig, use_container_width=True, key=str(time.time() + 0.1))

    time.sleep(UPDATE_FREQ_SEC)

@st.cache_data
def convert_df(df):
    return df.to_csv().encode("utf-8")

# Display download button after stopping
if st.session_state['stop']:
    csv = convert_df(st.session_state['activity_df'])
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name="activity_data.csv",
        mime="text/csv",
    )
