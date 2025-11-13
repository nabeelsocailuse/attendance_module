# service path /usr/lib/systemd/system/itc_logistics_in.service
from zk import ZK
# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Vriables
'''
    Branch Name: Regional Office Sindh
    IP:          175.107.222.80
    Port:        4370
'''
conn = None
device_ip = "175.107.222.80"
device_port=4370
#########

# create ZK instance
zk = ZK(device_ip, port=device_port, timeout=5000, password=0, force_udp=False, ommit_ping=False)
try:
	# print(f"zk: {zk}")
	conn = zk.connect()
	# print(f"conn: {conn}")
	for attendance in conn.live_capture():
		if attendance is None:
			print("empty")
		else:
			print (attendance) # Attendance object
			attendanceSplit = str(attendance).split()
			device_id = attendanceSplit[1]
			device_date = str(attendanceSplit[3])
			device_time = str(attendanceSplit[4])
			args = {
				"device_id": device_id,
				"device_ip": device_ip, 
				"device_port": device_port,
				"attendance_date": device_date,
				"log": device_date + " " + device_time
			}
			
			import subprocess, os, json
   
			os.chdir('/home/ubuntu/frappe-alkhidmat/')

			# Convert args to JSON string
			args_json = json.dumps(args)
		
			command = ["bench", "--site", "erp.alkhidmat.org", 
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

