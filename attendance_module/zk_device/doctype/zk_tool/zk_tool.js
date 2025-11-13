// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt
let msg = ``;
var logs = {};
frappe.ui.form.on("ZK Tool", {
	onload(frm){
		// frappe.realtime.off("attendance_marked_successfully");
		frappe.realtime.on("attendance_marked_successfully", function(data) {
			console.log("data");
			console.log(data);
			// frm.reload_doc();
		});
	},
    refresh(frm) {
        set_queries(frm);
        frm.set_value("fetched", 0);
		// 
		// check_zkteco_machine_status(frm);
		// activate_live_attendance_service(frm);
    },
    company: function (frm) {
        get_company_details(frm);
    },
    log_type: function (frm) {
		get_company_details(frm);
	},
	get_employees: function (frm) {
		let d = progress_message_dialog("Getting employees!");
		frm.call("get_employees", {
		}).then(r => {
			$(d.$wrapper).find('.change_message').empty();
			$(d.$wrapper).find('.change_message').html(`
					<small class="" style="margin-right: 20px;
					font-style: italic;
					font-family: monospace;
					font-weight: bold;">Employees found!</small>
					<i class="fa fa-smile-o" style="font-size:30px; color: green;"></i>
				`);
				
				setInterval(() => {
					d.hide();
				}, 6000);
		});
	},
	fetch_attendance: function (frm) {
		let d = progress_message_dialog("Fetching Attendance!");
		var start = new Date();
		frm.call('fetch_attendance', {})
			.then(r => {
				let data = r.message;
				logs = data.logs;
				console.log(data);
				frm.set_value("fetched", data.fetched);
				var end = new Date();
				const total_time = calculate_process_time(start, end);
				$(d.$wrapper).find('.change_message').empty();
				$(d.$wrapper).find('.change_message').html(`
						<small class="" style="margin-right: 20px;
						font-style: italic;
						font-family: monospace;
						font-weight: bold;">${data.msg}</small>
						<i class="fa fa-smile-o" style="font-size:30px; color: green;"></i>
						<br>
						<p>${total_time}</p>
					`);
				setInterval(() => {
					d.hide();	
				}, 10000);
			});
	},
	mark_attendance: function (frm) {
		if (logs != null) {
			// var start = new Date();
			// let d = progress_message_dialog("Marking attendance!");
			let employees_list = frm.doc.employee_list;
			frm.call('mark_attendance', {
				employees: employees_list, logs: logs
			}).then(r => {
					console.log(r.message);
					/*
					const data = r.message;
					
					let msg = (data.marked == true)? "Attendance marked!": "Attendance already marked!"
					var end = new Date();
					const total_time = calculate_process_time(start, end);
					
					$(d.$wrapper).find('.change_message').empty();
					$(d.$wrapper).find('.show_progress').empty();
					$(d.$wrapper).find('.change_message').html(`
							<small class="" style="margin-right: 20px;
							font-style: italic;
							font-family: monospace;
							font-weight: bold;">${msg}</small>
							<i class="fa fa-smile-o" style="font-size:30px; color: green;"></i>
							<br>
							<p>${total_time}</p>
						`);
					setInterval(() => {
							d.hide();	
						}, 10000);
					*/
				
			});
			
		} else {
			frappe.msgprint(`Logs not found please fetch first from machine.`)
		}
	},
});


function set_queries(frm) {
	frm.set_query('branch', function () {
		return {
			filters: {
				// 'company': frm.doc.company,
			}
		}
	});
	frm.set_query('department', function () {
		return {
			filters: {
				'is_group': 0,
				'disabled': 0,
				'company': frm.doc.company,
			}
		}
	});
	frm.set_query('designation', function () {
		return {
			filters: {
				// 'company': frm.doc.company
			}
		}
	});
	frm.set_query('employee', function () {
		return {
			filters: {
				'status': 'Active',
				'company': frm.doc.company,
				'department': frm.doc.department,
				'designation': frm.doc.designation
			}
		}
	});

	frm.set_query('employee', 'employee_list', function () {
		return {
			filters: {
				'status': 'Active',
				'company': frm.doc.company
			}
		}
	});
}

function get_company_details(frm) {
	if (frm.doc.company) {
		logs = {};
		frm.set_value("fetched", 0);
		frm.call('get_company_details', {
			throw_if_missing: true, freeze: true,
		}).then(r => {
			if (r.message) {
				// let linked_doc = r.message;
			}
		});
	} else {
		frm.set_value("ip_address", "")
		frm.set_value("port", "")
	}
}

// Listening to event published on server side
function progress_message_dialog(msg){
	let d = new frappe.ui.Dialog({
		title: 'add message',
		fields: [
			{
				label: '',
				fieldname: 'show_msg',
				fieldtype: 'HTML',
				options: `
				<div class="row">
					<div class="col-xs-12 change_message">
						<small class="" style="margin-right: 20px;
						font-style: italic;
						font-family: monospace;
						font-weight: bold;">${msg}</small>
						<i class="fa fa-spinner fa-spin" style="font-size:30px; color: blue;"></i>
					</div>
					<div class="col-xs-12 show_progress">
					</div>
				</div>`
			},
		],
		size: 'small', // small, large, extra-large 
		primary_action_label: 'Fetch',
		primary_action(values) {
			// console.log(values);
			d.hide();
		}
	});
	d.show();
	// Hide the buttons (if you prefer to hide them entirely)
	$(d.$wrapper).find('.modal-header').hide();
	$(d.$wrapper).find('.btn-modal-close').hide();
	$(d.$wrapper).find('.btn-primary').hide();
	return d;
}

function calculate_process_time(start, end){
	var diffMs = end - start;
	var diffHrs = Math.floor((diffMs % 86400000) / 3600000); // 3600000 ms in an hour
	var diffMins = Math.floor(((diffMs % 86400000) % 3600000) / 60000); // 60000 ms in a minute
	var diffSecs = Math.floor((((diffMs % 86400000) % 3600000) % 60000) / 1000); // seconds
	return `${diffHrs} hours:${diffMins} minutes: ${diffSecs} seconds`;
}

function check_zkteco_machine_status(frm){
	// frm.add_custom_button(__("Machine Status"), function(){
	// 	//perform desired action such as routing to new form or fetching etc.
	//   }, __("ZKTeco"));
}

function activate_live_attendance_service(frm){
	frm.add_custom_button(__("Activate Live Serivce"), function(){
		//perform desired action such as routing to new form or fetching etc.
		frappe.call({
			method: "akf_hrms.zk_device.doctype.zk_tool.zk_tool.activate_live_attendance_service",
			callback: function(r){
				console.log(r.message);
				// frappe.msgprint(r.message);
			}
		})
	  }, __("ZKTeco"));
}