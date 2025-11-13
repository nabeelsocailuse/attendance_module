# Mubashir Bashir


from __future__ import unicode_literals
from frappe import _
import frappe
import ast

def execute(filters=None):
	columns, data = [], []
	
	
	user = frappe.session.user

	if filters.get("report_type") == "Absentees":
		columns = get_absentess_columns()
		data = get_absentees(filters, user)
	
	if filters.get("report_type") == "Late Arrival":
		columns = get_late_arrival_columns()
		data = get_late_arrival(filters, user)

	if filters.get("report_type") == "Early Leavers":
		columns = get_early_leavers_columns()
		data = get_early_leavers(filters, user)

	if filters.get("report_type") == "Check In/Out Missing":
		columns = get_check_in_out_columns()
		data = get_check_in_out(filters, user)

	if filters.get("report_type") == "Pending Attendance Requests":
		columns = get_pending_attendance_requests_columns()
		data = get_pending_attendance_requests(filters, user)
	
	if filters.get("report_type") == "Pending Leaves":
		columns = get_pending_leaves_columns()
		data = get_pending_leaves(filters, user)
	
	if filters.get("report_type") == "Approved Leaves":
		columns = get_approved_leaves_columns()
		data = get_approved_leaves(filters, user)

# Not Applicable	
	# if filters.get("report_type") == "Pending Comp Off Requests":
	# 	columns = get_pending_comp_off_requests_columns()
	# 	data = get_pending_comp_off_requests(filters, user)

	# if filters.get("report_type") == "Approved Comp Off":
	# 	columns = get_approved_comp_off_columns()
	# 	data = get_approved_comp_off(filters, user)
		
	
	return columns, data


# Absentees @@@
def get_absentess_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Gender") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("Region") + ":Data:120",
		_("Status") + ":Data:120",
		_("Attendance Date") + ":Date:120",
	]
# 
def get_absentees(filters, user):
	conditions = get_attendance_condition(filters)
	
	if "HR Manager" in frappe.get_roles(user):
		# Query string
		absent_query = """ SELECT employee, employee_name, custom_gender, custom_designation, department, custom_region, status, attendance_date FROM `tabAttendance` att
                	WHERE docstatus=1 and status='Absent'  {condition}  order by attendance_date desc""".format(condition = conditions)
		# Database
		absent_result = frappe.db.sql(absent_query, filters)
	else:
		absent_query = """SELECT att.employee, att.employee_name, custom_gender, att.custom_designation, att.department, att.custom_region, att.status, att.attendance_date FROM `tabAttendance` att, `tabUser Permission` per 
        		WHERE att.docstatus=1 and att.status='Absent' and per.allow ='Employee' 
				and per.user = '{id}' and att.employee = per.for_value  {condition}
				order by att.attendance_date desc """.format(id =user , condition = conditions)
		absent_result = frappe.db.sql(absent_query, filters)
    
	return absent_result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


 
# Late Arrivals @@@
def get_late_arrival_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("Branch") + ":Data:120",
		_("Shift Check In") + ":Data:150",
		_("Check In") + ":Data:120",
		_("Late Entry Time") + ":Data:150",
		_("Check In Status") + ":Data:150",
		_("Status") + ":Data:120",
		_("Attendance Date") + ":HTML:120",

	]
