
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, get_datetime

@frappe.whitelist(allow_guest=True)
def create_attendance_log(**kwargs):
	kwargs = frappe._dict(kwargs)
	_insert_attedance_log(kwargs)

def _insert_attedance_log(kwargs):
	device_id = kwargs["device_id"]
	device_ip = kwargs["device_ip"]
	device_port = kwargs["device_port"]
	attendance_date = getdate(kwargs["attendance_date"])
	log = get_datetime(kwargs["log"])
	try:
		args = frappe._dict({
			"doctype": "Attendance Log",
			"device_id": device_id,
			"device_ip": device_ip,
			"device_port": device_port,
			"attendance_date": attendance_date,	
			"log_from": "Live",
			"log": log
		})
		args = set_employee_and_shift_type(args)
		

	except frappe.DoesNotExistError as e:
		frappe.log_error(f"Employee not found {device_id}:{device_port} : {str(e)}", "Attendance Error (_insert_attedance_log)")
	except Exception as e:
		frappe.log_error(f"Error in {device_id}:{device_port} : {str(e)}", "Attendance Error (_insert_attedance_log)")


def set_employee_and_shift_type(args):
	result = frappe.db.sql(f""" 
				select 
					e.name,
					(Select shift_type from `tabShift Assignment` where docstatus=1 and status="Active" and employee=e.name order by start_date limit 1) as shift_type
				from 
					`tabEmployee` e inner join `tabZK IP Detail` zk on (e.branch=zk.branch)
				where 
					attendance_device_id='{args.device_id}' and zk.device_ip = '{args.device_ip}'
				group by 
					e.attendance_device_id
			""", as_dict=1)
	if(not result):
		frappe.log_error(f"Employee with device-id: {args.device_id}, & device_ip: {args.device_ip}. Not found in ZK IP!", "Attendance Error (_insert_attedance_log)")
		# raise frappe.DoesNotExistError(f"Employee with device-id: {args.device_id}, & device-ip: {args.device_ip}. Not found in ZK IP!")
	else:
		for d in result:
			args.update({
				"employee":  d.name,
				"shift": d.shift_type
			})
		
		if(not frappe.db.exists(args)):
			frappe.get_doc(args).insert(ignore_permissions=True)
			frappe.db.commit()
	# return args


""" from __future__ import unicode_literals
import frappe
from frappe import _
import traceback
import sys
from frappe.utils import getdate

@frappe.whitelist(allow_guest=True)
def create_attendance(**kwargs):
	kwargs = frappe._dict(kwargs)
	# api information
	args = {
		'device_id': kwargs['device_id'],
		'device_ip': kwargs['device_ip'], 
		'device_port': kwargs['device_port'],
		'attendance_date': kwargs['attendance_date'],
		'log': kwargs['log'],
		'doctype': 'Attendance Log'
	}
	frappe.get_doc(args).insert()

def changePath():
	import subprocess, os, json
	os.chdir('/home/ubuntu/frappe-alkhidmat/')
	print("Changed directory to /lib/systemd/system/")
	 # Define the args as a dictionary
	args = {
		"device_id": "811", 
		"device_ip": "10.0.7.201", 
		"device_port": 4370, 
		"attendance_date": "2025-05-29", 
		"log": "2025-05-29 15:28:01"
	}

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

def checkParams(**kwargs):
	print(kwargs)
"""
# bench --site erp.alkhidmat.org execute akf_hrms.services.live_capture.biometric_attendance.create_akfp.changePath