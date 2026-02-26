// Copyright (c) 2025, nasirucode and contributors
// For license information, please see license.txt

frappe.ui.form.on("Carrier Partner", {
	setup(frm) {
        frm.set_query("supplier", function() {
            return {
                "filters": {
                    "is_transporter": 1
                }
            };
        });
	},
    supplier: function(frm) {
        if(frm.doc.supplier) {
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Carrier Partner",
                    filters: {
                        "supplier": frm.doc.supplier,
                        "name": ["!=", frm.doc.name || ""]
                    },
                    fields: ["name", "account_name"]
                },
                callback: function(r) {
                    if(r.message && r.message.length > 0) {
                        let carrier_partners = r.message.map(cp => cp.account_name || cp.name).join(", ");
                        frappe.show_alert({
                            message: __(`This supplier is already used by carrier partner(s): ${carrier_partners}`),
                            indicator: 'orange'
                        }, 10);
                    }
                }
            });
        }
    }
});
