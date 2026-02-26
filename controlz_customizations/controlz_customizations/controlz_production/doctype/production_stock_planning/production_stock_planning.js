// Copyright (c) 2024, Controlz Customizations and contributors
// For license information, please see license.txt

frappe.ui.form.on("Production Stock Planning", {
	refresh(frm) {
        frm.add_custom_button(__('Make Part Material Request'), function(){
            frappe.model.open_mapped_doc({
                method: "controlz_customizations.controlz_production.doctype.production_stock_planning.production_stock_planning.make_part_material_request_from_psp",
                frm: cur_frm,
            });
        })
        frm.add_custom_button(__('Make FG Material Request'), function(){
            frappe.model.open_mapped_doc({
                method: "controlz_customizations.controlz_production.doctype.production_stock_planning.production_stock_planning.make_fg_material_request_from_psp",
                frm: cur_frm,
            });
        })
        frm.set_query("controlz_bom", "production_stock_planning_table", function (doc, cdt, cdn) {
			let d = locals[cdt][cdn];
			return {
				filters: {
                    item: d.item_to_produce
				},
			};
		});

	},
    
});