# 
def get_late_arrival(filters, user):
	
	conditions = ""
	if filters.get("company"):
		conditions += " and att.company = %(company)s"
	if filters.get("employee"):
		conditions += " AND att.employee = %(employee)s"
	if filters.get("branch"):
		conditions += " AND att.custom_branch = %(branch)s"
	if filters.get("department"):
		conditions += " AND att.department = %(department)s"
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and att.attendance_date BETWEEN %(from_date)s AND %(to_date)s"

	holiday_exclusion = """
		AND att.attendance_date NOT IN (
			SELECT h.holiday_date
			FROM `tabHoliday` h
			INNER JOIN `tabHoliday List` hl ON h.parent = hl.name
			INNER JOIN `tabEmployee` emp ON emp.holiday_list = hl.name
			WHERE emp.name = att.employee
		)
	"""
	
	if "HR Manager" in frappe.get_roles(user):
		late_query = f""" SELECT att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_start_time as time) as from_time,  
				cast(att.in_time as time) as check_in_time, TIMEDIFF(cast(att.in_time as time), cast(att.custom_start_time as time)) AS late_entry_time, CASE WHEN att.late_entry = 1 THEN 'Late' WHEN att.late_entry = 0 THEN 'on Time' END AS late_status, att.status, att.attendance_date    
				FROM `tabAttendance` att
				WHERE  docstatus = 1 and late_entry = 1 and att.status = "Present" {conditions} {holiday_exclusion} order by  att.late_entry desc  """
		# Database
		late_arrival_result = frappe.db.sql(late_query, filters, as_dict=True)
	else:
		late_query = """ SELECT att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_start_time as time) as from_time,  
				cast(att.in_time as time) as check_in_time, TIMEDIFF(cast(att.in_time as time), cast(att.custom_start_time as time)) AS late_entry_time, CASE WHEN att.late_entry = 1 THEN 'Late' WHEN att.late_entry = 0 THEN 'on Time' END AS late_status, att.status, att.attendance_date      
				FROM `tabAttendance` att INNER JOIN `tabUser Permission` per ON (att.employee=per.for_value)
				WHERE  att.docstatus = 1 and late_entry = 1 and att.status = "Present" and per.user='{user}' and per.allow='Employee'   {conditions} {holiday_exclusion}
				order by  att.late_entry desc  """
        # Database
		late_arrival_result = frappe.db.sql(late_query, filters, as_dict=True)

	
	
	# Process Results and Add Buttons
	formatted_results = []
	for row in late_arrival_result:
		formatted_row = [
			row.get('employee'),
			row.get('employee_name'),
			row.get('custom_designation'),
			row.get('department'),
			row.get('custom_branch'),
			row.get('from_time'),
			row.get('check_in_time'),
			row.get('late_entry_time'),
			row.get('late_status'),
			row.get('status'),
			create_button(row.get('attendance_date'))
		]
		formatted_results.append(formatted_row)

	return formatted_results

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
 
 
# Early Leavers @@@

def get_early_leavers_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("Branch") + ":Data:120",
		_("Shift Check Out") + ":Data:150",
		_("Check Out") + ":Data:120",
		_("Early Left Time") + ":Data:150",
		_("Check Out Status") + ":Data:150",
		_("Status") + ":Data:120",
		_("Attendance Date") + ":HTML:120",

	]
# 
def get_early_leavers(filters, user):
	
	conditions = ""
	if filters.get("company"):
		conditions += " and att.company = %(company)s"
	if filters.get("employee"):
		conditions += " AND att.employee = %(employee)s"
	if filters.get("branch"):
		conditions += " AND att.custom_branch = %(branch)s"
	if filters.get("department"):
		conditions += " AND att.department = %(department)s"
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and att.attendance_date BETWEEN %(from_date)s AND %(to_date)s"

	holiday_exclusion = """
		AND att.attendance_date NOT IN (
			SELECT h.holiday_date
			FROM `tabHoliday` h
			INNER JOIN `tabHoliday List` hl ON h.parent = hl.name
			INNER JOIN `tabEmployee` emp ON emp.holiday_list = hl.name
			WHERE emp.name = att.employee
		)
	"""
	
	if "HR Manager" in frappe.get_roles(user):
		late_query = f""" SELECT att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_end_time as time) as from_time,  
				cast(att.out_time as time) as check_out_time, TIMEDIFF(cast(att.custom_end_time as time), cast(att.out_time as time)) AS early_left_time, CASE WHEN att.early_exit = 1 THEN 'Early Exit' WHEN att.early_exit = 0 THEN 'on Time' END AS early_exit_status, att.status, att.attendance_date     
				FROM `tabAttendance` att
				WHERE  docstatus = 1 and early_exit = 1 and att.status = "Present" {conditions} {holiday_exclusion} order by  att.early_exit desc  """
		# Database
		early_exit_result = frappe.db.sql(late_query, filters, as_dict=True)
	else:
		late_query = """ SELECT att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_end_time as time) as from_time,  
				cast(att.out_time as time) as check_out_time, TIMEDIFF(cast(att.custom_end_time as time), cast(att.out_time as time)) AS early_left_time, CASE WHEN att.early_exit = 1 THEN 'Early Exit' WHEN att.early_exit = 0 THEN 'on Time' END AS early_exit_status, att.status, att.attendance_date      
				FROM `tabAttendance` att INNER JOIN `tabUser Permission` per ON (att.employee=per.for_value)
				WHERE  att.docstatus = 1 and early_exit = 1 and att.status = "Present" and per.user='{user}' and per.allow='Employee'   {conditions} {holiday_exclusion}
				order by  att.early_exit desc  """
        # Database
		early_exit_result = frappe.db.sql(late_query, filters, as_dict=True)
	
	# Process Results and Add Buttons
	formatted_results = []
	for row in early_exit_result:
		formatted_row = [
			row.get('employee'),
			row.get('employee_name'),
			row.get('custom_designation'),
			row.get('department'),
			row.get('custom_branch'),
			row.get('from_time'),
			row.get('check_out_time'),
			row.get('early_left_time'),
			row.get('early_exit_status'),
			row.get('status'),
			create_button(row.get('attendance_date'))
		]
		formatted_results.append(formatted_row)

	return formatted_results

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

