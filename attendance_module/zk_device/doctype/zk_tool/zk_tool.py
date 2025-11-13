# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import socket
from attendance_module.zk_device.zk_detail.base import (
    ZK, ZK_helper, ZKErrorConnection
)
from frappe.utils import (
    date_diff, add_to_date, getdate, get_time, get_datetime
)
from datetime import (
    datetime, time
)

employeeDetail=[]
class ZKTool(Document):
	@frappe.whitelist()
	def validate_filters(self):
		if(not self.company):
			frappe.msgprint("Please select company")
		if(not self.employee_list):
			frappe.msgprint("There's no employees in employee list!", title="Employee List")
			return []
		
	@frappe.whitelist()
	def get_company_details(self):
		doctype = 'ZK IP Detail'
		filters = {'enable': 1, 'company': self.company, 'log_type': self.log_type}
		fieldname = ['*']
		# SQL
		device_detail = frappe.db.get_value(doctype, filters, fieldname, as_dict=1)
		# Set values
		self.device_ip = device_detail.device_ip if(device_detail) else ""
		self.device_port = device_detail.device_port if(device_detail) else ""	
		return device_detail
	
	@frappe.whitelist()
	def get_employees(self):
		def get_conditions():
			conditions = f" and branch='{self.branch}'" if(self.branch) else ""
			conditions += f" and department='{self.department}'" if(self.department) else ""
			conditions += f" and designation='{self.designation}'" if(self.designation) else ""
			conditions += f" and employee='{self.employee}'" if(self.employee) else ""
			return conditions

		employees = frappe.db.sql(f""" select name, employee_name, attendance_device_id 
						from `tabEmployee` 
						where status in ("Active", "Left") 
							and ifnull(attendance_device_id, "")!=""
							and (ifnull(relieving_date, "")="" || relieving_date >= "{self.from_date}")
							and company = '{self.company}' {get_conditions()}""", as_dict=1)
		
		self.total_employees = len(employees)
		self.set("employee_list", [])
		
		for e in  employees:
			self.append("employee_list", 
				{'employee': e.name, 'employee_name': e.employee_name, 'attendance_device_id': e.attendance_device_id})

	@frappe.whitelist()
	def fetch_attendance(self):
		
		self.validate_filters()
		if (self.device_ip and self.device_port):
			addr_ip = socket.gethostbyname(self.device_ip)
			# if(is_zk_device_online(addr_ip, port=self.device_port, timeout=100)):
			# verify destination host availability.
			helper = ZK_helper(addr_ip, int(self.device_port))
			if(not helper.test_ping()): return {"msg": "Destination Host Unreachable!", "logs": [], "fetched": 0}
		
			zk = ZK(str(addr_ip), port=int(self.device_port), timeout=100000, password=786786, force_udp=False, ommit_ping=False)
			CONN = None
			device_ids = None
			attendance_records = None
			try:
				print('-----------before connect-----------------')
				CONN = zk.connect()
				print('-----------after connect-----------------')
				if (CONN): 
					device_ids = {d.get("attendance_device_id"): {} for d in self.employee_list}
					date_split = (self.from_date).split("-")
					print('working-zk')
					print(device_ids)
					print('----------------------------')

					attendance_records = CONN.get_attendance_json(userIds=device_ids, year=date_split[0], month=date_split[1])
					# attendance_records = CONN.get_attendance()
					print(attendance_records)
			except Exception as e:
				return {"msg": str(e), "logs": attendance_records, "fetched": 0}
			finally:
				print(CONN)
				if CONN:
					CONN.disconnect()
					return {"msg": "Attendance Fetched.", "logs": attendance_records, "fetched": 1}
				else:
					return {"msg": "Attendance not found.", "logs": attendance_records, "fetched": 0}
		else:
			return {"msg": "Please select right company and log type to 'Get Attendance'", "fetched": 0, "logs": attendance_records}

	@frappe.whitelist()
	def	mark_attendance(self, employees, logs):
		# mark_attendance_for_employees(self, employees, logs, publish_progress=True)
		frappe.enqueue(
			mark_attendance_for_employees,
			timeout=3000,
			self = self,
			employees=employees,
			logs=logs,
			publish_progress=False,
		)
		frappe.msgprint(
			_("Mark attendance creation is queued. It may take a few minutes"),
			alert=True,
			indicator="blue",
		)

