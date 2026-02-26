// Copyright (c) 2024, Frappe Customizations and contributors
// For license information, please see license.txt

frappe.ui.form.on('Support Ticket', {
	refresh: function(frm) {
		if(frm.doc.status == "Waiting For Pick Arrange"){
			frm.add_custom_button(__('Create Clickpost Pickup Order'), function(){
				frappe.model.open_mapped_doc({
                    method: "undoworld_customizations.undoworld_customizations.doctype.clickpost_order.clickpost_order.make_clickpost_doc_from_support_ticket_from_customer",
                    frm: cur_frm,
                });
			})
		}
		if(frm.doc.status == "Waiting For Delivery Arrange"){
			frm.add_custom_button(__('Create Clickpost Delivery Order'), function(){
				frappe.model.open_mapped_doc({
                    method: "undoworld_customizations.undoworld_customizations.doctype.clickpost_order.clickpost_order.make_clickpost_doc_from_support_ticket_to_customer",
                    frm: cur_frm,
                });
			})
		}
	}
});