def create_button(date):
    date_str = date.strftime('%Y-%m-%d')
    return f"""
        <button 
        onclick="redirect_to_leave_application('{date_str}')"
        style="
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
            padding: 5px 10px;
            cursor: pointer;
        "
    >
        {date.strftime('%d-%m-%Y')}
    </button>
    """
  
# Early Leavers @@@

def get_check_in_out_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:150",
		_("Designation") + ":Data:150",
		_("Department") + ":Data:150",
		_("Region") + ":Data:120",
		_("Date") + ":Data:120",
		_("Check In/Out") + ":Data:150"
	]

def get_check_in_out(filters, user):

	conditions = ""
	if filters.get("company"):
		conditions += " and att.company = %(company)s"
	if filters.get("employee"):
		conditions += " AND att.employee = %(employee)s"
	if filters.get("branch"):
		conditions += " AND att.custom_branch = %(branch)s"
	if filters.get("department"):
		conditions += " AND att.department = %(department)s"
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and att.attendance_date BETWEEN %(from_date)s AND %(to_date)s"

	holiday_exclusion = """
		AND att.attendance_date NOT IN (
			SELECT h.holiday_date
			FROM `tabHoliday` h
			INNER JOIN `tabHoliday List` hl ON h.parent = hl.name
			INNER JOIN `tabEmployee` emp ON emp.holiday_list = hl.name
			WHERE emp.name = att.employee
		)
	"""
        
	if "HR Manager" in frappe.get_roles(user):
		query=f""" SELECT  employee, employee_name, custom_designation, department, custom_region, attendance_date,
            (case
				when  in_time is null and out_time is null then 'Check In/Out Missed'
				when in_time is null then 'Check In Missed'
				when out_time is null then 'Check Out Missed'
				else 'On Time' 
			end) as in_out
            FROM `tabAttendance` att
            WHERE docstatus=1 and status='Present' and (in_time is null or out_time is null) {conditions} {holiday_exclusion}
            order by employee_name
             """
		result = frappe.db.sql(query, filters, as_dict=0)
	else:
		query=""" SELECT  att.employee, att.employee_name, att.custom_designation, att.department, att.custom_region, att.attendance_date,
            (case
				when  in_time is null and out_time is null then 'Check In/Out Missed'
				when in_time is null then 'Check In Missed'
				when out_time is null then 'Check Out Missed'
				else 'On Time' 
			end) as in_out
            FROM `tabAttendance` att,   `tabUser Permission` per
            WHERE att.docstatus=1 and status='Present' and (in_time is null or out_time is null)
            and att.employee=per.for_value and per.user='{user}' and per.allow='Employee' 
            {conditions} {holiday_exclusion}
            order by att.employee_name  """
		result = frappe.db.sql(query, filters, as_dict=0)
	return result

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# ---Pending Attendance Requests @@@
def get_pending_attendance_requests_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Department") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Region") + ":Data:120",
		_("From Time") + ":Data:120",
		_("To Time") + ":Data:120",
		_("From Date") + ":Data:120",
		_("Feedback") + ":Data:220",
		_("Status") + ":Data:220",
	]

