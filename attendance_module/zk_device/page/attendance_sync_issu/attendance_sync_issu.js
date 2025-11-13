frappe.pages['attendance-sync-issu'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Attendance Sync Issue Dashboard',
		single_column: true
	});
	// design.loadDesign(page);
	api.loadRealTimeInformation(page, {});
}
const api = {
	loadRealTimeInformation: function (page, filters) {
		frappe.call({
			method: 'attendance_module.zk_device.page.attendance_sync_issu.device_status.get_device_status',
			// method: 'attendance_module.zk_device.page.attendance_sync_issu.device_status_multi_files.get_device_status',
			args: {
				filters: JSON.stringify(filters)
			},
			freeze: true,
			freeze_message: "Fetching device statuses...",
			callback: function (r) {
				console.log(r.message);
				
				design.loadDesign(page, r.message);
				// // Show Print and Refresh buttons once the employee record is being shown.
				// if (filters.employee) {
				// 	page.fields_dict.print.$wrapper.show();
				// 	page.fields_dict.refresh.$wrapper.show();
				// } else {
				// 	page.fields_dict.print.$wrapper.hide();
				// 	page.fields_dict.refresh.$wrapper.hide();
				// }
			}
		});
	}
};

const design = {
	loadDesign: function (page, info) {
		$(".employee").remove();
		const content = frappe.render_template("attendance_sync_issu", info);
		$(content).appendTo(page.main);
	}
};