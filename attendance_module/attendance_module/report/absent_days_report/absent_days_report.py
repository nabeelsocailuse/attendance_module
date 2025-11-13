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
        _("Absent Days") + ":HTML:250"
    ]

def get_data(filters):
    return_list = []
    conditions, filters = get_conditions(filters)

    get_employee = frappe.db.sql(f"""
        SELECT name, employee_name, department, designation, branch, employment_type, grade, custom_region, holiday_list, date_of_joining
        FROM `tabEmployee`
        WHERE custom_no_attendance = 0
        AND status = 'Active'
        {conditions}
    """, filters, as_dict=1)

    from_date = frappe.utils.getdate(filters.get("from_date"))
    to_date = frappe.utils.getdate(filters.get("to_date"))

    for emp in get_employee:
        if emp.date_of_joining and emp.date_of_joining > from_date:
            from_date = emp.date_of_joining
        
        attendance_dates = frappe.db.sql(f"""
            SELECT attendance_date 
            FROM `tabAttendance` 
            WHERE employee = %(employee)s 
            AND attendance_date BETWEEN %(from_date)s AND %(to_date)s
            AND docstatus = 1
        """, {"employee": emp.get("name"), "from_date": from_date, "to_date": to_date}, as_dict=1)
        # """, {"employee": emp.get("name"), "from_date": filters.get("from_date"), "to_date": filters.get("to_date")}, as_dict=1)

        attendance_dates_set = {d['attendance_date'].strftime('%Y-%m-%d') for d in attendance_dates}

        # from_date = frappe.utils.getdate(filters.get("from_date"))
        # to_date = frappe.utils.getdate(filters.get("to_date"))
        
        all_dates = []
        current_date = from_date
        while current_date <= to_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)

        holiday_dates = frappe.db.sql(f"""
            SELECT holiday_date 
            FROM `tabHoliday`
            WHERE parent = %(holiday_list)s
            AND holiday_date BETWEEN %(from_date)s AND %(to_date)s
        """, {"holiday_list": emp.get("holiday_list"), "from_date": filters.get("from_date"), "to_date": filters.get("to_date")}, as_dict=1)
        
        holiday_dates_set = {h['holiday_date'].strftime('%Y-%m-%d') for h in holiday_dates}

        missing_dates = [
            d for d in all_dates 
            if d.strftime('%Y-%m-%d') not in attendance_dates_set
            and d.strftime('%Y-%m-%d') not in holiday_dates_set
        ]

        if missing_dates:
            first_row = [
                emp.get("name"),
                emp.get("employee_name"),
                emp.get("department"),
                emp.get("designation"),
                emp.get("branch"),
                emp.get("employment_type"),
                emp.get("grade"),
                emp.get("custom_region"),
                create_button(missing_dates[0]) 
            ]
            return_list.append(first_row)

            for missing_date in missing_dates[1:]:
                return_list.append(['-', '-', '-', '-', '-', '-', '-', '-', create_button(missing_date)])

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