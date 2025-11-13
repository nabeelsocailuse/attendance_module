// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["In Out Timing Report"] = {
	"filters": [
		{
			"fieldname":"month",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": "Jan\nFeb\nMar\nApr\nMay\nJun\nJul\nAug\nSep\nOct\nNov\nDec",
			"default": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
				"Dec"][frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth()],
			"hidden": 1
		},
		{
			"fieldname":"year",
			"label": __("Year"),
			"fieldtype": "Select",
			//"reqd": 1,
			"hidden": 1
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_start(),
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"get_query": function() {
				var company = frappe.query_report.get_filter_value('company');
				return {
					"doctype": "Employee",
					"filters": {
						"status": "Active",
						"company": company,
					}
				}
			}
		},
		{
			"fieldname":"branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch"
		},
		{
			"fieldname":"department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"get_query": function() {
				var company = frappe.query_report.get_filter_value('company');
				return {
					"doctype": "Department",
					"filters": {
						"is_group": 0,
						"disabled": 0,
						"company": company,
					}
				}
			}
		},
		{
			"fieldname":"designation",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation"
		},		
	],
	"onload": function(frm) {
		// Set years
		frappe.call({
			method: "hrms.hr.report.monthly_attendance_sheet.monthly_attendance_sheet.get_attendance_years",
			callback: function(r) {
				var year_filter = frappe.query_report.get_filter('year');
				year_filter.df.options = r.message;
				year_filter.df.default = r.message.split("\n")[0];
				year_filter.refresh();
				year_filter.set_input(year_filter.df.default);
			}
		});

		// Set current user's employee ID
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Employee",
				filters: {
					"user_id": frappe.session.user
				},
				fields: ["name"]
			},
			callback: function(r) {
				if (r.message && r.message.length > 0) {
					var employee_filter = frappe.query_report.get_filter('employee');
					employee_filter.df.default = r.message[0].name;
					employee_filter.refresh();
					employee_filter.set_input(r.message[0].name);
				}
			}
		});
	}
};
