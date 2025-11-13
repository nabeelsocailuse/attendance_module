
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, get_datetime

@frappe.whitelist(allow_guest=True)
def create_attendance_log(**kwargs):
	kwargs = frappe._dict(kwargs)
	frappe.enqueue(
			_insert_attedance_log,
			timeout=300,
			kwargs = kwargs,
			publish_progress=False,
			user= "Guest"
		)
	# _insert_attedance_log(kwargs)

def _insert_attedance_log(kwargs, publish_progress=True):
	try:
		args = frappe._dict({
			"doctype": "Attendance Log",
			"device_id": kwargs['device_id'],
			"device_ip": kwargs["device_ip"],
			"device_port": kwargs["device_port"],
			"attendance_date": getdate(kwargs['attendance_date']),
			"log": get_datetime(kwargs['log'])
		})
		args = set_employee_and_shift_type(args)
		frappe.get_doc(args).save(ignore_permissions=True)
		# frappe.db.commit()

	except frappe.DoesNotExistError as e:
		frappe.log_error(f"Employee not found {args.device_id}:{args.device_port} : {str(e)}", "Attendance Error (_insert_attedance_log)")
	except Exception as e:
		frappe.log_error(f"Error in {args.device_id}:{args.device_port} : {str(e)}", "Attendance Error (_insert_attedance_log)")

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
	if(not result)
		raise frappe.DoesNotExistError(f"Item with code {item_code} not found!")
	
	for d in result:
		args.update({
			"employee":  d.name,
			"shift": d.shift_type
		})
	
	return args

""" 
from __future__ import unicode_literals
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
	args = {'id': 1, 'name': 'nabeel'}

	# Convert args to JSON string
	args_json = json.dumps(args)
 
	command = ["bench", "--site", "erp.alkhidmat.org", 
			"execute", "akf_hrms.services.live_capture.biometric_attendance.create_akfp.checkParams",
			"--kwargs", args_json  # Use --kwargs to pass JSON-formatted arguments
			]
	# Run the command
	output = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	# Print the output
	print("Command Output:", output.stdout)

def checkParams(**kwargs):
	print(type(kwargs))
"""

# bench --site erp.alkhidmat.org execute akf_hrms.services.live_capture.biometric_attendance.create_akfp.test_jobs_in_background