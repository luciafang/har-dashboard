from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# Data storage
sensor_data = {
	"time": [],
	"accel_x": [],
	"accel_y": [],
	"accel_z": [],
	"db": []
}


@app.route("/data", methods=["POST"])
def receive_data():
	if request.method == "POST":
		try:
			raw_data = request.data
			data = json.loads(raw_data)
			if 'payload' not in data:
				return jsonify({"status": "error", "message": "Payload not found"}), 400

			for d in data['payload']:
				if d.get("name", None) == "wrist motion":
					try:
						ts = datetime.fromtimestamp(d["time"] / 1e9)  # Convert nanoseconds to seconds
						if len(sensor_data["time"]) == 0 or ts > datetime.fromisoformat(sensor_data["time"][-1]):
							sensor_data["time"].append(ts.isoformat())
							sensor_data["accel_x"].append(d["values"]["accelerationX"])
							sensor_data["accel_y"].append(d["values"]["accelerationY"])
							sensor_data["accel_z"].append(d["values"]["accelerationZ"])
					except KeyError as e:
						print(f"KeyError: {e} in data entry {d}")
					except Exception as e:
						print(f"Unexpected error: {e}")
				if d.get("name", None) == "microphone":
					try:
						sensor_data["db"].append(d["values"]["dBFS"])
					except KeyError as e:
						print(f"KeyError: {e} in data entry {d}")
					except Exception as e:
						print(f"Unexpected error: {e}")
		except json.JSONDecodeError as e:
			print(f"JSON decoding error: {e}")
		except Exception as e:
			print(f"Error processing data: {e}")
	return jsonify({"status": "success"})


@app.route("/get_data", methods=["GET"])
def get_data():
	# print(f"Serving sensor data: {sensor_data}")  # Confirm data is available
	return jsonify(sensor_data)


if __name__ == "__main__":
	app.run(port=8000, host="0.0.0.0")
