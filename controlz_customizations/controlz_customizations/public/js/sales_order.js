frappe.ui.form.on('Sales Order', {
	refresh: function(frm) {
			// frm.add_custom_button(__('Create Clickpost Pickup Order'), function(){
			// 	frappe.model.open_mapped_doc({
            //         method: "controlz_customizations.apis.clickpost_order.make_clickpost_doc_from_support_ticket_from_customer",
            //         frm: cur_frm,
            //     });
			// })
            if(frm.doc.docstatus == 1){
                frm.add_custom_button(__('Create Clickpost Delivery Order'), function(){
                    frappe.model.open_mapped_doc({
                        method: "controlz_customizations.apis.clickpost_order.make_clickpost_doc_from_sales_order_to_customer",
                        frm: cur_frm,
                    });
                })
            }
	}
});