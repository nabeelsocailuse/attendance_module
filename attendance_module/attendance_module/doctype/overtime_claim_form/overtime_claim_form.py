# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe, ast
from frappe.model.document import Document
from frappe.utils import fmt_money, money_in_words, get_link_to_form, get_timedelta, time_diff, get_time
MONTHSLIST = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

class OvertimeClaimForm(Document):
	def autoname(self):
		from frappe.model.naming import make_autoname
		self.name = make_autoname(self.naming_series%{
			"employee": self.employee, 
			"month": self.month, 
			"year": self.year
			})

	def validate(self):
		self.already_applied_for_overtime()
		self.set_salary_structure_assignment()

	def on_submit(self):
		self.create_additional_salary()
		self.update_attendance()

	def create_additional_salary(self):
		month = MONTHSLIST.index(self.month) + 1
		payroll_date = f"{self.year}-{month}-21"
		doc = frappe.get_doc({
			"doctype": "Additional Salary",
			"employee": self.employee,
			"payroll_date": payroll_date,
			"salary_component": "Overtime",
			"overwrite_salary_structure_amount": 0,
			"amount": self.amount_in_figures,
		}).submit()
		self.link_additional_salary(doc.name)
		frappe.msgprint("Addtional Salary has been created.", alert=1)
	
	def link_additional_salary(self, additional_salary):
		frappe.db.set_value(self.doctype, self.name, 'additional_salary', additional_salary)
		self.reload()

	def update_attendance(self, cancelled=0):
		for row in self.detail_of_overtime:
			if(row.attendance):
				custom_overtime_claim = 0 if(cancelled) else 1 
				ocfName = None if(cancelled) else self.name 
				frappe.db.set_value("Attendance", row.attendance, "custom_overtime_claim", custom_overtime_claim)
				frappe.db.set_value("Attendance", row.attendance, "custom_overtime_claim_form", ocfName)

	def on_cancel(self):
		self.delete_additional_salary()
		self.update_attendance(cancelled=1)
		self.update_fields()
		
	def update_fields(self):
		frappe.db.sql(f""" update `tab{self.doctype}` 
			set approval_status = "Cancelled", additional_salary=""
				where name = '{self.name}' """)
		self.reload()
	
	def delete_additional_salary(self):
		frappe.db.sql(f""" delete from `tabAdditional Salary` where name = '{self.additional_salary}' """)
	
	@frappe.whitelist()
	def get_details_of_overtime(self, reset=False):
		self.already_applied_for_overtime()
		self.set_salary_structure_assignment()
		if(reset): self.set("detail_of_overtime", self.get_attendance())
		self.set_total_hours_worked()
		self.set_total_overtime_hours()
		self.set_amount_in_figures()
		self.set_amount_in_words()

		return True if(self.detail_of_overtime) else False
	
	def already_applied_for_overtime(self):
		name = frappe.db.get_value("Overtime Claim Form", {
			"docstatus": ["<", 2],
			"year": self.year,
			"month": self.month,
			"employee": self.employee,
			"name": ["!=", self.name]
		}, "name")
		if(name):
			link_to_form = get_link_to_form("Overtime Claim Form", name, "Overtime Claim Form")

			frappe.throw(f"{link_to_form} on {self.month}-{self.year}", title="APPLIED")
	
	@frappe.whitelist()
	def set_salary_structure_assignment(self):
		ssa = frappe.db.get_value("Salary Structure Assignment", {"docstatus": 1, "employee": self.employee}, ["name", "custom_hourly_base"], as_dict=1)
		if(ssa):
			self.salary_structure_assignment = ssa.name
			self.hourly_rate = ssa.custom_hourly_base
		else:
			frappe.throw(f"No active, salary structure assignment found.")
	
	def set_total_hours_worked(self):
		self.total_hours_worked = get_total_hours_worked(self.detail_of_overtime)
	
	def get_attendance(self):
		return frappe.db.sql(f""" 
			Select (attendance_date) as date, in_time, out_time, 
				(custom_total_working_hours) as total_working_hours,
				(custom_hours_worked) as hours_worked,
				(custom_overtime_hours) as overtime_hours,
				(name) as attendance
			From `tabAttendance`
			Where
				docstatus=1
				and custom_overtime_claim = 0
				and ifnull(attendance_adjustment,"")=""
				and ifnull(custom_hours_worked, "")!=""
				and ifnull(custom_overtime_hours, "")!=""
				and (TIME_TO_SEC(custom_overtime_hours)/3600)>=2
				and year(attendance_date) = '{self.year}'
				and monthname(attendance_date) = '{self.month}'
				and employee = '{self.employee}'
		""", as_dict=1)

	def set_total_overtime_hours(self):
		self.total_overtime_hours = get_total_overtime_hours(self.detail_of_overtime)

	def set_amount_in_figures(self):
		self.amount_in_figures = float(self.get_total_overtime_seconds()) * float(self.hourly_rate)
		
	def set_amount_in_words(self):
		self.amount_in_words = money_in_words(self.amount_in_figures)
	
	def get_total_overtime_seconds(self):
		if(not self.total_overtime_hours): return 0.0
		ot_split = (self.total_overtime_hours).split(":")
		return ((3600 * float(ot_split[0])) + (60 * float(ot_split[1])))/3600
	
	# This function is for future changes (if any)
	@frappe.whitelist()
	def calculate_detail_of_overtime(self):
		self.set_detail_of_overtime_hours()
		self.set_total_hours_worked()
		self.set_total_overtime_hours()
		self.set_amount_in_figures()
		self.set_amount_in_words()
	
	# This function is for future changes (if any)
	def set_detail_of_overtime_hours(self):
		for row in self.detail_of_overtime:
			row.hours_worked = time_diff(row.out_time, row.in_time)
			row.overtime_hours = time_diff(row.out_time, row.in_time)
			if(get_time(row.in_time)>get_time(row.out_time)): 
				frappe.throw(f"Row#{row.idx}: In-Time must be less than Out-Time.")

def get_total_hours_worked(hours_worked_time_list):
	total_h_worked= '0'	
	hours_worked_ = 0
	
	for tm in hours_worked_time_list:
		if(tm.hours_worked):
			timeParts = [int(s) for s in str(tm.hours_worked).split(':')]
			hours_worked_ += (timeParts[0] * 60 + timeParts[1]) * 60 + timeParts[2]
	# hours_worked_, sec = divmod(hours_worked_, 60)
	# hr, min_ = divmod(hours_worked_, 60)
	# total_h_worked = '{}:{}'.format(int(hr), str(str(int(min_)).zfill(2)))
	# return total_h_worked

def get_total_overtime_hours(hours_worked_time_list):
	total_h_worked= '0'	
	hours_worked_ = 0
	for tm in hours_worked_time_list:
		if(tm.overtime_hours):
			timeParts = [int(s) for s in str(tm.overtime_hours).split(':')]
			hours_worked_ += (timeParts[0] * 60 + timeParts[1]) * 60 + timeParts[2]
	hours_worked_, sec = divmod(hours_worked_, 60)
	hr, min_ = divmod(hours_worked_, 60)
	total_h_worked = '{}:{}'.format(int(hr), str(str(int(min_)).zfill(2)))
	return total_h_worked

@frappe.whitelist()
def calculate_hours_worked_overtime_hours(doc):
	row = ast.literal_eval(doc)
	row = frappe._dict(row)
	print(row)
	return row
	# return time_diff(out_time, in_time)