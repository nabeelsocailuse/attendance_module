# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff, getdate, get_datetime, time_diff_in_hours, get_time, datetime
from datetime import datetime	# Mubashir Bashir 25-02-2025

class AttendanceLog(Document):
	def validate(self):
		self.set_employee_and_shift_type()
		# self.process_attendance()
		if(not self.attendance_date):	# Mubashir Bashir 30-07-2025
			frappe.throw("Attendance date and time is required.")

	def set_employee_and_shift_type(self):
		if(self.shift): 
			return
		query = f""" 
				select 
					e.name,
					(Select shift_type from `tabShift Assignment` where docstatus=1 and status="Active" and employee=e.name order by start_date limit 1) as shift_type
				from `tabEmployee` e inner join `tabZK IP Detail` zk on (e.branch=zk.branch)
				where attendance_device_id='{self.device_id}' and zk.device_ip = '{self.device_ip}'
				group by e.attendance_device_id
				"""
		for d in frappe.db.sql(query, as_dict=1):
			self.employee = d.name
			self.shift = d.shift_type
			
	def after_insert(self):
		self.process_attendance()

	def process_attendance(self):
		attendance = self.get_attendance()
		
		if (attendance):
			self.update_attendance(attendance)
		else:
			self.create_attendance()

	def get_attendance(self):
		
		attendance = frappe.db.sql(f'''
			Select 
				name, status, shift, in_time, out_time
			From 
   				`tabAttendance`
			Where 
				docstatus=1
				and employee="{self.employee}"
				and attendance_date = "{self.attendance_date}"
		''', as_dict=1)
		args = frappe._dict()
		
		for att in attendance:
			args.update(att)
		
		return args

	def update_attendance(self, attendance):
		# frappe.throw(f"{attendance}")
		if(attendance.status!="Present"): 
			return	

		shift_start_time = None
		shift_end_time = None
		mid_shift = None
		if(self.shift):
			doc = frappe.get_doc("Shift Type", self.shift)
			shift_start_time = get_datetime("%s %s"%(self.attendance_date, doc.start_time))
			shift_end_time =get_datetime("%s %s"%(self.attendance_date, doc.end_time))
			if(doc.enable_auto_attendance):
				if(doc.custom_grace_in_time):
					shift_start_time = get_datetime("%s %s"%(self.attendance_date, doc.custom_grace_in_time))
				if(doc.custom_grace_out_time):
					shift_end_time = get_datetime("%s %s"%(self.attendance_date, doc.custom_grace_out_time))
			mid_shift = shift_start_time + (shift_end_time - shift_start_time) / 2		

			frappe.db.set_value("Attendance", attendance.name, {
	   			"shift": doc.name, 
		  		"custom_start_time": doc.start_time, 
				"custom_end_time": doc.end_time,
			 	
			})
		in_time = get_datetime(attendance.in_time) if(attendance.in_time) else None
		out_time = get_datetime(attendance.out_time) if(attendance.out_time) else None
		
		new_log = get_datetime(self.log)
		UPDATE_LOG = True
		# case#1 when in-time is empty
		if(not in_time):
			if(out_time<new_log):
				in_time = out_time
				out_time = new_log
			else:
				in_time = new_log
		# case#2 when out-time is empty
		elif(not out_time):
			if(in_time<new_log):
				out_time = new_log
			else:
				in_time = new_log
				out_time = in_time
		# case#3 when both (in/out) time are available
		elif(in_time and out_time):
			# case#3.1 when new_log between in/out. then do nothing
			if(new_log<in_time):
				in_time = new_log
			# case#3.2 when (new_log>out) time 
			elif(new_log>out_time):
				out_time = new_log

			# case#3.3 when (out<new_log) time
			if(in_time>out_time):
				in_time = out_time
				out_time = in_time
				# case#3.4 when new_log between in/out. then do nothing		
				if(new_log>in_time and new_log<out_time):
					UPDATE_LOG = False
			else:
				# case#3.5 when new_log between in/out. then do nothing	
				if(new_log>in_time and new_log<out_time):
					UPDATE_LOG = False
			
				
		if(in_time == out_time):
			if(shift_start_time and shift_end_time and mid_shift):
				if (new_log <= mid_shift):
					out_time = None				
				else:				
					in_time = None
			UPDATE_LOG = True
		# elif(getdate(in_time)!=getdate(out_time)):
		# 	if(shift_start_time and shift_end_time and mid_shift):
		# 		if (new_log <= mid_shift):
		# 			out_time = None				
		# 		else:				
		# 			in_time = None
		if(in_time and shift_start_time):
			if(in_time>shift_start_time):
				frappe.db.set_value("Attendance", attendance.name, "late_entry", self.late_entry(out_time))
		if(out_time and shift_end_time):
			if(out_time<shift_end_time):
				frappe.db.set_value("Attendance", attendance.name, "early_exit", self.early_exit(out_time))
		if(not in_time):
			frappe.db.set_value("Attendance", attendance.name, {
				"custom_hours_worked": "",
				"custom_overtime_hours": ""
			})
		if(not out_time):
			frappe.db.set_value("Attendance", attendance.name, {
				"custom_hours_worked": "",
				"custom_overtime_hours": ""
			})
		# frappe.throw(f"shift_start: {in_time} shift_end: {out_time}")
		if(UPDATE_LOG):
			hours_worked = self.cal_hours_worked(in_time, out_time) if(in_time and out_time) else None
			overtime_hours = self.cal_overtime_hours(hours_worked) if(hours_worked) else None
			
			if("." in str(hours_worked)): 
				hours_worked = str(hours_worked).split(".")[0]
			if("." in str(overtime_hours)): 
				overtime_hours = str(overtime_hours).split(".")[0]

			frappe.db.set_value("Attendance", attendance.name, {
	   			"in_time": in_time, 
		  		"custom_in_times": in_time, 
				"out_time": out_time, 
			 	"custom_out_times": out_time,
				"custom_hours_worked": hours_worked,
				"custom_overtime_hours": overtime_hours,
				"early_exit": self.early_exit(out_time)
			})
			
	
	def cal_hours_worked(self, in_time, out_time):
		# frappe.msgprint(f"{self.log} {in_time}")
		return time_diff(str(out_time), str(in_time))

	# Mubashir Bashir 25-02-2025 Start 
	def create_attendance(self):
		# print(f'-> {self.employee} {self.device_id}')
		attendance_date = getdate(self.attendance_date)
		# log_time = datetime.combine(today, get_time(self.log))
		log_time = get_datetime(self.log)

		late_entry = False
		early_exit = False
		custom_out_times = ""
		custom_in_times = ""
		shift_start_time = None
		shift_end_time = None
		if self.shift:

			shift_details = frappe.get_value("Shift Type", self.shift, ["start_time", "end_time"], as_dict=True)
			if not shift_details:
				frappe.throw("Shift details not found for the selected shift.")
			shift_start_time = shift_details.get("start_time")
			shift_end_time = shift_details.get("end_time")
			shift_start = datetime.combine(attendance_date, get_time(shift_details.get("start_time")))
			shift_end = datetime.combine(attendance_date, get_time(shift_details.get("end_time")))
			mid_shift = shift_start + (shift_end - shift_start) / 2			
			
			if log_time <= mid_shift:
				custom_in_times = log_time				
				late_entry = self.late_entry(custom_in_times)
			else:				
				custom_out_times = log_time
				early_exit = self.early_exit(custom_out_times)
			
		else:
			custom_in_times = log_time
		
		args = {
			"doctype": "Attendance",
			"employee": self.employee,
			"attendance_date": self.attendance_date,
			"status": "Present",
			"shift": self.shift,
			"custom_start_time": shift_start_time,
			"custom_end_time": shift_end_time,
			"in_time": custom_in_times,
			"out_time": custom_out_times,
			"custom_in_times": custom_in_times,
			"custom_out_times": custom_out_times,
			"late_entry": late_entry,
			"early_exit": early_exit,
		}

		doc = frappe.get_doc(args).save(ignore_permissions=True)
		doc.submit()
		# Mubashir Bashir 25-02-2025 End

	def late_entry(self, in_time):
		if(not in_time):
			return False
		if (not self.shift or not self.log): 
			return False
		doc = frappe.get_doc("Shift Type", self.shift)
		log = get_datetime(in_time)
		late_time = log
		if(doc.enable_auto_attendance and doc.custom_grace_in_time): 
			late_time = get_datetime("%s %s"%(getdate(in_time), doc.custom_grace_in_time))
		else:
			late_time = get_datetime("%s %s"%(getdate(in_time), doc.start_time))
		if(log>late_time):
			return True
		else:
			return False

	def early_exit(self, out_time):
		if(not out_time):
			return False
		if (not self.shift): 
			return False
		doc = frappe.get_doc("Shift Type", self.shift)
		log = get_datetime(out_time)
		exit_time = log
		if(doc.enable_auto_attendance and doc.custom_grace_out_time): 	
			exit_time = get_datetime("%s %s"%(getdate(out_time), doc.custom_grace_out_time))
		else:
			exit_time = get_datetime("%s %s"%(getdate(out_time), doc.end_time))
		
		if(log<exit_time):
			return True
		else:
			return False

	def get_2_hours_late(self):
		if(not self.shift): return False
		doc = frappe.get_doc("Shift Type", self.shift)
		log_in_time = get_datetime(self.log)
		shift_in_time = log_in_time
		if(doc.enable_auto_attendance and doc.custom_grace_in_time): 
			shift_in_time = get_datetime("%s %s"%(getdate(self.log), doc.custom_grace_in_time))
		else:
			shift_in_time = get_datetime("%s %s"%(getdate(self.log), doc.start_time))
		
		hours_differnce = time_diff_in_hours(log_in_time, shift_in_time)
		if(hours_differnce>2):
			return True
		else:
			return False

	def cal_overtime_hours(self, hours_worked):
		overtime_hours = None
		if(not self.shift): 
			return overtime_hours
		total_working_hours = frappe.db.get_value("Shift Type", self.shift, "custom_total_working_hours")
		if(not total_working_hours): 
			return overtime_hours
		if(hours_worked>total_working_hours):
			
			overtime_hours = time_diff(str(hours_worked), str(total_working_hours))

		return overtime_hours



