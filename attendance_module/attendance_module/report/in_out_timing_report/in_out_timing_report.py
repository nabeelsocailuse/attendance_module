# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import timedelta, datetime
from frappe.utils import today
from frappe import _
import re


def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def get_columns(filters):
	if ("Leave Approver" in frappe.get_roles()) or ("Principle" in frappe.get_roles()):
		columns = [
			_("Employee") + ":Data:180"
		]
	else:
		columns = [
			_("Employee") + ":Link/Employee:180"
		]
	columns.extend([
		_("Employee Name") + "::180",
		_("CNIC") + "::180",
		_("Branch") + ":Link/Branch:150",
		_("Department") + ":Link/Department:150",
		_("Designation") + ":Link/Designation:150",
		_("WD") + ":Float:70",
		_("HW") + ":Data:70",
		_("Total Present") + ":Float:140",
		_("Total Leaves") + ":Float:140",
		_("Total Absent") + ":Float:140",
		_("Total Holidays") + ":Float:140",
		_("") + "::60"
	])

	for days in get_days_in_month(filters):
		columns.append(str(frappe.utils.formatdate(str(days), "dd-MMM")) + "::80")
	return columns


def get_data(filters):
	data = []
	days_list = get_days_in_month(filters)
	attendnace_map = get_attendance_list(filters)
	employee_map = get_employee_details(filters)
	holiday_map = get_holiday(employee_map, filters)
	default_holiday_list = frappe.db.get_value("Company", filters.get("company"), "default_holiday_list")

	status_map = {
		"On Leave": "<font color='blue'><center><b>L</b></center></font>",
		"None": "<font color='red'><center><b>A</b></center></font>",
		"Absent": "<font color='red'><center><b>A</b></center></font>",
		"Holiday": "<center><b>H</b></center>",
		"Work From Home": "<center><b>WFH</b></center>",
	}

	for employee_id in sorted(attendnace_map):
		employee_data = employee_map.get(employee_id)
		if not employee_data:
			continue
		today_date = datetime.strptime(str(today()), "%Y-%m-%d").date()

		total_days_worked = 0
		total_present = total_absent = total_leaves = total_holidays = 0.0
		hours_worked_time_list = ["0:00:00"]

		inlist, outlist, hwlist = [], [], []

		for day in days_list:
			month_date = datetime.strptime(str(day), "%Y-%m-%d").date()
			status_data = attendnace_map.get(employee_id).get(day, ["None"])
			status = status_data[0]

			if status == "None" and holiday_map:
				emp_holiday_list = employee_data.holiday_list if employee_data.holiday_list else default_holiday_list
				if (emp_holiday_list in holiday_map) and (month_date in holiday_map[emp_holiday_list]):
					status = "Holiday"

			if status in ["None", "Absent", "On Leave", "Work From Home", "Holiday"]:
				status_value = status_map[status] if today_date >= month_date else ""
				inlist += [status_value]
				outlist += [status_value]
				hwlist += [status_value]

				if (today_date >= month_date) and status in ["None", "Absent"]:
					total_absent += 1
				if (today_date >= month_date) and status == "On Leave":
					total_leaves += 1
				if status == "Holiday":
					total_holidays += 1

			elif status in ["Present", "Half Day"]:
				total_days_worked += 1

				check_in_raw = status_data[1]
				check_out_raw = status_data[2]
				hours_raw = status_data[3]

				late_entry = status_data[4]
				early_exit = status_data[5]
				custom_total_working_hours = status_data[6]

				display_in = _format_hhmmss(check_in_raw)
				display_out = _format_hhmmss(check_out_raw)
				display_hw = _format_hhmmss(hours_raw)

				if _time_to_seconds(hours_raw) and _time_to_seconds(custom_total_working_hours) and \
				   _time_to_seconds(hours_raw) < _time_to_seconds(custom_total_working_hours):
					display_hw = f"<span style='background-color: red; color: white;'>{display_hw}</span>"

				if late_entry and display_in:
					display_in = f"<span style='background-color: red; color: white;'>{display_in}</span>"
				if early_exit and display_out:
					display_out = f"<span style='background-color: red; color: white;'>{display_out}</span>"

				if status == "Present":
					inlist += [display_in if display_in else ""]
					outlist += [display_out if display_out else ""]
					hwlist += [display_hw if display_hw else ""]
					total_present += 1

				elif status == "Half Day":
					inlist += [f"HD {display_in}" if display_in else ""]
					outlist += [f"HD {display_out}" if display_out else ""]
					hwlist += [f"HD {display_hw}" if display_hw else ""]
					total_present += 0.5
					total_leaves += 0.5

				hours_worked_time_list.append(status_data[3])

		working_hours = get_total_hours_worked(hours_worked_time_list)
		row1 = [employee_id, employee_data.employee_name, employee_data.custom_cnic,
		        employee_data.branch, employee_data.department, employee_data.designation,
		        total_days_worked, working_hours, float(total_present), float(total_leaves),
		        float(total_absent), float(total_holidays), "<b>In</b>"] + inlist
		row2 = ["", "", "", "", "", "", "", "", "", "", "", "", "<b>Out</b>"] + outlist
		row3 = ["", "", "", "", "", "", "", "", "", "", "", "", "<b>HW</b>"] + hwlist

		data.append(row1)
		data.append(row2)
		data.append(row3)

	return data


