// Copyright (c) 2025, Controlz Customizations and contributors
// For license information, please see license.txt

frappe.ui.form.on("Controlz Setup", {
	refresh(frm) {
        cur_frm.page.add_menu_item("Inventroy Sync", function () {

            frappe.call({
                method: "controlz_customizations.sync_inventory.update_inventory",
                freeze: true,
                callback: function (r) {

                    frappe.msgprint("Inventory Sync Done")


                }
            });


        })

	},
});
