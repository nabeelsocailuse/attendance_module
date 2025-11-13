# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff, getdate, get_datetime, time_diff_in_hours, get_time, datetime
from datetime import datetime	# Mubashir Bashir 25-02-2025

from attendance_module.zk_device.doctype.attendance_log.shift_details import (
    get_shift_info
)
from attendance_module.zk_device.doctype.attendance_log.no_shift import (
    get_no_shift
)

class AttendanceLog(Document):
	def validate(self):
		self.set_employee_and_shift_type()
		self.process_attendance()
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
		# frappe.enqueue(process_attendance_in_background, self=self)

	def process_attendance(self):
		cargs = {}
		if(self.shift):
			cargs  = get_shift_info(self)
		else:
			cargs = get_no_shift(self)

		attendance = self.get_attendance(cargs)
		if (attendance):
			self.update_attendance(attendance, cargs)
		else:
			self.create_attendance(cargs)
		

	def get_attendance(self, cargs):
		
		attendance = frappe.db.sql('''
			Select 
				name, status
			From 
				`tabAttendance`
			Where 
				docstatus=1
				and status in ("Present", "Half Day")
				and employee=%(employee)s
				and attendance_date = %(attendance_date)s
		''', cargs, as_dict=1)

		args = frappe._dict()
		
		for att in attendance:
			args.update(att)
		
		return args

	def update_attendance(self, attendance, cargs):
		frappe.db.set_value("Attendance", attendance.name, cargs)
		'''if(self.shift and attendance):
			frappe.db.set_value("Attendance", attendance.name, cargs)'''

	def create_attendance(self, cargs):
		doc = frappe.get_doc({
			"doctype": "Attendance",
			"employee": self.employee,
			"attendance_date": cargs.get("attendance_date"),
			"status": "Present",
		})
		doc.save(ignore_permissions=True)
		doc.submit()

		frappe.db.set_value("Attendance", doc.name, cargs)
		'''if(self.shift):	
			# cargs  = get_logs_info(self)
			# frappe.throw(f"{cargs}")
			frappe.db.set_value("Attendance", doc.name, cargs)
		'''
	
''' Background Jobs'''

def process_employee_and_shift_type(self):
	if(not self.shift): 
		query = f""" 
				select 
					e.name,
					(Select shift_type from `tabShift Assignment` where docstatus=1 and status="Active" and employee=e.name order by start_date limit 1) as shift_type
				from `tabEmployee` e inner join `tabZK IP Detail` zk on (e.branch=zk.branch)
				where attendance_device_id='{self.device_id}' and zk.device_ip = '{self.device_ip}'
				group by e.attendance_device_id
			"""
		for d in frappe.db.sql(query, as_dict=1):
			frappe.db.set_value('Attendance Log', self.name,{
				'employee': d.name,
				'shift': d.shift_type
			})

def process_attendance_in_background(self):
	cargs = {}
	if(self.shift):
		cargs  = get_shift_info(self)
	else:
		cargs = get_no_shift(self)

	attendance = self.get_attendance(cargs)
	if (attendance):
		self.update_attendance(attendance, cargs)
	else:
		self.create_attendance(cargs)
	

''' REST APIs '''

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