def get_attendance_list(filters):
	conditions = get_conditions(filters)
	attendance_list = frappe.db.sql("""
		select employee, attendance_date as day_of_month,
		status, ifnull(in_time, "0:00:00") as check_in_time,
		ifnull(out_time ,  "0:00:00") as check_out_time,
		(case when (custom_hours_worked="" or custom_hours_worked is null) then "0:00:00" else  custom_hours_worked end) as hours_worked,
		late_entry, early_exit, custom_total_working_hours
		from tabAttendance
		where docstatus = 1 %s order by employee, attendance_date""" % conditions, filters, as_dict=1)

	att_map = {}
	for d in attendance_list:
		att_map.setdefault(d.employee, frappe._dict()).setdefault(d.day_of_month, "")
		att_map[d.employee][str(d.day_of_month)] = [
			d.status,
			get_times_split(d.check_in_time),
			get_times_split(d.check_out_time),
			d.hours_worked,
			d.late_entry,
			d.early_exit,
			d.custom_total_working_hours
		]

	return att_map


def get_conditions(filters, is_employee=False):
	conditions = ""
	if is_employee:
		if filters.get("company"): conditions += " and company = %(company)s"
		if filters.get("employee"): conditions += " and name = %(employee)s"
		if filters.get("branch"): conditions += " and branch = %(branch)s"
		if filters.get("department"): conditions += " and department = %(department)s"
		if filters.get("designation"): conditions += " and designation = %(designation)s"
	else:
		if (filters.get("from_date") and filters.get("to_date")):
			conditions += " and attendance_date between %(from_date)s and %(to_date)s"
		if filters.get("company"): conditions += " and company = %(company)s"
		if filters.get("employee"): conditions += " and employee = %(employee)s"
		if filters.get("branch"): conditions += " and custom_branch = %(branch)s"
		if filters.get("department"): conditions += " and department = %(department)s"
		if filters.get("designation"): conditions += " and custom_designation = %(designation)s"
		if filters.get("late_entry"): conditions += " and late_entry = %(late_entry)s"
		if filters.get("early_exit"): conditions += " and early_exit = %(early_exit)s"
	return conditions


def get_times_split(_time_):
	s_time_ = str(_time_).split(" ")
	_time_ = s_time_[1].split(".")[0] if len(s_time_) > 1 else _time_
	return _time_


def get_employee_details(filters):
	conditions = get_conditions(filters, is_employee=True)
	emp_map = frappe._dict()
	for d in frappe.db.sql("""select name, employee_name, custom_cnic, branch, department, designation, date_of_joining,
		holiday_list from tabEmployee where docstatus=0 %s """ % conditions, filters, as_dict=1):
		emp_map.setdefault(d.name, d)
	return emp_map


def get_holiday(emp_map, filters):
	holiday_list = [emp_map[d]["holiday_list"] for d in emp_map if emp_map[d]["holiday_list"]]
	default_holiday_list = frappe.db.get_value("Company", filters.get("company"), "default_holiday_list")
	holiday_list.append(default_holiday_list)
	holiday_list = list(set(holiday_list))

	holiday_map = frappe._dict()
	for d in holiday_list:
		if d:
			holiday_map.setdefault(d, frappe.db.sql_list('''select holiday_date from `tabHoliday`
				where parent=%s and holiday_date between %s and %s''',
				(d, filters.get("from_date"), filters.get("to_date"))))
	return holiday_map


def get_days_in_month(filters):
	days_list = []
	start_date = datetime.strptime(str(filters.get("from_date")), "%Y-%m-%d")
	end_date = datetime.strptime(str(filters.get("to_date")), "%Y-%m-%d")
	delta = end_date - start_date
	for i in range(delta.days + 1):
		day = start_date + timedelta(days=i)
		split_day = str(day).split(" ")[0]
		days_list.append(split_day)
	return days_list


def get_total_hours_worked(hours_worked_time_list):
	total_seconds = 0
	for tm in hours_worked_time_list:
		total_seconds += _time_to_seconds(tm)

	total_minutes, sec = divmod(total_seconds, 60)
	hr, min_ = divmod(total_minutes, 60)
	return f"{int(hr)}:{str(int(min_)).zfill(2)}:{str(int(sec)).zfill(2)}"


# --- Helpers for normalization written by Mubashir ---

def _strip_html(s):
	return re.sub(r'<[^>]+>', '', str(s) or '').strip()

def _format_hhmmss(s):
	s = _strip_html(s)
	if not s or s in ("0:00:00", "0:00", "None"):
		return ""
	parts = s.split(":")
	try:
		h = int(parts[0])
		m = int(parts[1]) if len(parts) > 1 else 0
		sec = int(parts[2]) if len(parts) > 2 else 0
		return f"{h}:{str(m).zfill(2)}:{str(sec).zfill(2)}"
	except Exception:
		return s

def _time_to_seconds(s):
	s = _strip_html(s)
	if not s:
		return 0
	if ":" in s:
		parts = s.split(":")
		try:
			h = float(parts[0])
			m = float(parts[1]) if len(parts) > 1 else 0
			sec = float(parts[2]) if len(parts) > 2 else 0
			return h * 3600 + m * 60 + sec
		except Exception:
			return 0
	else:
		try:
			return float(s) * 3600
		except Exception:
			return 0