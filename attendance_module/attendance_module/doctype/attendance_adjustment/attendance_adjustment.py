import frappe
from frappe import _
from datetime import datetime, timedelta
from frappe.model.document import Document
from frappe.utils import formatdate, time_diff

class AttendanceAdjustment(Document):
	@frappe.whitelist()
	def get_attendance_stats(self, adjust=None):
		attendance_date =""
		if(not adjust):
			attendance_date =f" and (attendance_date between DATE_SUB('{self.posting_date}', INTERVAL 30 DAY) and '{self.posting_date}')"
		elif(adjust==1):
			attendance_date = f" and attendance_date = '{self.adjustment_date}' "

		# if(self.docstatus==0):
		# 	attendance_date += f""" and ifnull(attendance_adjustment, "")=""  """
		# elif(self.docstatus==1):
		# 	attendance_date += f""" and name = '{self.adjustment_for}' """

		return frappe.db.sql(f""" 
			select name, attendance_date,  custom_total_working_hours, custom_hours_worked, custom_overtime_hours
			from `tabAttendance`
			where docstatus=1
			and status='Present'
			and custom_overtime_claim=0
			
			and ifnull(custom_overtime_hours, "")!=""
			and TIME_TO_SEC(custom_overtime_hours) > 5400
			and employee='{self.employee}'
			{attendance_date}
			order by attendance_date
		""", as_dict=1)
    
	@frappe.whitelist()
	def get_compensation_date_stats(self):
		if(not self.compensation_type): return
		conditions = " and late_entry = 1 " if(self.compensation_type=="Late Entry" and self.docstatus==0) else ""
		conditions += " and early_exit = 1 " if(self.compensation_type=="Early Exit" and self.docstatus==0) else ""
		if(self.compensation_for and self.docstatus==1): conditions = f" and name = '{self.compensation_for}' "
		# else: conditions = """ and (ifnull(custom_overtime_hours, "")="" or custom_overtime_hours <= 0) """
		return frappe.db.sql(f""" 
			select name, custom_total_working_hours, in_time, out_time, custom_hours_worked, ifnull(custom_overtime_hours, '-')  as custom_overtime_hours
			from `tabAttendance`
			where docstatus=1
			and status in ('Present', 'Half Day')
			and custom_overtime_claim=0
			and employee='{self.employee}'
			and attendance_date = '{self.compensation_date}'
			{conditions}
		""", as_dict=1)
    
	@frappe.whitelist()
	def get_adjustment_date_stats(self):
		conditions = ""
		if(self.adjustment_for and self.docstatus==1): conditions = f" and name = '{self.adjustment_for}' "
		return frappe.db.sql(f""" 
			select name, custom_total_working_hours, in_time, out_time, custom_hours_worked, ifnull(custom_overtime_hours, '-')  as custom_overtime_hours
			from `tabAttendance`
			where docstatus=1
			and status in ('Present', 'Half Day')
			and custom_overtime_claim=0
			and employee='{self.employee}'
			and attendance_date = '{self.adjustment_date}'
			{conditions}
		""", as_dict=1)

	@frappe.whitelist()
	def get_adjustment_for(self):
		resp = self.get_attendance_stats(adjust=1)
		return resp[0].name if resp and len(resp) > 0 else None

	@frappe.whitelist()
	def get_compensation_for(self):
		resp = self.get_compensation_date_stats()
		
		return resp[0].name if resp and len(resp) > 0 else None

	@frappe.whitelist()
	def verify_linkages(self):
		link1 = frappe.db.get_value('Attendance', self.adjustment_for, 'attendance_adjustment')
		link2 = frappe.db.get_value('Attendance', self.compensation_for, 'attendance_adjustment')
		return True if(link1 or link2) else False

	@frappe.whitelist()
	def de_link(self):
		frappe.db.set_value('Attendance Adjustment', self.name, 'docstatus', 2)
		frappe.db.set_value('Attendance Adjustment', self.name, 'status', 'Cancelled')
		frappe.db.set_value('Attendance Adjustment', self.name, 'adjustment_for', None)
		frappe.db.set_value('Attendance Adjustment', self.name, 'compensation_for', None)
		self.update_attendance(True)
		self.reload()
		frappe.msgprint('Documents are delinked successfully!', alert=1)
		
	def validate(self):
		self.validate_dates()
		self.validate_adjustments()

	def validate_dates(self):
		if self.adjustment_date and self.compensation_date:
			if self.adjustment_date >= self.compensation_date:
				frappe.throw(
					_("Adjustment Date must be earlier than Compensation Date."),
					title=_("Invalid Dates")
				)

	def validate_adjustments(self):
		adjust_stats = self.get_adjustment_date_stats()
		comp_stats = self.get_compensation_date_stats()
		if((not self.adjustment_for) or (not adjust_stats)): frappe.throw(f'No attendance record available for adjustment on {formatdate(self.adjustment_date)}', title='Adjustment For')
		if((not self.compensation_for) or (not comp_stats)): frappe.throw(f'No attendance record available for compensation on {formatdate(self.compensation_date)}', title='Compensation For')
			
	def on_submit(self):
		self.update_attendance(False)
		frappe.msgprint('Attendance records are updated successfully!', alert=1)

	def update_attendance(self, cancel=False):
		
		def adjustment_for_attendance():
			custom_adjustment = 0 if(cancel) else 1
			attendance_adjustment = None if(cancel) else self.name
			frappe.db.set_value('Attendance', self.adjustment_for, 'custom_adjustment', custom_adjustment)
			frappe.db.set_value('Attendance', self.adjustment_for, 'attendance_adjustment', attendance_adjustment)
			
		def compensation_for_attendance():
			overtime_hours = frappe.db.get_value('Attendance', self.adjustment_for, 'custom_overtime_hours')
			if(not overtime_hours and (not cancel)): return
			
			if(self.compensation_type=='Late Entry'):
				timeFunc = f'addtime' if(cancel) else f'subtime'
				resp = frappe.db.sql(f""" select 
						{timeFunc}(in_time, '{overtime_hours}') as in_time,
						(case when {timeFunc}(in_time, '{overtime_hours}')<=addtime(attendance_date, custom_start_time)
							then 0 else 1 end
						) late_entry,
						out_time
					from 
						`tabAttendance`
					where 
						docstatus=1
						and name='{self.compensation_for}'
				""", as_dict=1)
				print(f'Late Entry: {resp}')
				if(resp):
					r = resp[0]
					frappe.db.set_value('Attendance', self.compensation_for, 'custom_adjustment', 0 if(cancel) else 1) 
					frappe.db.set_value('Attendance', self.compensation_for, 'attendance_adjustment', None if(cancel) else self.name)
					frappe.db.set_value('Attendance', self.compensation_for, 'in_time', r.in_time)
					frappe.db.set_value('Attendance', self.compensation_for, 'late_entry', r.late_entry)
					hours_worked = time_diff(r.out_time, r.in_time)
					frappe.db.set_value('Attendance', self.compensation_for, 'custom_hours_worked', hours_worked)
					
			elif(self.compensation_type=='Early Exit'):
				timeFunc = f'subtime' if(cancel) else f'addtime'
				resp = frappe.db.sql(f""" 
					select
						{timeFunc}(out_time, '{overtime_hours}') as out_time,
						(case when {timeFunc}(out_time, '{overtime_hours}')>=addtime(attendance_date, custom_end_time)
							then 0 else 1 end
						) early_exit,
						in_time
					from 
						`tabAttendance`
					where 
						docstatus=1
						and name='{self.compensation_for}'
				""", as_dict=1)
				
				if(resp):
					r = resp[0]
					print(f'Early Exit: {resp}')
					frappe.db.set_value('Attendance', self.compensation_for, 'custom_adjustment', 0 if(cancel) else 1) 
					frappe.db.set_value('Attendance', self.compensation_for, 'attendance_adjustment', None if(cancel) else self.name)
					frappe.db.set_value('Attendance', self.compensation_for, 'out_time', r.out_time)
					frappe.db.set_value('Attendance', self.compensation_for, 'early_exit', r.early_exit)
					hours_worked = time_diff(r.out_time, r.in_time)
					frappe.db.set_value('Attendance', self.compensation_for, 'custom_hours_worked', hours_worked)
					
		adjustment_for_attendance()
		compensation_for_attendance()



