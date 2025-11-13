import frappe
import os
from frappe.utils import (
	format_datetime
)
# bench --site erp.alkhidmat.com execute akf_hrms.services.cron_jobs.device_status.get_device_status
@frappe.whitelist()
def get_device_status(filters=None):
	"""Read last lines of the device log and extract current status."""
	log_path = os.path.join(frappe.get_app_path("akf_hrms"), "services", "live_capture", "device_log.txt")
	print(log_path)
	if not os.path.exists(log_path):
	    return {"status": "Log file not found", "details": ""}

	# Read last 10 lines safely
	with open(log_path, "r") as f:
		lines = f.readlines()[-10:]
	
	error_log_list = []
	for last_line in lines:
		
		# last_line = lines[-1].strip() if lines else "No log entries found."
		# print(last_line)
		# Determine status based on text
		if "DEVICE ONLINE" in last_line:
			status = "Online"
			color = "green"
		elif "TRYING TO CONNECT" in last_line:
			status = "Connecting..."
			color = "orange"
		elif "DISCONNECT" in last_line or "ERROR" in last_line:
			status = "Offline / Error"
			color = "red"
		else:
			status = "Unknown"
			color = "gray"
		
		# Split at first closing bracket
		parts = last_line.split("]", 1)
		timestamp = parts[0].strip("[]")   # remove [ and ]
		message = parts[1].strip() # remove leading space

		error_log_list.append({
			"timestamp": format_datetime(timestamp),
			"error": message,
			"message": last_line,
			"status": status,
			"color": color,
		})
		
	# print('-------------------')
	
	# print(error_log_list)
	
	return {"data": error_log_list}
	
