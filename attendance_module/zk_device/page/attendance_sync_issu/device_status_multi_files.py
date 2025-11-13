import frappe
import os
from frappe.utils import format_datetime
import json

# bench --site erp.alkhidmat.com execute akf_hrms.zk_device.page.attendance_sync_issu.device_status_multi_files.get_device_status
@frappe.whitelist()
def get_device_status(filters=None):
	"""Read last lines from the latest device log file and extract current status."""
	
	log_dir = os.path.join(frappe.get_app_path("akf_hrms"), "services", "live_capture")

	if not os.path.exists(log_dir):
		return {"status": "Log directory not found", "details": ""}

	# Find all log files matching the pattern device_log.txt*
	log_files = [
		os.path.join(log_dir, f)
		for f in os.listdir(log_dir)
		if f.startswith("device_log")
	]

	if not log_files:
		return {"status": "No log files found", "details": ""}

	# Sort by modification time (latest last)
	# log_files.sort(key=os.path.getmtime, reverse=True)

	
	# Pick the latest file
	latest_log = log_files[0]
	frappe.logger().info(f"Reading from latest log file: {latest_log}")
	# print(latest_log)
	
	error_log_list = []
	
	for log_file in log_files:
		print(log_file)	
	
		# # Read last 10 lines
		try:
			with open(log_file, "r") as f:
				lines = f.readlines()[-10:]
		except Exception as e:
			return {"status": "Error reading log", "details": str(e)}

		

		for last_line in lines:
			last_line = last_line.strip()
			if not last_line:
				continue

			# Determine status
			if "DEVICE ONLINE" in last_line:
				status, color = "Online", "green"
			elif "TRYING TO CONNECT" in last_line:
				status, color = "Connecting...", "orange"
			elif "DISCONNECT" in last_line or "ERROR" in last_line:
				status, color = "Offline / Error", "red"
			else:
				status, color = "Unknown", "gray"

			# Extract timestamp & message safely
			if "]" in last_line:
				parts = last_line.split("]", 1)
				timestamp = parts[0].strip("[]")
				message = parts[1].strip()
			else:
				timestamp = ""
				message = last_line

			args = {
				"timestamp": format_datetime(timestamp) if timestamp else "",
				"error": message,
				"status": status,
				"color": color,
				"file": os.path.basename(latest_log),
			}
			error_log_list.append(args)
			# print('-------------------')
			# print(args)
		# Sort logs newest first (by timestamp)
	error_log_list.sort(key=lambda x: x["timestamp"], reverse=True)

	# Pretty JSON string
	pretty_json = json.dumps(error_log_list, indent=4, ensure_ascii=False)

	print(pretty_json)
	return {"data": error_log_list, "file": os.path.basename(latest_log)}
