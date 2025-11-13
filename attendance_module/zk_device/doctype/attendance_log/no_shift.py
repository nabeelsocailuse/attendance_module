import frappe
from frappe.utils import (
    get_datetime
)

def get_no_shift(self):
	if(not self.shift):
		filters =  {
			'employee': self.employee,
			'attendance_date' :self.attendance_date
		}
	
		logs_resp = frappe.db.sql('''
			Select 
				log 
			From 
				`tabAttendance Log`
			Where 
				docstatus=0
				and employee = %(employee)s
				and attendance_date=%(attendance_date)s
			Order by 
				log asc
		''', filters, as_dict=1)

		in_time = None
		out_time = None
		hours_worked = None

		if not logs_resp:
			return filters
		
		logs_list = [row.log for row in logs_resp]
		
		if(len(logs_list)>1):
			in_time = get_datetime(logs_list[0])
			out_time = get_datetime(logs_list[-1])
			hours_worked = (out_time - in_time)
		else:
			in_time = logs_list[0]

		filters.update({
			'in_time': in_time,
			'out_time': out_time,
			'custom_in_times': in_time,
			'custom_out_times': out_time,
			'custom_hours_worked': hours_worked,
		})
		
		return filters