@frappe.whitelist()
def get_logs_details(filters=None):
	return frappe.db.sql("""
		select device_ip, log_type, log
		from `tabAttendance Log`
		where
			docstatus=0
			and company=%(company)s
			and employee=%(employee)s
			and attendance_date=%(attendance_date)s
	""", filters, as_dict=1)


# Mubashir 25-02-2025 Start

from frappe.utils import nowdate, now_datetime

@frappe.whitelist()
def get_employee_shift(employee):
	"""Get latest shift assignment for an employee."""
	shift = frappe.db.sql("""
		SELECT shift_type FROM `tabShift Assignment`
		WHERE employee=%s AND docstatus=1
		ORDER BY start_date DESC LIMIT 1
	""", (employee,), as_dict=True)
	
	return shift[0]['shift_type'] if shift else None

@frappe.whitelist()
def check_attendance_status(employee, shift):
	"""Check if the employee already has an attendance log for the same shift today."""
	existing_log = frappe.db.exists("Attendance Log", {
		"employee": employee,
		"shift": shift,
		"attendance_date": nowdate()
	})

	return "check_out" if existing_log else "check_in"

@frappe.whitelist()
def get_current_datetime():
	"""Return current date and datetime"""
	return {"date": nowdate(), "datetime": now_datetime()}

@frappe.whitelist()
def record_attendance(docname, button_type, latitude=None, longitude=None):
	"""Mark check-in or check-out and update attendance log."""
	doc = frappe.get_doc("Attendance Log", docname)
	
	if button_type in ["mark_check_in", "mark_check_out"]:
		doc.attendance_date = nowdate()
		doc.log = now_datetime()
		if latitude and longitude:
			doc.latitude = latitude
			doc.longitude = longitude

	doc.save()
	return f"{button_type.replace('_', ' ').title()} recorded successfully."

# Mubashir 25-02-2025 Start

#  bench --site erp.alkhidmat.com execute akf_hrms.akf_hrms.doctype.attendance_log.attendance_log_v01.delete_attendance
def delete_attendance():
	total = frappe.db.sql('''delete from `tabAttendance` 
			where docstatus=1 and status='Present' and owner='Administrator'  and attendance_date='2025-10-05' ''')
	frappe.db.sql('''delete from `tabAttendance Log` 
			where owner='Administrator'  and attendance_date='2025-10-05' ''')
	print(total)