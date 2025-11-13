import frappe
import socket
from akf_hrms.zk_device.zk_detail.base import ZK
from frappe.utils import getdate, date_diff, add_to_date, get_datetime

""" 4 functions are using to fetch attendance form machine. """
@frappe.whitelist()
def fetch_attendance():
	frappe.db.sql(f""" delete from `tabMachine Logs`""")
	for device in get_zk_ip_detail():
		employees = get_employees(device.company)
		if(employees):
			attendance_device_ids = {e.attendance_device_id: {} for e in employees if(e.attendance_device_id)}
			if(attendance_device_ids):
				get_attendance_from_zk_device(device, attendance_device_ids)

def get_zk_ip_detail():
	return frappe.db.sql(""" 
		Select company, device_ip, device_port
		From `tabZK IP Detail`
		Where enable = 1
			and ifnull(company, "")!=""
			and ifnull(device_ip, "")!=""
			and ifnull(device_port, "")!=""
		""", as_dict=1)

def get_employees(company):
	return frappe.db.sql(""" Select attendance_device_id
		From `tabEmployee` e
		Where
			status = 'Active' 
			and ifnull(attendance_device_id, '')!=''
			and company = '%s'
		Group by
			attendance_device_id
		"""%company, as_dict=1)

def get_attendance_from_zk_device(device, attendance_device_ids):
	device_ip = device.device_ip
	device_port = device.device_port
	print("device: ", device)
	if (device_ip and device_port):
		conn = None
		attendance_records = []
		addr_ip = socket.gethostbyname(device_ip)
		zk = ZK(str(addr_ip), port=int(device_port), timeout=3000000, password=0, force_udp=False, ommit_ping=False)
		try:
			conn = zk.connect()
			if (conn):
				# Fetch from machine
				attendance_records = conn.get_attendance_json(userIds=attendance_device_ids)
		except Exception as e:
			return e
		finally:
			if conn:
				conn.disconnect()
				frappe.get_doc({
					"doctype": "Machine Logs",
					"company": device.company,
					"device_ip": device_ip,
					"device_port": device_port,
					"json_logs": str(attendance_records),
					
				}).save()
				return "Attendance fetched." if(attendance_records) else "Attendance not found."		
	else:
		return "Please select right company and log type to 'Get Attendance' "

@frappe.whitelist()
def mark_proxy_attendance_logs():
	try:
		# frappe.db.sql(""" delete from `tabProxy Attendance Log` """)
		dates_list = get_dates_list(getdate(), getdate())
		for device in get_zk_ip_detail():
			employees = get_employees(device.company)
			mlogs = get_saved_machine_logs(device)
			logs = eval(mlogs[0][1]) if(mlogs) else {}
			if(employees):
				for emp in employees:
					multi_years= logs[emp.attendance_device_id] if(emp.attendance_device_id in logs) else None
					if(multi_years): 
						for date in dates_list:
							year = str(date).split('-')[0]
							signle_year = multi_years[year] if (year in multi_years) else []
							signle_year = sorted(list(signle_year))
							for log in signle_year:
								if (str(date) in log):
									# attendance_date = str(log).split(" ")[0]
									_log_ = get_datetime(log)
									
									args = frappe._dict({
										"doctype": "Attendance Log",
										"device_id": emp.attendance_device_id,
										"device_ip": device.device_ip,
										"device_port": device.device_port,
										"attendance_date": date,
										"log":_log_
									})
									if (not frappe.db.exists(args)):
										args.update({"doctype": "Proxy Attendance Log"})
										if (not frappe.db.exists(args)):
											frappe.get_doc(args).save(ignore_permissions=True)
						# frappe.throw('stop')
				# Delete fetched logs from machine
	except Exception as e:
		print(e)
	finally:
		print('finished.')

def get_saved_machine_logs(device):
	logs = frappe.db.sql(f"""  
			Select name, json_logs
			From `tabMachine Logs`
			Where 
				company = '{device.company}'
				and device_ip = '{device.device_ip}'
				and device_port = '{device.device_port}'
			""", as_dict=0) or {}
	
	return logs

def get_dates_list(from_date, to_date):
	days = date_diff(to_date, from_date) + 1
	dates_list = []
	for i in range(days):
		new_date = add_to_date(from_date, days=i)
		dates_list.append(new_date)
	return dates_list

	
""" 1 function used to mark attendance. """
@frappe.whitelist()
def mark_attendance():
	try:
		for d in frappe.db.sql(""" 
						Select 
							name, employee, shift, device_id, device_ip, device_port, 
							attendance_date, log, log_type
						From `tabProxy Attendance Log`
						Where ifnull(employee, "")!=""
						Order By employee, attendance_date, log
						Limit 50""", as_dict=1):
			name = d.name
			
			args = frappe._dict(d)
			args.pop("name")
			if(not frappe.db.exists("Attendance Log", args)):
				args.update({"doctype": "Attendance Log"})
				frappe.get_doc(args).insert(ignore_permissions=True)
				#
				frappe.db.sql(f""" delete from `tabProxy Attendance Log` where name = '{name}' """)
				
	except Exception as e:
		print(e)

""" Mubarrim
> implemet leave deduction, If employee come 2 hours late consective 3 or above days in a month.
 """
@frappe.whitelist()
def deduct_leave_of_2_hours():
	from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import (
		create_leave_ledger_entry,
	)
	from frappe.utils import time_diff_in_hours

@frappe.whitelist()
def reset_attendance():
	attendances = frappe.db.sql(""" select  * from `tabAttendance`
				where docstatus=1 and custom_hours_worked like "%-%" """, as_dict=1)
					# where docstatus=1 and custom_hours_worked like "%-%" """, as_dict=1)
	from frappe.utils import time_diff, get_datetime
	for d in attendances:
		hours_worked = time_diff(str(d.out_time), str(d.in_time))
		# # # hours_worked = get_time(hours_worked)
		overtime_hours = "0:00:00"
		if(hours_worked>d.custom_total_working_hours):
			overtime_hours = time_diff(str(hours_worked), str(d.custom_total_working_hours))
		# print(d.name)
		# print(d.employee)
		print(hours_worked)
		print(overtime_hours)
		late_entry = 1 if(get_datetime("%s %s"%(d.attendance_date, d.custom_start_time))<d.in_time) else 0
		early_exit = 1 if(get_datetime("%s %s"%(d.attendance_date, d.custom_end_time))>d.out_time) else 0
		print(late_entry)
		print(early_exit)
		# frappe.db.sql(f""" 
		# 	update `tabAttendance`
		# 	set in_time = '{d.out_time}', out_time='{d.in_time}'
		# 	where name = '{d.name}'
		#  """)
		
		frappe.db.sql(f""" 
					update `tabAttendance`
					set custom_hours_worked = '{hours_worked}', custom_overtime_hours='{overtime_hours}',
					late_entry = {late_entry},
					early_exit = {early_exit}
					where name = '{d.name}'
				""")