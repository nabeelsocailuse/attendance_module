// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime Claim Form", {
	
	refresh(frm) {
		acf.set_queries(frm);
		acf.employee_info(frm);
		frm.trigger("showWorkFlowState");
	},
	year: function (frm) {
		acf.load_details_of_overtime(frm, {reset: true});
	},
	month: function (frm) {
		acf.load_details_of_overtime(frm, {reset: true});
	},
	employee: function (frm) {
		acf.employee_info(frm);
		acf.load_details_of_overtime(frm, {reset: true});
	},
	showWorkFlowState: function(frm){
		if(frm.doc.tracking_information==undefined) {
			frm.set_df_property('tracking_html', 'options', '<p></p>')
		}else{
			const stateObj = JSON.parse(frm.doc.tracking_information)
			let rows = ``;
			let idx = 1
			// for (const data of orderedStates) {
            for (const data of stateObj) {
				const dt = moment(data.modified_on).format("DD-MM-YYYY hh:mm:ss a");
				rows += `
				<tr>
					<th scope="row">${idx}</th>	
					<td scope="row">${data.employee_name}</td>
					<td scope="row">${data.current_state}</td>
					<td class="">${dt}</td>
					<td class="">${data.next_state}</td>
					
				</tr>`;
				idx += 1;
			}
			let _html_ = `
			<table class="table">
				<thead class="thead-dark">
					<tr>
					<th scope="col">#</th>
					<th class="text-left" scope="col">Employee Name</th>
					<th class="text-left" scope="col">Current State</th>
					<th class="text-left" scope="col">DateTime</th>
					<th scope="col">Next State(Employee Name, Role)</th>
					</tr>
				</thead>
				<tbody>
					${rows}
				</tbody>
			</table>`;
			frm.set_df_property('tracking_html', 'options', _html_)
		}
	},
});

// COMMENTS
acf = {
	set_queries: function (frm) {
		frm.set_query("employee", function () {
			return {
				filters: {
					"custom_overtime_allowed": 1,
				}
			}
		})
	},
	employee_info: function (frm) {
		let employee = frm.doc.employee;
		if (employee == undefined || employee == ""){
			frm.set_df_property("employee_info_html", "options", '<p></p>');
			return
		}else{
			frappe.call({
				method: "frappe.client.get_value",
				async: false,
				args: {
					doctype: "Employee",
					filters: { name: frm.doc.employee },
					fieldname: [
						"employee_name",
						"company",
						"designation",
						"department"
					]
				},
				callback: function (r) {
					// console.log(r.message);
					let acf_employee_info = frappe.render_template("acf_employee_info", r.message);
					frm.set_df_property("employee_info_html", "options", acf_employee_info);
				}
			});
		}
	},
	load_details_of_overtime: function (frm, filters) {
		if (frm.doc.year != "" && frm.doc.month != "" && frm.doc.employee != undefined) {
			frm.call("get_details_of_overtime", filters).then(r => {
				// console.log(r.message);
				frm.set_intro('');
				frm.set_intro(r.message == undefined ? "Device detail not found." : "", 'red');
				frm.refresh_field("detail_of_overtime");
			});
		}else{
			console.log('not')
		}
	}
}

frappe.ui.form.on("Details of OT", {
	in_time: function(frm, cdt, cdn){
		// details.calculate_detail_of_overtime(frm, cdt, cdn);
	},
	out_time: function(frm, cdt, cdn){
		// details.calculate_detail_of_overtime(frm, cdt, cdn);
	},
	detail_of_overtime_remove: function(frm, cdt, cdn){
		acf.load_details_of_overtime(frm, {reset: false});
	}
});

details = {
	calculate_detail_of_overtime: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		if(row.in_time==undefined || row.out_time==undefined) return
		frm.call("calculate_detail_of_overtime").then(r=>{
			console.log(r.message);
		});
	}
}