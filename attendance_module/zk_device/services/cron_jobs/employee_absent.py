from __future__ import unicode_literals
import frappe
from datetime import datetime

@frappe.whitelist()
def send_absent_employee_notification():
    absent_employees = frappe.db.sql("""
        SELECT 
            att.employee,
            att.employee_name,
            emp.department,
            emp.designation,
            GROUP_CONCAT(att.attendance_date ORDER BY att.attendance_date DESC LIMIT 3) AS absent_dates,
            COUNT(*) AS absent_days,
            (SELECT e.user_id FROM `tabEmployee` AS e WHERE e.employee = emp.reports_to) AS reports_to,            
            emp.user_id
        FROM 
            `tabAttendance` att
        INNER JOIN
            `tabEmployee` emp ON att.employee = emp.employee
        WHERE 
            att.status = 'Absent'
        GROUP BY 
            att.employee
        HAVING 
            COUNT(*) >= 3
    """, as_dict=True)
     
    # Email template
    if absent_employees:
        for employee in absent_employees:
            if employee.reports_to:
                # Email subject
                email_subject = f"Notification of the Absence of Employee: {employee.employee_name} {employee.employee}"
                # Construct HTML content for the current employee
                table_header_absentees = """
                    <p>Dear Concerned,</p>
                    <p>This email is to notify that {} is Absent consecutively for the last 03 days. The details are as under.</p>
                    <table class="table table-bordered" style="border: 2px solid black; background-color: #f6151;">
                        <thead style="background-color: #0b4d80; color: white; text-align: left;">
                        <tr>
                            <th style="border: 1px solid black;">Employee ID</th>
                            <th style="border: 1px solid black;">Employee Name</th>
                            <th style="border: 1px solid black;">Department</th>
                            <th style="border: 1px solid black;">Designation</th>
                            <th style="border: 1px solid black;">Absent Dates</th>
                            <th style="border: 1px solid black;">Absent Days</th>
                        </tr>
                        </thead>
                        <tbody>
                """.format(employee.employee_name)
                
                # Formatting for Absent Dates and Absent Days
                absent_dates = employee.absent_dates.split(',')
                absent_dates_formatted = [datetime.strptime(date_str, '%Y-%m-%d').strftime('%d %B, %Y') for date_str in absent_dates]
                absent_day_names = [datetime.strptime(date_str, '%Y-%m-%d').strftime('%A') for date_str in absent_dates]
                absent_days_str = ', '.join(absent_day_names)
                absent_dates_str = ', '.join(absent_dates_formatted)
                
                # Construct HTML row for the current employee
                employee_row = """
                    <tr style="background-color: #d1e0e4; text-align: left;">
                        <td class="text-left" style="border: 1px solid black;">{}</td>
                        <td class="text-left" style="border: 1px solid black;">{}</td>
                        <td class="text-left" style="border: 1px solid black;">{}</td>
                        <td class="text-left" style="border: 1px solid black;">{}</td>
                        <td class="text-left" style="border: 1px solid black;">{}</td>
                        <td class="text-left" style="border: 1px solid black;">{}</td>
                    </tr>
                """.format(
                    employee.get('employee', ''), 
                    employee.get('employee_name', ''), 
                    employee.get('department', ''), 
                    employee.get('designation', ''), 
                    absent_dates_str, 
                    absent_days_str
                )
                
                table_closing_tags = "</tbody></table><br><p>The email is routed for any further necessary action please.</p>"
                
                html_content = table_header_absentees + employee_row + table_closing_tags

                # Get the email of the reporting manager
                recipients = []

                # Adding employee's email
                if employee.get('user_id'):
                    recipients.append(employee.get('user_id'))

                # Add reporting manager's email

                reports_to_email = frappe.db.get_value("Employee", {"user_id": employee.reports_to}, "user_id")
                recipients.append(reports_to_email)

                # Add HR manager's email
                hr_manager_email = frappe.db.sql("""
                    SELECT u.email 
                    FROM `tabUser` AS u 
                    INNER JOIN `tabHas Role` AS h ON (u.name = h.parent) 
                    WHERE u.name NOT IN ("Administrator") 
                    AND h.role = 'HR Manager' 
                    GROUP BY u.name
                """, as_dict=False)

                recipients.extend([row[0] for row in hr_manager_email])

                # Send email to all recipients
                frappe.sendmail(
                    recipients=recipients,
                    subject=email_subject,
                    message=html_content
                )