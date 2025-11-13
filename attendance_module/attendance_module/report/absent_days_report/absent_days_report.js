// Developer Mubashir Bashir

frappe.query_reports["Absent Days Report"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			// "reqd": 1
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
			"options": "Department"
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": get_default_from_date(),
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": get_default_to_date(),
			"reqd": 1
		}
	],

	onload: function(report) {
		if (frappe.user.has_role("Employee")) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Employee",
					fieldname: ["name", "branch", "department"],
					filters: { user_id: frappe.session.user }
				},
				callback: function(response) {
					if (response && response.message) {
						const employee_id = response.message.name;
						const branch = response.message.branch;
						const department = response.message.department;

						report.set_filter_value("employee", employee_id);
						if (branch) {
							report.set_filter_value("branch", branch);
						}
						if (department) {
							report.set_filter_value("department", department);
						}
					}
				}
			});
		}
	}
};


function get_default_from_date() {
	const today = new Date();
	const day = today.getDate();
	const month = today.getMonth();
	const year = today.getFullYear();

	let from_date;

	if (day > 20) {
		from_date = new Date(year, month, 22).toISOString().split("T")[0];
	} else {
		from_date = new Date(year, month - 1, 22).toISOString().split("T")[0];
	}

	console.log("Calculated from_date:", from_date);
	return from_date;
}

function get_default_to_date() {
	const today = new Date();
	const day = today.getDate();
	const month = today.getMonth();
	const year = today.getFullYear();

	let to_date;

	if (day > 20) {
		to_date = new Date(year, month + 1, 21).toISOString().split("T")[0];
	} else {
		to_date = new Date(year, month, 21).toISOString().split("T")[0];
	}

	console.log("Calculated to_date:", to_date);
	return to_date;
}

function redirect_to_leave_application(absent_date) {
    frappe.new_doc("Leave Application", {}, function(doc) {
        frappe.model.set_value(doc.doctype, doc.name, "from_date", absent_date);
        frappe.model.set_value(doc.doctype, doc.name, "to_date", absent_date);
        cur_frm.refresh_field("from_date");
        cur_frm.refresh_field("to_date");
    });
}