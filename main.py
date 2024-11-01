import streamlit as st
import plotly.graph_objs as go
import requests
from collections import deque
from datetime import datetime
import time
import subprocess
import threading

# Constants
MAX_DATA_POINTS = 50
UPDATE_FREQ_SEC = 0.1  # Update every 0.05 seconds (50 ms)

# Data storage
time_data = deque(maxlen=MAX_DATA_POINTS)
accel_x = deque(maxlen=MAX_DATA_POINTS)
accel_y = deque(maxlen=MAX_DATA_POINTS)
accel_z = deque(maxlen=MAX_DATA_POINTS)
db = deque(maxlen=MAX_DATA_POINTS)

# Page Config
st.set_page_config(page_title="Live Sensor Readings",
				   layout="wide"
				   )
st.markdown("# Live Sensor Readings")
# st.markdown("Streamed from Sensor Logger")

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


# Define the new specified colors for the acceleration plots
accel_colors = ['#A51C30', '#2066A8', '#5E4C54']  # Red, Blue, Dark Gray


# Plotting function for live data
def plot_live_data():
	data = [
		go.Scatter(
			x=list(time_data),
			y=list(d),
			mode="lines",
			name=name,
			line=dict(width=3, color=color)  # Set line width and color
		)
		for d, name, color in zip([accel_x, accel_y, accel_z], ["X", "Y", "Z"], accel_colors)
	]
	layout = go.Layout(
		xaxis=dict(
			type="date",
			title="Time",
			title_font=dict(size=18),  # Increase font size for x-axis title
			tickfont=dict(size=14),  # Increase font size for x-axis ticks
		),
		yaxis=dict(
			title="Acceleration ms<sup>-2</sup>",
			title_font=dict(size=18),  # Increase font size for y-axis title
			tickfont=dict(size=16),  # Increase font size for y-axis ticks
			range=[-5, 5],
		),
		margin=dict(l=40, r=40, t=40, b=40),  # Increase margins if needed
	)
	fig = go.Figure(data=data, layout=layout)
	return fig


# Plotting function for db data
def plot_db_data():
	db_fig = go.Figure(
		data=go.Scatter(
			x=list(time_data),
			y=list(db),
			mode="lines",
			name="DB",
			line=dict(width=3, color='black')  # Set DB line color to black
		),
		layout=go.Layout(
			xaxis=dict(
				type="date",
				title="Time",
				title_font=dict(size=18),  # Increase font size for x-axis title
				tickfont=dict(size=14),  # Increase font size for x-axis ticks
			),
			yaxis=dict(
				title="DB Values",
				title_font=dict(size=18),  # Increase font size for y-axis title
				tickfont=dict(size=14),  # Increase font size for y-axis ticks
			),
			margin=dict(l=40, r=40, t=40, b=40),  # Increase margins if needed
		)
	)

	# Adding a dashed red line at -5 dB
	db_fig.add_shape(
		type="line",
		x0=min(time_data),  # Start of the line
		x1=max(time_data),  # End of the line
		y0=-5,  # Y-coordinate of the line
		y1=-5,
		line=dict(
			color="red",
			width=2,
			dash="dash"  # Dashed line
		),
	)

	return db_fig

# Create placeholders for the live graphs
col1, col2 = st.columns([1, 1])
col1_container, col2_container = col1.container(border=True), col2.container(border=True)
graph_placeholder = col1_container.empty()
db_graph_placeholder = col2_container.empty()

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