def get_pending_attendance_requests(filters, user):
    
	conditions = ""
	if filters.get("company"):
		conditions += " and lr.company = %(company)s"
	if filters.get("employee"):
		conditions += " AND lr.employee = %(employee)s"
	if filters.get("branch"):
		conditions += " AND lr.custom_branch = %(branch)s"
	if filters.get("department"):
		conditions += " AND lr.department = %(department)s"
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and lr.from_date BETWEEN %(from_date)s AND %(to_date)s"

	if "HR Manager" in frappe.get_roles(user):
		query =""" 
                SELECT lr.employee, lr.employee_name, lr.department, lr.designation, lr.custom_region, 
                cast(lr.custom_from as time) as from_time, cast(lr.custom_to as time) as to_time, lr.from_date, lr.reason, lr.custom_approval_status
                FROM `tabAttendance Request` lr
                WHERE lr.docstatus = 0 {condition}
                order by to_date desc  """.format(condition = conditions)
        # Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
    			SELECT lr.employee, lr.employee_name, lr.department, lr.designation, lr.custom_region, cast(lr.custom_from as time) as from_time, cast(lr.custom_to as time) as to_time, lr.from_date, lr.reason, lr.custom_approval_status
        		FROM `tabAttendance Request` lr, `tabUser Permission` per
        		WHERE lr.docstatus = 0 and lr.employee = per.for_value  and per.user='{id}' and per.allow='Employee'  {condition}
        		order by to_date desc  """.format(id=user, condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	return result

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# Pending Leaves @@@
def get_pending_leaves_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Leave Type") + ":Data:120",
		_("Department") + ":Data:120",
		_("Designation") + ":Data:120",
		_("From Date") + ":Data:120",
		_("To Date") + ":Data:120",
		_("Total Leave Days") + ":Data:120",
		_("Status") + ":Data:120",
	]
# 
def get_pending_leaves(filters, user):

	conditions = get_leave_condition(filters)
	if "HR Manager" in frappe.get_roles(user):
		query =""" 
                SELECT 
                	employee, employee_name, leave_type, department, custom_designation, 
					from_date, to_date, total_leave_days, status 
                FROM `tabLeave Application` 
                WHERE  docstatus = 0 and status='Open' {condition}
                order by total_leave_days desc  """.format(condition = conditions)
    	# Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
            SELECT la.employee, la.employee_name, la.leave_type, la.department, la.custom_designation, la.from_date, la.to_date, la.total_leave_days, la.status 
            FROM `tabLeave Application` la, `tabUser Permission` per  
            WHERE  la.docstatus = 0 and la.status='Open' and la.employee = per.for_value  and per.user='{id}' and per.allow='Employee' {condition}
            order by la.total_leave_days desc  """.format(id=user,condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	return result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# ---Approved Leaves @@@
def get_approved_leaves_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Department") + ":Data:120",
		_("Designation") + ":Data:120",
		_("From Date") + ":Data:120",
		_("To Date") + ":Data:120",
		_("Total Leave Days") + ":Data:120",
		_("Leave Type") + ":Data:120",
	]

