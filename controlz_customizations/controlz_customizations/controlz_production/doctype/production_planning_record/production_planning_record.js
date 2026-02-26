// Copyright (c) 2024, Controlz Customizations and contributors
// For license information, please see license.txt

frappe.ui.form.on("Production Planning Record", {
	refresh(frm) {
        frm.add_custom_button(__('Material Transfer For Manufacturing'), function(){
            frappe.model.open_mapped_doc({
                method: "controlz_customizations.controlz_production.doctype.production_planning_record.production_planning_record.make_material_issue_from_ppr",
                frm: cur_frm,
            });
        })
        frm.add_custom_button(__('Finished Good Entry'), function(){
            frappe.model.open_mapped_doc({
                method: "controlz_customizations.controlz_production.doctype.production_planning_record.production_planning_record.make_fg_from_ppr",
                frm: cur_frm,
            });
        })

	},
    onload: function (frm) {
		frm.set_query("controlz_bom", function (doc) {
			return {
				filters: {
					item: doc.item_to_produce,
				},
			};
		});
	},
    controlz_bom: function(frm){
        frappe.call({
            method: "controlz_customizations.controlz_production.doctype.production_planning_record.production_planning_record.get_raw_materials",
            args: {
                controlz_bom: frm.doc.controlz_bom,
            },
            callback: function (r) {
                if (r.message) {
                    r.message.forEach(element => {
                        var production_planning_raw_material = cur_frm.add_child("production_planning_raw_material");
                        production_planning_raw_material.item= element.item
                        production_planning_raw_material.qty_percentage= element.qty_percentage

                        cur_frm.refresh_fields("production_planning_raw_material");
                        
                    });
                }
            },
        });
    }
});