def mark_attendance_for_employees(self, employees, logs, publish_progress=True):
	marked = False
	try:
		split_date = (self.from_date).split("-")
		year_month = f"{split_date[0]}-{split_date[1]}"
		for row in employees:
			row = frappe._dict(row)
			employee_log = logs[row.attendance_device_id]
			# logs.pop(row.attendance_device_id)
			if(employee_log):
				
				if(year_month in employee_log):
					mlogs = sorted(employee_log[year_month])
					filtered_dates  = []
					for date in get_dates_list(self.from_date, self.to_date):
						filtered_dates += [log for log in mlogs if(date in log)]
					for flog in sorted(filtered_dates):
						args = frappe._dict({
							"company": self.company,
							"employee": row.employee,
							"device_id": row.attendance_device_id,
							"device_ip": self.device_ip,
							"device_port": "4370",
							"attendance_date": getdate(flog),
							"log": flog,
						})
						if(frappe.db.exists("Attendance Log", args)):
						# if(frappe.db.exists("Proxy Attendance Log", args)):
							pass
						else:
							args.update({
								# "doctype": "Attendance Log",
								# "doctype": "Proxy Attendance Log",
								"log_type": self.log_type,
								"log_from": "ZK Tool",
							})
							doc = frappe.get_doc(args)
							doc.insert(ignore_permissions=True)
							frappe.db.commit()
							marked = True
		return {"marked": marked}
	except Exception as e:
		frappe.msgprint(f"{e}")
	finally:
		frappe.db.commit()  # nosemgrep
		# frappe.publish_realtime("attendance_marked_successfully", message={"marked": "marked"}, user=frappe.session.user)


def get_dates_list(from_date, to_date):
	days = date_diff(to_date, from_date) + 1
	dates_list = []
	for i in range(days):
		new_date = add_to_date(from_date, days=i)
		dates_list.append(new_date)
	return dates_list


@frappe.whitelist()
def activate_live_attendance_service():
	try:
		service_list = ["ksm_live_in.service", "ksm_live_out.service"]
		for sn in service_list:
			command = ["sudo", "systemctl", "status", sn]
			import subprocess, os
			"""
			Run a shell command and capture the output.

			:param command: Command to run as a list (e.g., ['sudo', 'systemctl', 'start', 'service_name'])
			:return: output from the command
			"""
			# Step 1: Change to the directory
			os.chdir('/lib/systemd/system/')
			print("Changed directory to /lib/systemd/system/")
			# Run the command
			output = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

			# Print the output
			print("Command Output:", output.stdout)
			return output.stdout

	except subprocess.CalledProcessError as e:
		# If there is an error, print the error message
		print("Error:", e.stderr)
		return e.stderr


@frappe.whitelist(allow_guest=True)
def activate_live_attendance_service():
	import subprocess, os
	try:
		service_list = ["live_akfp.service"]
		for sn in service_list:
			command = ["echo", "Z0ng4G?2023"," | ", "sudo -S", "systemctl", "restart", sn]
			
			"""
			Run a shell command and capture the output.

			:param command: Command to run as a list (e.g., ['sudo', 'systemctl', 'restart', 'service_name'])
			:return: output from the command
			"""
			# Step 1: Change to the directory
			os.chdir('/lib/systemd/system/')
			print("Changed directory to /lib/systemd/system/")
			# Run the command
			output = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

			# Print the output
			print("Command Output:", output.stdout)
			frappe.msgprint(f"{output.stdout}")
		# return output.stdout

	except subprocess.CalledProcessError as e:
		# If there is an error, print the error message
		print("Error:", e.stderr)
		return e.stderr

# bench --site erp.alkhidmat.com execute attendance_module.zk_device.doctype.zk_tool.zk_tool.reset_status
def reset_status():
	frappe.db.sql('''Delete From `tabAttendance Log` where log_from="Cron" and attendance_date between '2025-09-01' and '2025-09-18' ''')
