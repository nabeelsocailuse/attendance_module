// Mubashir 25-02-2025 Start

frappe.ui.form.on('Attendance Log', {
    refresh: function(frm) {
        hide_show_fields(frm);
    },

    employee: function(frm) {
        if (frm.doc.employee) {
            frappe.call({
                method: "attendance_module.zk_device.doctype.attendance_log.attendance_log.get_employee_shift",
                args: { employee: frm.doc.employee },
                callback: function(response) {
                    if (response.message) {
                        frm.set_value("shift", response.message);
                    }
                }
            });
            hide_show_fields(frm);
        }
    },

    mark_check_in: function(frm) {
        updateAndProcessAttendance(frm, "mark_check_in");
    },

    mark_check_out: function(frm) {
        updateAndProcessAttendance(frm, "mark_check_out");
    }
});

// Function to update attendance fields, save, then process attendance
function updateAndProcessAttendance(frm, button_type) {
    frappe.call({
        method: "attendance_module.zk_device.doctype.attendance_log.attendance_log.get_current_datetime",
        callback: function(response) {
            let data = response.message;
            frm.set_value("attendance_date", data.date);
            frm.set_value("log", data.datetime);

            frm.save()
                .then(() => CallOpenStreetMap(frm, button_type))
                .catch(err => frappe.msgprint(__("Error saving document: ") + err.message));
        }
    });
}

// Function to show/hide fields based on role
function hide_show_fields(frm) {
    if (frappe.user.has_role("Attendance Log") && frappe.session.user !== "Administrator") {
        console.log('has role atl');
        
        ["device_id", "device_ip", "device_port", "log_type", "log_from"].forEach(field => {
            frm.set_df_property(field, "hidden", true);
        });
        ["attendance_date", "log"].forEach(field => {
            frm.set_df_property(field, "read_only", true);
        });
    }
    else {
        ["device_id", "device_ip", "device_port", "log_type", "log_from"].forEach(field => {
            frm.set_df_property(field, "hidden", false);
        });
        ["attendance_date", "log"].forEach(field => {
            frm.set_df_property(field, "read_only", false);
        });
    }
    
    if (frm.doc.attendance_date || frm.doc.log){
        console.log(frm.doc.attendance_date, frm.doc.log);
        
        frm.set_df_property("mark_check_in", "hidden", true);
        frm.set_df_property("mark_check_out", "hidden", true);
        return;
    };
    frm.set_df_property("mark_check_in", "hidden", true);
    frm.set_df_property("mark_check_out", "hidden", true);

    if (frappe.user.has_role("Attendance Log")) {
        setTimeout(() => {  
            check_attendance_status(frm);
            // frm.set_df_property("shift", "reqd", true);
        }, 200);
    } else {
        frm.set_df_property("mark_check_in", "hidden", true);
        frm.set_df_property("mark_check_out", "hidden", true);
    }
}

function check_attendance_status(frm) {
    if (frm.doc.employee && frm.doc.shift) {
        frappe.call({
            method: "attendance_module.zk_device.doctype.attendance_log.attendance_log.check_attendance_status",
            args: { employee: frm.doc.employee, shift: frm.doc.shift },
            callback: function(response) {
                if (response.message === "check_in") {
                    frm.set_df_property("mark_check_in", "hidden", false);
                    frm.set_df_property("mark_check_out", "hidden", true);
                } else if (response.message === "check_out") {
                    frm.set_df_property("mark_check_in", "hidden", true);
                    frm.set_df_property("mark_check_out", "hidden", false);
                }
            }
        });
    }
}


function CallOpenStreetMap(frm, button_type) {
    navigator.geolocation.getCurrentPosition(
        (position) => {
            frappe.call({
                method: "attendance_module.zk_device.doctype.attendance_log.attendance_log.record_attendance",
                args: {
                    docname: frm.doc.name,
                    button_type: button_type,
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                },
                callback: function(response) {
                    frappe.msgprint(response.message);
                    frm.reload_doc();
                }
            });
        },
        (error) => {
            console.error("Geolocation error:", error.message);
        }
    );
}

// Mubashir 25-02-2025 End