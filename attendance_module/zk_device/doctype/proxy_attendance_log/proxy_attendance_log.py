# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProxyAttendanceLog(Document):
	def validate(self):
		self.set_employee_and_shift_type()
	# def after_insert(self):
	# 	self.set_employee_and_shift_type()
		self.create_attendance_log()
	def set_employee_and_shift_type(self):
		query = f""" 
				select 
					e.name,
					(Select shift_type from `tabShift Assignment` where docstatus=1 and status="Active" and employee=e.name order by start_date limit 1) as shift_type
				from `tabEmployee` e inner join `tabZK IP Detail` zk on (e.company=zk.company)
				where attendance_device_id='{self.device_id}' and zk.device_ip = '{self.device_ip}'
				group by e.attendance_device_id
				"""
		for d in frappe.db.sql(query, as_dict=1):
			self.employee = d.name
			self.shift = d.shift_type
			# frappe.db.set_value("Proxy Attendance Log", self.name, "employee", d.name)
			# frappe.db.set_value("Proxy Attendance Log", self.name, "shift", d.shift_type)

	'''def create_attendance_log(self):
		args = frappe._dict({
				"company": self.company,
				"employee": self.employee,
				"device_id": self.device_id,
				"device_ip": self.device_ip,
				"device_port": "4370",
				"attendance_date": frappe.utils.getdate(self.log),
				"log": self.log,
				"doctype": "Attendance Log",
				"log_type": self.log_type,
				"log_from": "ZK Tool",
			})
						
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)'''
# bench --site erp.alkhidmat.com execute akf_hrms.zk_device.doctype.zk_tool.zk_tool.reset_status