# bench --site erp.alkhidmat.com execute attendance_module.zk_device.doctype.zk_tool.zk_tool.adjust_attendance_logs
def adjust_attendance_logs():
	count = 0
	error_logs = []
	
	for row in frappe.db.get_list("Proxy Attendance Log", filters={}, fields=["*"], order_by = "log", limit="2000"):
		quit_filters = {
			"employee": row.employee,
			"shift": row.shift,
			"company": row.company,
			"device_id": row.device_id,
			"device_ip": row.device_ip,
			# "device_port": row.device_port,
			"attendance_date": row.attendance_date,
			"log": row.log
		}
		try:
			logs_list =  frappe.db.get_list("Attendance Log", filters=quit_filters, fields=["name"], order_by = "log")
			count = count + 1
			print(f"count: {count}:-  attendance_date: {row.attendance_date} = employee: {row.employee}")
			if(logs_list):
				for lname in logs_list:
					frappe.db.sql(f'''Delete From `tabAttendance Log` where name="{lname.name}" ''')
				args = {
					'doctype': 'Attendance Log',
					'log_from': 'ZK Tool',
					"device_port": row.device_port
				}
				args.update(quit_filters)
				frappe.get_doc(args).insert(
					ignore_permissions=True, 
					# ignore_links=True,
					# ignore_if_duplicate=True,
					ignore_mandatory=True,
					# set_name=False,
					# set_child_names=False
				)
				frappe.db.sql(f'''Delete From `tabProxy Attendance Log` where name="{row.name}" ''')
				frappe.db.commit()
			else:
				args = {
					'doctype': 'Attendance Log',
					'log_from': 'ZK Tool',
					"device_port": row.device_port
				}
				args.update(quit_filters)
				frappe.get_doc(args).insert(
					ignore_permissions=True, 
					# ignore_links=True,
					# ignore_if_duplicate=True,
					ignore_mandatory=True,
					# set_name=False,
					# set_child_names=False
				)
					
				frappe.db.commit()

		except Exception:
			error_logs += [row.name]
	
	print('------------------------')
	print(error_logs)
# bench --site erp.alkhidmat.com execute attendance_module.zk_device.doctype.zk_tool.zk_tool.clean_attendance_logs
def clean_attendance_logs():
	# Fetch dirty records
	records = frappe.db.sql("""
		Select 
			name, employee, employee_name, attendance_date
		From 
			`tabAttendance Log`
		Where
			docstatus=0
			and attendance_date between '2025-09-01' and '2025-09-21'
			and owner='Administrator'
			and ifnull(device_ip, '')!=''
		-- limit 1
	""", as_dict=True)

	print(len(records))
	count = len(records)
	exempt_rec = []
	for rec in records:
		print(f"rows: {rec.attendance_date} {rec.employee_name}: {count}")
		count = count - 1
		try:
			doc = frappe.get_doc('Attendance Log', rec.name)
			doc.log_from = 'ZK Tool'
			doc.save(ignore_permissions=True)
			frappe.db.commit()
		except Exception:
			exempt_rec += [rec]
			continue
	print(exempt_rec)
		# doc = frappe.db.get_value('Shift Type', rec.shift, ['custom_grace_in_time','custom_grace_out_time'], as_dict=1)
		# shift_start = get_time(doc.custom_grace_in_time)
		# shift_end = get_time(doc.custom_grace_out_time)
		# # Midpoint of the shift = boundary between IN and OUT
		# shift_mid = time(
		# 	(shift_start.hour + shift_end.hour) // 2,
		# 	(shift_start.minute + shift_end.minute) // 2
		# )
		# print(f"{shift_start}, {shift_end}, {shift_mid}")
		# if not rec.custom_in_times:
		# 	continue

		# # Convert to datetime.time for comparison
		# punch_time = get_time(rec.custom_in_times)

		# # Decide IN/OUT based on midpoint
		# if punch_time <= shift_mid:
		# 	print('in')
		# 	Before midpoint → keep as IN, clear OUT
		# frappe.db.set_value("Attendance", rec.name, {
		# 	"out_time": rec.in_time,
		# 	"in_time": None
		# })
		# else:
		# 	print('out')
		# 	# After midpoint → keep as OUT, clear IN
		# 	frappe.db.set_value("Attendance", rec.name, {
		# 		"custom_in_times": None,
		# 		"custom_out_times": rec.custom_out_times
		# 	})

		# frappe.db.commit()
		# print(f"Cleaned {rec.name} ({rec.employee}) on {rec.attendance_date}")


def is_zk_device_online(ip, port=4370, timeout=5):
	"""Check if ZKTeco device is online using zk library."""
	zk = ZK(str(ip), port=int(port), timeout=timeout, password=786786, force_udp=False, ommit_ping=True)
	conn = None
	try:
		conn = zk.connect()
		# frappe.throw(f"✅ Device {ip}:{port} is ONLINE and responding to ZK commands.")
		# print(f"✅ Device {ip}:{port} is ONLINE and responding to ZK commands.")
		return True
	except ZKErrorConnection:
		frappe.throw(f"❌ Device {ip}:{port} is NOT responding to ZK protocol (unauthenticated or unreachable).")
		# print(f"❌ Device {ip}:{port} is NOT responding to ZK protocol (unauthenticated or unreachable).")
		return False
	except Exception as e:
		frappe.throw(f"⚠️ Device check failed: {e}")
		return False
	finally:
		if conn:
			# conn.disconnect()
			pass