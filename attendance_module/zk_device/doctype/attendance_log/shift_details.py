
import frappe
from datetime import datetime, timedelta, time
from frappe.utils import getdate, get_datetime


'''
	span_time = 180
'''

# bench --site al-khidmat.com execute akf_hrms.akf_hrms.doctype.attendance_log.att_log.pass_logs
# bench --site al-khidmat.com execute akf_hrms.akf_hrms.doctype.attendance_log.att_log.get_shift_info

# def pass_logs():
# 	log = "2025-09-27 03:16:00"
# 	check_in = "2025-09-27 07:46:00"
# 	logs_list = ["2025-09-26 23:16:00", "2025-09-27 03:16:00", "2025-09-27 07:46:00"]

# 	logs_list = ["2025-09-26 23:16:00", "2025-09-27 03:16:00", "2025-09-27 07:46:00"]
# 	for log in logs_list:
# 		get_shift_info(log)
	
def get_shift_info(self):	
	attendance_date = self.attendance_date
	log = self.log
	shift_type = self.shift
	
	shift_obj = frappe.get_doc('Shift Type', shift_type)
	
	start_time = get_datetime("%s %s"%(attendance_date, shift_obj.start_time))
	end_time = get_datetime("%s %s"%(attendance_date, shift_obj.end_time))
	total_working_hours = (end_time - start_time)
	
	# Late Entry & Early Exit Settings for Auto Attendance
	# add grace in-time in minutes.
	if(shift_obj.enable_late_entry_marking and hasattr(shift_obj, 'custom_grace_in_time')):
		start_time = start_time + timedelta(minutes=shift_obj.late_entry_grace_period)
	# add grace out-time in minutes.
	if(shift_obj.enable_early_exit_marking and hasattr(shift_obj, 'custom_grace_out_time')):
		end_time = end_time + timedelta(minutes=-1 * shift_obj.early_exit_grace_period)
	
	log_time = get_datetime(log)

	filters = frappe._dict({
		'employee': self.employee,
		'start_time': start_time,
		'end_time': end_time,
		'log_time': log_time
	})

	# mid time for [NIGHT] shift.
	if end_time.time() <= start_time.time():
		filters.update({
			"shift_type": "Night"
		})
		get_night_shift(filters)
	# mid time for [Morning] shift.
	else:
		filters.update({
			"shift_type": "Morning",
			"custom_total_working_hours": total_working_hours,
		})
		get_morning_shift(filters)
	

	log_dict = frappe._dict({
		'shift': shift_type,
		'attendance_date': self.attendance_date,
		'custom_start_time': start_time,
		'custom_end_time': end_time,
	})

	process_logs(filters, log_dict)
	set_log_type(self.name, filters.get('log_type'))
	
	# print(log_dict)
	return log_dict


def get_night_shift(filters):
	start_time = filters.get('start_time')
	end_time = filters.get('end_time')
	log_time = filters.get('log_time')
	# print(filters)
	# previous attendance in/out times
	pre_start_time = start_time + timedelta(days=-1)
	pre_end_time = end_time
	# current attendance in/out times
	cur_start_time = start_time
	cur_end_time = end_time + timedelta(days=1)
	# employee can come early to office 360 minutes earlier | leave office 360 minutes late.
	span_minutes = 360
	# previous attedance in/out times with span
	span_pre_start_time = pre_start_time + timedelta(minutes=-span_minutes)
	span_pre_end_time = pre_end_time + timedelta(minutes=span_minutes)
	# current attedance in/out times with span
	span_cur_start_time = cur_start_time + timedelta(minutes=-span_minutes)
	span_cur_end_time = cur_end_time + timedelta(minutes=span_minutes)

	mid_time = None

	if(log_time>=span_pre_start_time and log_time<=span_pre_end_time):
		mid_time = pre_start_time + (pre_end_time - pre_start_time) / 2
		total_working_hours = (pre_end_time - pre_start_time)
		# print('|-----------------------------|')
		# print(pre_start_time)
		# print(pre_end_time)
		# print(total_working_hours)
		filters.update({
			'start_time': pre_start_time,
			'end_time': pre_end_time,
			'query_start_time': span_pre_start_time,
			'query_end_time': span_pre_end_time,
			'custom_total_working_hours': total_working_hours,
			'mid_time': mid_time,
			'log_type': 'IN' if(log_time<mid_time) else 'OUT',
			'condition_log_in': " and (log>='{0}' and log <= '{1}') ".format(query_start_time, mid_time),
			'condition_log_out': " and (log > '{0}' and log <= '{1}' ) ".format(mid_time, query_end_time)
		})
	if(log_time>=span_cur_start_time and log_time<=span_cur_end_time):
		mid_time = cur_start_time + (cur_end_time - cur_start_time) / 2
		total_working_hours = (cur_end_time - cur_start_time)
		filters.update({
			'start_time': cur_start_time,
			'end_time': cur_end_time,
			'query_start_time': span_cur_start_time,
			'query_end_time': span_cur_end_time,
			'custom_total_working_hours': total_working_hours,
			'mid_time': mid_time,
			'log_type': 'IN' if(log_time<mid_time) else 'OUT',
			'condition_log_in': " and (log>='{0}' and log <= '{1}') ".format(query_start_time, mid_time),
			'condition_log_out': " and (log > '{0}' and log <= '{1}' ) ".format(mid_time, query_end_time)
		})

