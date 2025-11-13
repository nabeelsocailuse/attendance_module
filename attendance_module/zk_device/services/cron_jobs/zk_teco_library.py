import frappe
from frappe import _
from frappe.model.document import Document
import socket
from akf_hrms.zk_device.zk_detail.base import ZK, ZK_helper
from frappe.utils import (
	date_diff, 
	add_to_date, 
	getdate, 
	get_time, 
	get_datetime
)
from datetime import datetime, time

device_ip = "10.0.7.201"
device_port = "4370"
branch = "Central Office"

# bench --site erp.alkhidmat.com execute akf_hrms.services.cron_jobs.zk_teco_library.get_proxy_attendance_logs
def get_proxy_attendance_logs():
	from_date = getdate()
	
	# Process logic
	addr_ip = socket.gethostbyname(device_ip)
	
	# verify destination host availability.
	helper = ZK_helper(addr_ip, int(device_port))
	if(not helper.test_ping()): 
		frappe.log_error(f"Destination Host Unreachable! {branch}, {device_ip}, {device_port} ")

	zk = ZK(str(addr_ip), port=int(device_port), timeout=4000000, password=0, force_udp=False, ommit_ping=False)
	CONN = None
	device_ids = None
	attendance_records = None

	try:
		CONN = zk.connect()
		if (CONN): 
			employee_list = get_employee_list(branch, from_date)
			device_ids = {d.get("device_id"): {} for d in employee_list}
			date_split = str(from_date).split("-")
			# print('working-zk')
			attendance_records = CONN.get_attendance_json(userIds=device_ids, year=date_split[0], month=date_split[1])
			# print(attendance_records)
			# attendance_records = CONN.get_attendance()
			mark_proxy_attendance_logs(from_date, employee_list, attendance_records)
			# data_cleaning_of_proxy_attendance_logs()
	except Exception as e:
		frappe.log_error(f"{e}")
	finally:
		# print(CONN)
		if CONN:
			CONN.disconnect()
			# return {"msg": "Attendance Fetched.", "logs": attendance_records, "fetched": 1}
		else:
			frappe.log_error("Attendance not found.")

def get_employee_list(branch, from_date):
	return frappe.db.sql(f""" 
				Select 
			 		company, (name) as employee, employee_name, (attendance_device_id) as device_id
				From 
					`tabEmployee` 
				Where
					status in ("Active", "Left") 
					and ifnull(attendance_device_id, "")!=""
					and (ifnull(relieving_date, "")="" || relieving_date >= "{from_date}")
					and branch = '{branch}' """,
	 		as_dict=1)


def mark_proxy_attendance_logs(from_date, employee_list, logs):
	try:
		delete_proxy_attendance_log()
		# from_date = getdate()
		# employee_list = get_employee_list(branch, from_date)

		split_date = str(from_date).split("-")
		year_month = f"{split_date[0]}-{split_date[1]}"
		
		attendance_logs = get_attendance_logs(from_date)
		for row in employee_list:
			row = frappe._dict(row)
			employee_log = logs[row.device_id] if(row.device_id in logs) else []
			
			if(employee_log):
				if(year_month in employee_log):
					machine_logs = sorted(employee_log[year_month])
					
					for flog in machine_logs:
						flog = get_datetime(flog)
						# print(f"{type(flog)} {flog} {flog not in attendance_logs}")
						if(flog not in attendance_logs):
							# print('------------------')
							row.update({
								"doctype": "Proxy Attendance Log",
								"device_ip": device_ip,
								"device_port": device_port,
								"attendance_date": getdate(flog),
								"log": flog,
								"log_from": "Cron",
							})
							
							doc = frappe.get_doc(row)
							doc.insert(ignore_permissions=True)
							frappe.db.commit()
	except Exception as e:
		frappe.log_error(f"{e}")
	finally:
		frappe.db.commit()

# bench --site erp.alkhidmat.com execute akf_hrms.services.cron_jobs.zk_teco_library.delete_proxy_attendance_log
def delete_proxy_attendance_log(remove_list=None):
	if(remove_list):
		frappe.db.sql(f"Delete From `tabProxy Attendance Log` Where name in ({remove_list}) ")
	else:
		frappe.db.sql("Delete From `tabProxy Attendance Log`")


def get_attendance_logs(from_date):
	attendance_logs = frappe.db.sql(f"""
		Select name, employee, log 
		From `tabAttendance Log` 
		Where 
			ifnull(device_ip, '')!=''
			and year(attendance_date) = year('{from_date}') 
			and month(attendance_date) = month('{from_date}') 
			""", as_dict=1)
	
	logs = [row.log for row in attendance_logs]
	
	return logs

# bench --site erp.alkhidmat.com execute akf_hrms.services.cron_jobs.zk_teco_library.data_cleaning_of_proxy_attendance_logs
def data_cleaning_of_proxy_attendance_logs():
	proxy_attendance_logs = frappe.db.sql('''
		Select name, employee, log, device_id
		From `tabProxy Attendance Log` e

		Where 
		year(attendance_date) = year(curdate())
		and month(attendance_date) = month(curdate())
	
	''', as_dict=1)

	attendance_logs = frappe.db.sql("""
		Select name, employee, log 
		From `tabAttendance Log` 
		Where 
			ifnull(device_ip, '')!=''
			and year(attendance_date) = year(curdate()) 
			and month(attendance_date) = month(curdate()) 
			""", as_dict=1)
	
	logs = [row.log for row in attendance_logs]

	count = 1
	unique = []
	
	for row in proxy_attendance_logs:
		if(row.log not in logs):
			unique.append(row.name)
	
	if(unique):
		inlist = ','.join(f'"{item}"' for item in unique)	
		clean_proxy_attendance_logs = frappe.db.sql(f'''
		Delete
		From `tabProxy Attendance Log`

		Where name not in ({inlist})
		
		''')
	else:
		frappe.db.sql(f'''
			Delete From `tabProxy Attendance Log` 
		''')

# bench --site erp.alkhidmat.com execute akf_hrms.services.cron_jobs.zk_teco_library.mark_attendance_of_missiong_logs
def mark_attendance_of_missiong_logs():
	try:
		cleaned_proxy_attendance_logs = frappe.db.sql('''
			Select 
				company, employee, shift, device_id, device_ip, device_port, log_from, attendance_date, log 
			From 
				`tabProxy Attendance Log` e
			Where 
				year(attendance_date) = year(curdate())
				and month(attendance_date) = month(curdate())

		''', as_dict=1)
		exception_free_records = []
		for args in cleaned_proxy_attendance_logs:
			try:
				args.update({
					"doctype": "Attendance Log"
				})
				doc = frappe.get_doc(args)
				doc.insert(ignore_permissions=True)
				frappe.db.commit()
				exception_free_records.append(args.name)
			except Exception as e:
				continue
				# frappe.log_error(f"{e}")
		remove_list = ','.join(f'"{item}"' for item in exception_free_records)
		if(exception_free_records):
			delete_proxy_attendance_log(remove_list)
	
	except Exception as e:
		frappe.log_error(f"{e}")
	finally:
		frappe.db.commit()
		