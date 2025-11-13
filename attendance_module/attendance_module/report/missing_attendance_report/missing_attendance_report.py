# Developer Mubashir Bashir

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import timedelta

def execute(filters=None):
    columns, data = [], []
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        _("Employee") + ":Link/Employee:180",
        _("Employee Name") + "::180",
        _("Department") + ":Link/Department:150",
        _("Designation") + ":Link/Designation:150",
        _("Branch") + ":Link/Branch:150",
        _("Employment Type") + ":Link/Employment Type:150",
        _("Grade") + "::150",
        _("Region") + "::150",
        _("Missing Attendance Dates") + ":HTML:250",
        _("Check In/Out Missing") + "::250",
        _("Check In/Out Time") + "::250"
    ]

def get_data(filters):
    return_list = []
    conditions, filters = get_conditions(filters)

    get_employee = frappe.db.sql(f"""
        SELECT name, employee_name, department, designation, branch, employment_type, grade, custom_region, holiday_list
        FROM `tabEmployee`
        WHERE custom_no_attendance = 0
        AND status = 'Active'
        {conditions}
    """, filters, as_dict=1)

    for emp in get_employee:
        
        attendance_dates = frappe.db.sql(f"""
            SELECT attendance_date, in_time, out_time, custom_in_times, custom_out_times
            FROM `tabAttendance` 
            WHERE employee = %(employee)s 
            AND attendance_date BETWEEN %(from_date)s AND %(to_date)s
            AND docstatus = 1
            AND ((custom_in_times IS NULL AND custom_out_times IS NOT NULL) OR (custom_out_times IS NULL AND custom_in_times IS NOT NULL))
            AND status IN ('Present', 'Half Day', 'Work From Home')
        """, {"employee": emp.get("name"), "from_date": filters.get("from_date"), "to_date": filters.get("to_date")}, as_dict=1)

        if attendance_dates:
            first_row_added = False
            for attendance in attendance_dates:
                attendance_date = create_button(attendance['attendance_date'])
                if attendance['custom_in_times'] is None and attendance['custom_out_times'] is not None:
                    missing_type = 'Check In Missing'
                    check_in_out_times = attendance['custom_out_times']
                elif attendance['custom_out_times'] is None and attendance['custom_in_times'] is not None:
                    missing_type = 'Check Out Missing'
                    check_in_out_times = attendance['custom_in_times']
                else:
                    missing_type = ''
                    check_in_out_times = ''

                if not first_row_added:
                    first_row = [
                        emp.get("name"),
                        emp.get("employee_name"),
                        emp.get("department"),
                        emp.get("designation"),
                        emp.get("branch"),
                        emp.get("employment_type"),
                        emp.get("grade"),
                        emp.get("custom_region"),
                        attendance_date,
                        missing_type,
                        check_in_out_times
                    ]
                    return_list.append(first_row)
                    first_row_added = True
                else:
                    return_list.append(['-', '-', '-', '-', '-', '-', '-', '-', attendance_date, missing_type, check_in_out_times])

    return return_list


def get_conditions(filters):
    conditions = ""
    if filters.get("company"):
        conditions += " AND company = %(company)s"
    if filters.get("employee"):
        conditions += " AND name = %(employee)s"
    if filters.get("branch"):
        conditions += " AND branch = %(branch)s"
    if filters.get("department"):
        conditions += " AND department = %(department)s"

    return conditions, filters

def create_button(date):
    date_str = date.strftime('%Y-%m-%d')
    return f"""
        <button 
        onclick="redirect_to_attendance_request('{date_str}')"
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