# @frappe.whitelist()
# def get_less_than_90_mins_records():
# 	query = frappe.db.sql("""select 
# 		adj.name as Adjustment
# 	from `tabAttendance Adjustment` as adj
# 	left join `tabAttendance` as att 
# 		on att.name = adj.adjustment_for
# 	where adj.docstatus = 0
# 	and att.custom_overtime_claim = 0
# 	and att.custom_overtime_hours is not null
# 	and TIME_TO_SEC(att.custom_overtime_hours) <= 5400
# 	and att.attendance_date = adj.adjustment_date
# 	and adj.adjustment_date > '2025-07-01'
# 	-- and adj.status not in ('Rejected by the Head of Department', 'Rejected by CEO')
# 	and adj.status = 'Open'
# 	order by adj.employee;
# 	""", as_dict=1)
# 	# print(query)
# 	for rec in records:
#         # Update each record's status
#         frappe.db.set_value(
#             "Attendance Adjustment",
#             rec["name"],
#             "status",
#             "Rejected by the Head of Department"
#         )

#     frappe.db.commit()

#     print f"{len(records)} record(s) updated to 'Rejected by the Head of Department'."
@frappe.whitelist()
def get_less_than_90_mins_records():
    records = frappe.db.sql("""
        select 
            adj.name as Adjustment,
			att.name as Attendance
        from `tabAttendance Adjustment` as adj
        left join `tabAttendance` as att 
            on att.name = adj.adjustment_for
        where adj.docstatus = 0
          and att.custom_overtime_claim = 0
          and att.custom_overtime_hours is null
          -- and TIME_TO_SEC(att.custom_overtime_hours) <= 7200
          and att.attendance_date = adj.adjustment_date
          and adj.adjustment_date > '2025-07-01'
          and adj.status not in ('Rejected by the Head of Department', 'Rejected by CEO')
        order by adj.employee
    """, as_dict=True)

    for rec in records:
        frappe.db.set_value(
            "Attendance Adjustment",
            rec["Adjustment"],
            "status",
            "Rejected by the Head of Department"
        )

    frappe.db.commit()

    # print (records)
    print (f"{len(records)} record(s) updated to 'Rejected by the Head of Department'.")

	# bench --site erp.alkhidmat.com execute akf_hrms.akf_hrms.doctype.attendance_adjustment.attendance_adjustment.get_less_than_90_mins_records