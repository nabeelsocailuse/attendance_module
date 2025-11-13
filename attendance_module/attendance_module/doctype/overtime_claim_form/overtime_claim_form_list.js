frappe.listview_settings['Overtime Claim Form'] = {
	add_fields: ["approval_status"],
	get_indicator(doc) {
		const status_colors = {
			"Draft": "grey",
			"Pending": "grey",
			"Approved by the Head of Department": "green",
			"Approved by the CEO": "green",
			"Rejected by the Head of Department": "gray",
			"Rejected by the CEO": "gray",
			"Cancelled": "red",
		};
		return [__(doc.approval_status), status_colors[doc.approval_status], "approval_status,=,"+doc.approval_status];
	},
};