def get_approved_leaves(filters, user):
	conditions = get_leave_condition(filters)
	if "HR Manager" in frappe.get_roles(user):
		query =""" 
				SELECT 
    				employee, employee_name, department, custom_designation, 
					from_date, to_date, total_leave_days, leave_type
				FROM `tabLeave Application`
				WHERE docstatus= 1 and status='Approved' {condition}  
				order by posting_date desc  """.format(condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
                SELECT la.employee, la.employee_name, la.department, la.custom_designation, la.from_date,la.to_date, la.total_leave_days, la.leave_type
                FROM `tabLeave Application` la, `tabUser Permission` per
                WHERE la.docstatus= 1 and la.status='Approved' 
                and la.employee=per.for_value and per.user='{id}' and per.allow='Employee'
                {condition}
                order by la.posting_date desc  """.format(id=user, condition = conditions)
		result = frappe.db.sql(query, filters)
	return result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


#---Processing-Ending---##############################################################

###########################################
# Filter data condtions
def get_attendance_condition(filters):
    conditions = ""
    if filters.get("company"):
        conditions += " and att.company = %(company)s"
    if filters.get("employee"):
        conditions += " AND att.employee = %(employee)s"
    if filters.get("branch"):
        conditions += " AND att.custom_branch = %(branch)s"
    if filters.get("department"):
        conditions += " AND att.department = %(department)s"
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " and att.attendance_date BETWEEN %(from_date)s AND %(to_date)s"
    
    return conditions  

# Filter data conditions
def get_leave_condition(filters):
    conditions = ""
    if filters.get("company"):
        conditions += " and company = %(company)s"
    if filters.get("employee"):
        conditions += " AND employee = %(employee)s"
    if filters.get("branch"):
        conditions += " AND custom_branch = %(branch)s"
    if filters.get("department"):
        conditions += " AND department = %(department)s"
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " and from_date BETWEEN %(from_date)s AND %(to_date)s"
    
    return conditions  





# ---Pending Comp Off Requests @@@
def get_pending_comp_off_requests_columns():
	return [
		_("Employee Code") + ":Data:120",
		_("Employee name") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("From Time") + ":Data:120",
		_("To Time") + ":Data:120",
		_("Applying Hours") + ":Data:120",
		_("Total Comp Off Balance") + ":Data:120",
		_("Feedback/Status") + ":Data:120",
	]
# 
def get_pending_comp_off_requests(filters, user):
	conditions = get_leave_condition(filters)
	if "HR Manager" in frappe.get_roles(user):
		query =""" 
        		SELECT comp.employeecode, comp.employee_name, comp.designation, comp.department, comp.applying_date, 
        		cast(comp.work_from as time) as work_from, cast(comp.work_to as time) as work_to, comp.applying_hours, comp.total_comp_off_balance, comp.status
        		FROM `tabComp Off` comp
        		WHERE comp.docstatus = 0 and comp.leave_type = 'Regular'
    			{condition}  
        		order by comp.posting_date desc  """.format(condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
            	SELECT comp.employeecode, comp.employee_name, comp.designation, comp.department, comp.applying_date, 
            	cast(comp.work_from as time) as work_from, cast(comp.work_to as time) as work_to, comp.applying_hours, comp.total_comp_off_balance, comp.status
            	FROM `tabComp Off` comp, `tabUser Permission` per
            	WHERE comp.docstatus = 0 and comp.leave_type = 'Regular' 
            	and comp.employee=per.for_value and per.user='{id}' and per.allow='Employee'
            	{condition}
            	order by posting_date desc  """.format(id=user, condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	return result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# Approved Comp Off @@@
def get_approved_comp_off_columns():
	return [
		_("Employee Code") + ":Data:120",
		_("Employee name") + ":Data:120",
		_("Designation") + ":/Department:120",
		_("Department") + ":Data:120",
		_("From Time") + ":Data:120",
		_("To Time") + ":Data:120",
		_("Applying Hours") + ":Data:120",
		_("Total Comp Off Balance") + ":Data:120",
		_("Feedback/Status") + ":Data:120",
	]

def get_approved_comp_off(filters, user):
	conditions = get_leave_condition(filters)
	if "HR Manager" in frappe.get_roles(user):
		query =""" 
        		SELECT employeecode, employee_name, designation, department, cast(work_from as time) as work_from, cast(work_to as time) as work_to, applying_hours,total_comp_off_balance, status 
        		FROM `tabComp Off`
        		WHERE docstatus=1 and leave_type = 'Regular' {condition}
        		order by work_from, work_to  """.format(condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
				SELECT comp.employeecode, comp.employee_name, comp.designation, comp.department, cast(comp.work_from as time) as work_from, cast(comp.work_to as time) as work_to, comp.applying_hours,comp.total_comp_off_balance, comp.status 
            	FROM `tabComp Off` comp, `tabUser Permission` per
            	WHERE comp.docstatus=1 and comp.leave_type = 'Regular' 
            	and comp.employee=per.for_value and per.user='{id}' and per.allow='Employee' 
            	{condition}
            	order by work_from, work_to  """.format(id=user, condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	return result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
