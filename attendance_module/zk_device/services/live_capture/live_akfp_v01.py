# service path /usr/lib/systemd/system/itc_logistics_in.service
from zk import ZK
# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Vriables
conn = None
# 103.27.22.130
device_ip = "10.0.7.201"
device_port=4370
#########

# create ZK instance
# zk = ZK(device_ip, port=device_port, timeout=5000, password=0, force_udp=False, ommit_ping=False)
try:
	# conn = zk.connect()
	# for attendance in conn.live_capture():
	# 	if attendance is None:
	# 		print("empty")
	# 	else:
	# 		# print (attendance) # Attendance object
	# 		attendanceSplit = str(attendance).split()
	# 		device_id = attendanceSplit[1]
	# 		device_date = str(attendanceSplit[3])
	# 		device_time = str(attendanceSplit[4])
	# 		args = {
	# 			"device_id": device_id,
	# 			"device_ip": device_ip, 
	# 			"device_port": device_port,
	# 			"attendance_date": device_date,
	# 			"log": device_date + " " + device_time
	# 		}
			
	import subprocess, os, json

	os.chdir('/home/master/Frappe-alkhidmat/')
	
	args = {
		"device_id": "116",
		"device_ip": device_ip, 
		"device_port": device_port,
		"attendance_date": "2025-10-07",
		"log": "2025-10-07" + " " + "11:56:12"
	}
	# Convert args to JSON string
	args_json = json.dumps(args)

	command = ["bench", "--site", "erp.alkhidmat.com", 
			"execute", "akf_hrms.services.live_capture.biometric_attendance.create_akfp.create_attendance_log",
			"--kwargs", args_json  # Use --kwargs to pass JSON-formatted arguments
			]
	# Run the command
	output = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	# Print the output
	print("Command Output:", output.stdout)

except Exception as e:
	print ("Process terminate : {}".format(e))
finally:
	if conn:
		conn.disconnect()

""" myobj = {
    "device_id": "73",
    "device_ip": device_ip, 
    "device_port": device_port,
    "attendance_date": "2024-09-09",
    "log": "2024-09-09" + " " + "01:15:12"
}

import requests
url = 'https://erp.alkhidmat.org/api/method/akf_hrms.services.live_capture.biometric_attendance.create_akfp.create_attendance_log'

x = requests.post(url, data = myobj, verify=False)
print("post: ", x) """

