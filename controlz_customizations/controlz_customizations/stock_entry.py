import frappe
from controlz_customizations.bin import update_stock
def on_submit(doc, method):
    if doc.production_planning_record: 
        if doc.stock_entry_type == "Material Transfer for Manufacture":
            production_planning_record = frappe.get_doc("Production Planning Record", doc.production_planning_record)
            for row in doc.items:
                for ppr in production_planning_record.production_planning_raw_material:
                    if ppr.item == row.item_code:
                        frappe.db.set_value("Production Planning Raw Material", ppr.name, "transfered_qty", row.qty)
        
        if doc.stock_entry_type == "Manufacture":
            production_planning_record = frappe.get_doc("Production Planning Record", doc.production_planning_record)
            for row in doc.items:
                if row.is_finished_item:
                    frappe.db.set_value("Production Planning Record", doc.production_planning_record, "fg_qty", row.qty)
    on_cancel(doc, method)

def on_cancel(doc, method):
    for row in doc.items:
        if row.t_warehouse:
            update_stock(row.item_code, row.t_warehouse)
        
        if row.s_warehouse:
            update_stock(row.item_code, row.s_warehouse)