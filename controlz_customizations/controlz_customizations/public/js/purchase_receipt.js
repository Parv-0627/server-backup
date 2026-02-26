frappe.ui.form.on('Purchase Receipt', {
	refresh: function(frm) {
            if(frm.doc.docstatus == 0){
                frm.add_custom_button(__('Create Serial No'), function(){
                    frappe.call({
                        method: "controlz_customizations.bin.create_serial_numbers",
                        args: {
                            pr_name: frm.doc.name
                        },
                        callback(r) {
                            if (!r.exc) {
                                frm.reload_doc();
                                frappe.msgprint("Serial Numbers Created Successfully");
                            }
                        }
                    });
                })
            }
	}
}); 