def get_morning_shift(filters):
	start_time = filters.get('start_time')
	end_time = filters.get('end_time')
	log_time = filters.get('log_time')
 
	mid_time = start_time + (end_time - start_time) / 2
	# employee can come early to office 360 minutes earlier | leave office 360 minutes late.
	span_minutes = 360
	query_start_time = start_time + timedelta(minutes=-span_minutes)
	query_end_time = end_time + timedelta(minutes=span_minutes)
	filters.update({
		'query_start_time': query_start_time,
		'query_end_time': query_end_time,
		"mid_time": mid_time,
		'log_type': 'IN' if(log_time<mid_time) else 'OUT',
		'condition_log_in':  " and attendance_date = '{0}' and log <= '{1}' ".format(getdate(mid_time), mid_time),
		'condition_log_out': " and attendance_date = '{0}' and log > '{1}' ".format(getdate(mid_time), mid_time)
	})

def process_logs(filters, log_dict):
	in_data = frappe.db.sql('''
		Select log From `tabAttendance Log`
		Where 
			docstatus=0
			and employee = %(employee)s
			{0}
		Order by log asc
		Limit 1
	'''.format(filters.get('condition_log_in')), filters)

	out_data = frappe.db.sql('''
		Select log
		From `tabAttendance Log`
		Where 
			docstatus=0
			and employee = %(employee)s
			{0}
		Order by log desc
		Limit 1
	'''.format(filters.get('condition_log_out')), filters)

	# frappe.throw(f"{filters} {in_data} {out_data}")
	in_time = get_datetime(in_data[0][0]) if(in_data) else None
	out_time = get_datetime(out_data[0][0]) if(out_data) else None
	hours_worked = get_hours_worked(in_time, out_time)
	overtime_hours = get_overtime_hours(hours_worked, filters.get("custom_total_working_hours"))
	
	log_dict.update({
		'employee': filters.get('employee'),
		'attendance_date': getdate(filters.get('start_time')),
		'in_time': in_time,
		'out_time': out_time,
		'custom_total_working_hours': filters.get('custom_total_working_hours'),
		'custom_hours_worked': hours_worked,
		'custom_overtime_hours': overtime_hours,
		'custom_in_times': in_time,
		'custom_out_times': out_time,
		'late_entry': get_late_entry(in_time, filters.get("start_time")),
		'early_exit': get_early_exit(out_time, filters.get("end_time")), 
	})

def get_hours_worked(in_time, out_time):
	if(in_time and out_time):
		return (out_time - in_time)
	return None

def get_overtime_hours(hours_worked, total_working_hours):
	if (hours_worked):
		if(hours_worked > total_working_hours):
			diff_str = (hours_worked - total_working_hours)
			overtime_hours = str(diff_str).split(",")[-1].strip()
			return overtime_hours
	return None

def get_late_entry(in_time, start_time):
	if(in_time): 
		if(in_time > start_time):
			return True
	return False

def get_early_exit(out_time, end_time):
	if(out_time): 
		if(out_time < end_time):
			return True
	return False

def set_log_type(logId, log_type):
	frappe.db.set_value('Attendance Log', logId, 'log_type', log_type)
	frappe.db.commit()

